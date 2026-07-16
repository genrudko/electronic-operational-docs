from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ImportUploadForm
from .models import ImportBatch, ImportRow
from .services import (
    create_import_batch,
    discard_import_batch,
    require_import_employee,
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
            batch.status in {ImportBatch.Status.FAILED}
            or batch.warning_count > 0
            for batch in batches
            if batch.status != ImportBatch.Status.DISCARDED
        ),
        "discarded": sum(
            batch.status == ImportBatch.Status.DISCARDED for batch in batches
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
    status_filter = request.GET.get("status", "").strip().upper()
    allowed_statuses = {value for value, _label in ImportRow.Status.choices}

    rows = batch.rows.all()
    if status_filter in allowed_statuses:
        rows = rows.filter(status=status_filter)
    else:
        status_filter = ""

    paginator = Paginator(rows, 25)
    page = paginator.get_page(request.GET.get("page"))
    for row in page.object_list:
        source_values = list(row.source_values[: len(columns)])
        normalized_values = list(row.normalized_values[: len(columns)])
        row.preview_values = source_values
        row.preview_pairs = list(
            zip(columns, source_values, normalized_values, strict=True)
        )

    metrics = [
        ("Новые", batch.status_counts.get(ImportRow.Status.NEW, 0), "new"),
        (
            "Распознаны",
            batch.status_counts.get(ImportRow.Status.RECOGNIZED, 0),
            "recognized",
        ),
        (
            "Требуют проверки",
            batch.status_counts.get(ImportRow.Status.REVIEW, 0),
            "review",
        ),
        (
            "Конфликты",
            batch.status_counts.get(ImportRow.Status.CONFLICT, 0),
            "conflict",
        ),
        (
            "Отклонены",
            batch.status_counts.get(ImportRow.Status.REJECTED, 0),
            "rejected",
        ),
    ]
    duplicate_attempts = (
        ImportBatch.objects.filter(
            organization=batch.organization,
            file_sha256=batch.file_sha256,
        )
        .exclude(pk=batch.pk)
        .count()
    )
    return render(
        request,
        "imports/detail.html",
        {
            "batch": batch,
            "columns": columns,
            "hidden_column_count": max(batch.column_count - len(columns), 0),
            "page": page,
            "metrics": metrics,
            "status_filter": status_filter,
            "status_choices": ImportRow.Status.choices,
            "duplicate_attempts": duplicate_attempts,
        },
    )


@login_required
def import_discard(request: HttpRequest, public_id) -> HttpResponse:
    if request.method != "POST":
        return redirect("imports:detail", public_id=public_id)
    employee, batch = _organization_batch(request, public_id)
    discard_import_batch(batch=batch, employee=employee)
    messages.success(
        request,
        "Загрузка удалена из рабочего списка. Аудиторская запись сохранена.",
    )
    return redirect("imports:detail", public_id=batch.public_id)
