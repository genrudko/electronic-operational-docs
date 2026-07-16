from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import Count
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import (
    ImportColumnMappingForm,
    ImportPublicationConfirmationForm,
    ImportRowCorrectionForm,
    ImportUploadForm,
)
from .models import ImportBatch, ImportPublication, ImportRow
from .services import (
    build_import_publication_preview,
    bulk_decide_import_rows,
    can_publish_import,
    create_import_batch,
    decide_import_row,
    discard_import_batch,
    publish_import_batch,
    registry_field_specs,
    require_import_employee,
    require_import_publisher,
    save_column_mapping,
    save_row_correction,
)


def _organization_batch(request: HttpRequest, public_id):
    employee = require_import_employee(request.user)
    batch = get_object_or_404(
        ImportBatch.objects.select_related(
            "organization",
            "created_by",
            "created_by__position",
        ),
        public_id=public_id,
        organization=employee.organization,
    )
    return employee, batch


def _validation_message(error: ValidationError) -> str:
    if hasattr(error, "message_dict"):
        return " ".join(
            message
            for values in error.message_dict.values()
            for message in values
        )
    return " ".join(error.messages)


@login_required
def import_list(request: HttpRequest) -> HttpResponse:
    employee = require_import_employee(request.user)
    batches = list(
        ImportBatch.objects.filter(organization=employee.organization)
        .select_related("created_by")
        .annotate(stored_rows=Count("rows"))
        .order_by("-created_at", "-id")[:100]
    )
    summary = {
        "total": len(batches),
        "ready": sum(
            batch.status == ImportBatch.Status.READY for batch in batches
        ),
        "attention": sum(
            batch.status == ImportBatch.Status.FAILED
            or batch.warning_count > 0
            or bool(batch.review_counts.get("blocked", 0))
            for batch in batches
            if batch.status != ImportBatch.Status.DISCARDED
        ),
        "discarded": sum(
            batch.status == ImportBatch.Status.DISCARDED for batch in batches
        ),
        "published": sum(
            batch.status == ImportBatch.Status.PUBLISHED for batch in batches
        ),
    }
    return render(
        request,
        "imports/list.html",
        {"batches": batches, "summary": summary},
    )


@login_required
def import_upload(request: HttpRequest) -> HttpResponse:
    employee = require_import_employee(request.user)
    if request.method == "POST":
        form = ImportUploadForm(request.POST, request.FILES)
        if form.is_valid():
            batch = create_import_batch(
                uploaded_file=form.cleaned_data["source_file"],
                target_registry=form.cleaned_data["target_registry"],
                employee=employee,
            )
            if batch.status == ImportBatch.Status.READY:
                messages.success(
                    request,
                    "Файл разобран. Действующие справочники не изменены.",
                )
            else:
                messages.error(
                    request,
                    "Попытка сохранена в журнале, но файл не удалось разобрать.",
                )
            return redirect("imports:detail", public_id=batch.public_id)
    else:
        form = ImportUploadForm()
    return render(request, "imports/upload.html", {"form": form})


@login_required
def import_detail(request: HttpRequest, public_id) -> HttpResponse:
    _employee, batch = _organization_batch(request, public_id)
    columns = list(batch.columns.all()[:12])
    field_specs = registry_field_specs(batch.target_registry)
    field_labels = {spec.key: spec.label for spec in field_specs}

    review_filter = request.GET.get("review", "").strip().upper()
    decision_filter = request.GET.get("decision", "").strip().upper()
    allowed_review = {value for value, _label in ImportRow.ReviewStatus.choices}
    allowed_decisions = {value for value, _label in ImportRow.Decision.choices}

    rows = batch.rows.select_related("decided_by")
    if review_filter in allowed_review:
        rows = rows.filter(review_status=review_filter)
    else:
        review_filter = ""
    if decision_filter in allowed_decisions:
        rows = rows.filter(decision=decision_filter)
    else:
        decision_filter = ""

    paginator = Paginator(rows, 25)
    page = paginator.get_page(request.GET.get("page"))
    for row in page.object_list:
        source_values = list(row.source_values[: len(columns)])
        normalized_values = list(row.normalized_values[: len(columns)])
        row.preview_values = source_values
        row.preview_pairs = list(
            zip(columns, source_values, normalized_values, strict=True)
        )
        row.effective_pairs = [
            (field_labels.get(key, key), value)
            for key, value in row.effective_values.items()
        ]
        row.can_accept = row.review_status in {
            ImportRow.ReviewStatus.VALID,
            ImportRow.ReviewStatus.REVIEW,
        }

    clean_source_rows = (
        batch.status_counts.get(ImportRow.Status.NEW, 0)
        + batch.status_counts.get(ImportRow.Status.RECOGNIZED, 0)
    )
    source_metrics = [
        ("Без блокирующих замечаний", clean_source_rows, "recognized"),
        (
            "Требуют ручной проверки",
            batch.status_counts.get(ImportRow.Status.REVIEW, 0),
            "review",
        ),
        (
            "Конфликты внутри файла",
            batch.status_counts.get(ImportRow.Status.CONFLICT, 0),
            "conflict",
        ),
        (
            "Отклонены при разборе",
            batch.status_counts.get(ImportRow.Status.REJECTED, 0),
            "rejected",
        ),
    ]
    review_metrics = [
        ("Ожидают решения", batch.review_counts.get("pending", 0), "pending"),
        ("Приняты предварительно", batch.review_counts.get("accepted", 0), "accepted"),
        ("Отклонены пользователем", batch.review_counts.get("rejected", 0), "rejected"),
        ("Заблокированы", batch.review_counts.get("blocked", 0), "blocked"),
    ]
    duplicate_attempts = (
        ImportBatch.objects.filter(
            organization=batch.organization,
            file_sha256=batch.file_sha256,
        )
        .exclude(pk=batch.pk)
        .count()
    )
    mapped_count = batch.columns.exclude(mapped_key="").count()
    publication = getattr(batch, "publication", None)
    return render(
        request,
        "imports/detail.html",
        {
            "batch": batch,
            "columns": columns,
            "hidden_column_count": max(batch.column_count - len(columns), 0),
            "page": page,
            "source_metrics": source_metrics,
            "review_metrics": review_metrics,
            "review_filter": review_filter,
            "decision_filter": decision_filter,
            "review_choices": ImportRow.ReviewStatus.choices,
            "decision_choices": ImportRow.Decision.choices,
            "duplicate_attempts": duplicate_attempts,
            "mapped_count": mapped_count,
            "required_count": sum(spec.required for spec in field_specs),
            "field_labels": field_labels,
            "publication": publication,
            "can_publish": can_publish_import(request.user),
        },
    )


@login_required
def import_mapping(request: HttpRequest, public_id) -> HttpResponse:
    employee, batch = _organization_batch(request, public_id)
    if batch.status != ImportBatch.Status.READY:
        messages.error(request, "Сопоставление недоступно для этой загрузки.")
        return redirect("imports:detail", public_id=batch.public_id)

    if request.method == "POST":
        form = ImportColumnMappingForm(request.POST, batch=batch)
        if form.is_valid():
            try:
                batch = save_column_mapping(
                    batch=batch,
                    employee=employee,
                    mapping=form.mapping,
                )
            except ValidationError as error:
                form.add_error(None, _validation_message(error))
            else:
                messages.success(
                    request,
                    "Сопоставление подтверждено. Проверка строк пересчитана без публикации.",
                )
                return redirect("imports:detail", public_id=batch.public_id)
    else:
        form = ImportColumnMappingForm(batch=batch)

    return render(
        request,
        "imports/mapping.html",
        {
            "batch": batch,
            "form": form,
            "field_specs": registry_field_specs(batch.target_registry),
        },
    )


@login_required
def import_row_edit(request: HttpRequest, public_id, row_id: int) -> HttpResponse:
    employee, batch = _organization_batch(request, public_id)
    row = get_object_or_404(
        ImportRow.objects.select_related("batch"),
        pk=row_id,
        batch=batch,
    )
    if batch.status != ImportBatch.Status.READY:
        messages.error(request, "Опубликованную или закрытую загрузку нельзя редактировать.")
        return redirect("imports:detail", public_id=batch.public_id)
    if batch.mapping_completed_at is None:
        messages.error(request, "Сначала подтвердите сопоставление колонок.")
        return redirect("imports:mapping", public_id=batch.public_id)

    if request.method == "POST":
        form = ImportRowCorrectionForm(request.POST, row=row)
        if form.is_valid():
            try:
                save_row_correction(
                    row=row,
                    employee=employee,
                    values=form.corrected_values,
                    note=form.cleaned_data["note"],
                )
            except ValidationError as error:
                form.add_error(None, _validation_message(error))
            else:
                messages.success(
                    request,
                    f"Строка {row.row_number} исправлена и предварительно принята.",
                )
                return redirect("imports:detail", public_id=batch.public_id)
    else:
        form = ImportRowCorrectionForm(row=row)

    return render(
        request,
        "imports/row_edit.html",
        {"batch": batch, "row": row, "form": form},
    )


@login_required
def import_row_decide(request: HttpRequest, public_id, row_id: int) -> HttpResponse:
    if request.method != "POST":
        return redirect("imports:detail", public_id=public_id)
    employee, batch = _organization_batch(request, public_id)
    row = get_object_or_404(ImportRow, pk=row_id, batch=batch)
    action = request.POST.get("action", "")
    try:
        decide_import_row(
            row=row,
            employee=employee,
            action=action,
            note=request.POST.get("note", ""),
        )
    except ValidationError as error:
        messages.error(request, _validation_message(error))
    else:
        messages.success(request, f"Решение по строке {row.row_number} сохранено.")
    return redirect("imports:detail", public_id=batch.public_id)


@login_required
def import_bulk_decide(request: HttpRequest, public_id) -> HttpResponse:
    if request.method != "POST":
        return redirect("imports:detail", public_id=public_id)
    employee, batch = _organization_batch(request, public_id)
    raw_ids = request.POST.getlist("rows")
    try:
        row_ids = [int(value) for value in raw_ids]
    except ValueError:
        messages.error(request, "Передан некорректный список строк.")
        return redirect("imports:detail", public_id=batch.public_id)
    try:
        result = bulk_decide_import_rows(
            batch=batch,
            employee=employee,
            row_ids=row_ids,
            action=request.POST.get("action", ""),
        )
    except ValidationError as error:
        messages.error(request, _validation_message(error))
    else:
        messages.success(
            request,
            f"Обработано строк: {result['processed']}. Пропущено: {result['skipped']}.",
        )
    return redirect("imports:detail", public_id=batch.public_id)


@login_required
def import_discard(request: HttpRequest, public_id) -> HttpResponse:
    if request.method != "POST":
        return redirect("imports:detail", public_id=public_id)
    employee, batch = _organization_batch(request, public_id)
    try:
        discard_import_batch(batch=batch, employee=employee)
    except ValidationError as error:
        messages.error(request, _validation_message(error))
    else:
        messages.success(
            request,
            "Загрузка убрана из рабочего списка. Аудиторская запись сохранена.",
        )
    return redirect("imports:detail", public_id=batch.public_id)



@login_required
def import_publication(request: HttpRequest, public_id) -> HttpResponse:
    employee, batch = _organization_batch(request, public_id)
    if batch.status == ImportBatch.Status.PUBLISHED:
        return redirect("imports:publication_result", public_id=batch.public_id)

    try:
        preview = build_import_publication_preview(batch)
    except ValidationError as error:
        messages.error(request, _validation_message(error))
        return redirect("imports:detail", public_id=batch.public_id)

    allowed = can_publish_import(request.user)
    if request.method == "POST":
        publisher = require_import_publisher(request.user)
        form = ImportPublicationConfirmationForm(request.POST)
        if form.is_valid():
            try:
                publication = publish_import_batch(
                    batch=batch,
                    actor=publisher,
                    user=request.user,
                    password=form.cleaned_data["password"],
                    expected_digest=form.cleaned_data["preview_digest"],
                )
            except ValidationError as error:
                if hasattr(error, "message_dict") and "password" in error.message_dict:
                    for message in error.message_dict["password"]:
                        form.add_error("password", message)
                else:
                    form.add_error(None, _validation_message(error))
            else:
                messages.success(
                    request,
                    (
                        "Публикация завершена транзакционно. "
                        f"Создано записей: {publication.result_summary['accepted']}."
                    ),
                )
                return redirect(
                    "imports:publication_result",
                    public_id=batch.public_id,
                )
    else:
        form = ImportPublicationConfirmationForm(
            initial={"preview_digest": preview.digest}
        )

    return render(
        request,
        "imports/publication.html",
        {
            "batch": batch,
            "employee": employee,
            "preview": preview,
            "form": form,
            "can_publish": allowed,
        },
    )


@login_required
def import_publication_result(request: HttpRequest, public_id) -> HttpResponse:
    _employee, batch = _organization_batch(request, public_id)
    publication = get_object_or_404(
        ImportPublication.objects.select_related(
            "batch",
            "actor",
            "actor__position",
        ),
        batch=batch,
    )
    rows = publication.published_rows.select_related("row").order_by(
        "row__row_number"
    )
    return render(
        request,
        "imports/publication_result.html",
        {
            "batch": batch,
            "publication": publication,
            "published_rows": rows,
        },
    )
