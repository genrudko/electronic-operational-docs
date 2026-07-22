from __future__ import annotations

from datetime import date

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.db.models import Count
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import (
    ImportColumnMappingForm,
    ImportPublicationConfirmationForm,
    ImportRowCorrectionForm,
    ImportUploadForm,
    PersonnelPublicationConfirmationForm,
    PersonnelWorkbookUploadForm,
    PowerSystemDuplicateGroupDecisionForm,
    PowerSystemOccurrenceDecisionForm,
    PowerSystemPackageUploadForm,
    PowerSystemPublicationConfirmationForm,
)
from .models import (
    ImportBatch,
    ImportMappingTemplate,
    ImportPublication,
    ImportRow,
    PersonnelAuthorityCell,
    PersonnelPublication,
    PersonnelSourceRevision,
    PersonnelSourceRow,
    PowerSystemAssetOccurrence,
    PowerSystemSourceRevision,
)
from .personnel import (
    PersonnelWorkbookError,
    build_personnel_publication_preview,
    discard_personnel_revision,
    personnel_revision_for_user,
    publish_personnel_revision,
    stage_personnel_workbook,
)
from .personnel import (
    source_revision_queryset_for_employee as personnel_revision_queryset_for_employee,
)
from .power_system import (
    PowerSystemPackageError,
    build_power_system_publication_preview,
    decide_power_system_duplicate_group,
    decide_power_system_occurrence,
    discard_power_system_revision,
    power_system_revision_for_user,
    power_system_type_counts,
    publish_power_system_revision,
    source_revision_queryset_for_employee,
    stage_power_system_package,
)
from .services import (
    available_data_profiles,
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
from .unicode_search import filter_power_system_occurrences


def _organization_batch(request: HttpRequest, public_id):
    employee = require_import_employee(request.user)
    batch = get_object_or_404(
        ImportBatch.objects.select_related(
            "organization",
            "created_by",
            "created_by__position",
            "data_profile",
            "applied_mapping_template",
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


POWER_SYSTEM_ISSUE_LABELS = {
    "BROKEN_HELPER_FORMULAS": "Повреждённые служебные формулы",
    "DUPLICATE_TN_1_330": "Повторяющееся наименование ТН-1-330",
    "LEP_CROSS_LISTED_35KV_CABLES": "Повторное представление КЛ 35 кВ",
    "LEP_TSN_NAME_AUTHORITY_CONFLICT": "Конфликт принадлежности КЛ ТСН",
    "LEP_RESERVE_CABLE_DUPLICATE": "Повтор резервной КЛ 0,4 кВ",
    "KOCUBEYEVSKAYA_TYPO": "Опечатка в названии Кочубеевской ВЭС",
    "AUTHORITY_DOUBLE_SPACE": "Лишний пробел в субъекте ведения",
    "MISSING_CONDUCT_VALUES_DGR": "Не заполнено ведение ДГР",
    "RZA_KTP_HEADINGS_HAVE_AUTHORITY": "Полномочия указаны в заголовках КТП",
    "SDTU_EMPTY_NUMBERED_PLACEHOLDERS": "Пустые нумерованные строки СДТУ",
    "SDTU_SWITCH_NAME_POSSIBLE_TYPO": "Возможная опечатка в имени коммутатора",
    "SDTU_MUX_SPACING": "Разное оформление наименований MUX",
    "PARENT_REQUIRED_FOR_UNIQUENESS": "Родитель обязателен для различения объектов",
    "INFORMATIONAL_CONDUCT_FOOTNOTE_SCOPE": "Неясная область информационного ведения",
    "BLANK_VS_DASH_SEMANTICS": "Пустое значение отличается от явного прочерка",
    "AGGREGATE_DISPATCH_NAMES": "Составные диспетчерские наименования",
    "SOURCE_VERSION_UNCERTAIN": "Неопределённая редакция источника",
    "ABBREVIATION_VES_COLLISION": "Неоднозначное сокращение ВЭС",
    "EXTERNAL_AUTHORITY_SUBJECTS": "Внешние субъекты управления и ведения",
    "SOURCE_CATEGORY_TECHNICAL_MISMATCH": "Категория источника не равна техническому типу",
    "RZA_PRIMARY_LINK_MATCHING": "Связь РЗА с первичным оборудованием требует проверки",
    "ABBREVIATION_CONTACT_SCOPE": "Контактные данные вне области импорта оборудования",
}

POWER_SYSTEM_CATEGORY_LABELS = {
    "SOURCE_INTEGRITY": "Целостность источника",
    "DUPLICATE": "Возможный дубль",
    "AUTHORITY_CONFLICT": "Конфликт управления или ведения",
    "ALIAS": "Алиас и нормализация",
    "NORMALIZATION": "Нормализация",
    "MISSING_DATA": "Отсутствующие данные",
    "STRUCTURE": "Структура источника",
    "POSSIBLE_TYPO": "Возможная опечатка",
    "UNIQUENESS": "Уникальность",
    "SEMANTICS": "Смысл исходного значения",
    "GRANULARITY": "Гранулярность объекта",
    "VERSIONING": "Версия источника",
    "ALIAS_COLLISION": "Конфликт сокращений",
    "REFERENCE_DATA": "Внешние справочные данные",
    "CLASSIFICATION": "Классификация",
    "RELATIONSHIP": "Предлагаемая связь",
    "SCOPE": "Область применения",
}

POWER_SYSTEM_TEXT_REPLACEMENTS = (
    ("staging external authority references", "временные ссылки на внешних субъектов управления и ведения"),
    ("revision + parent + type + raw name", "редакция + родитель + тип + исходное имя"),
    (
        "is_informational сделать nullable",
        "признак информационного ведения разрешить оставлять неопределённым",
    ),
    ("type_code только PROPOSED", "технический тип хранить только как предложение"),
    ("proposed match с confidence", "предлагаемую связь с оценкой уверенности"),
    ("DRAFT source revision", "черновую редакцию источника"),
    ("source_category_raw", "исходная категория"),
    ("source-occurrence", "исходная строка"),
    ("source occurrences", "исходные строки"),
    ("source occurrence", "исходная строка"),
    ("Merge candidate", "Кандидат на объединение"),
    ("merge candidate", "кандидат на объединение"),
    ("после review", "после ручной проверки"),
    ("filename/checksum", "имя файла и контрольную сумму"),
    ("comparison key", "ключ сравнения"),
    ("normalized key", "нормализованный ключ"),
    ("placeholders", "пустые строки-заполнители"),
    ("Raw сохранить", "Исходное значение сохранить"),
    ("PROPOSED", "предложенный"),
    ("review", "ручная проверка"),
    ("scope", "область действия"),
    ("alias", "алиас"),
    ("raw", "исходное значение"),
)


def _power_system_ui_text(value: str) -> str:
    result = value or ""
    for source, target in POWER_SYSTEM_TEXT_REPLACEMENTS:
        result = result.replace(source, target)
    return result


def _power_system_parent_labels(revision: PowerSystemSourceRevision) -> dict[str, str]:
    return {
        external_key: dispatcher_name
        for external_key, dispatcher_name in revision.asset_occurrences.filter(
            record_role=PowerSystemAssetOccurrence.RecordRole.HIERARCHY_NODE,
        ).values_list("external_key", "dispatcher_name_raw")
    }


def _decorate_power_system_occurrence(row, parent_labels: dict[str, str]) -> None:
    row.resolved_parent_name = parent_labels.get(row.parent_external_key, "")
    row.is_root_site = row.asset_type_code == "energy_facility" and not row.parent_external_key
    row.is_orphan = row.asset_type_code != "energy_facility" and not row.parent_external_key
    if row.is_root_site:
        row.resolved_parent_name = "Корневой энергообъект"
    elif not row.resolved_parent_name:
        row.resolved_parent_name = row.parent_raw or "Не определён"
    row.needs_manual_decision = row.review_status in {
        PowerSystemAssetOccurrence.ReviewStatus.REVIEW_REQUIRED,
        PowerSystemAssetOccurrence.ReviewStatus.BLOCKED,
    }
    row.is_automatic_ready = row.review_status == PowerSystemAssetOccurrence.ReviewStatus.READY


def _power_system_duplicate_groups(
    revision: PowerSystemSourceRevision,
    parent_labels: dict[str, str],
) -> list[dict[str, object]]:
    rows = list(
        revision.asset_occurrences.filter(duplicate_group__gt="")
        .exclude(review_status=PowerSystemAssetOccurrence.ReviewStatus.PUBLISHED)
        .select_related("merge_target", "reviewed_by")
        .order_by("duplicate_group", "source_sheet", "source_row", "occurrence_id")
    )
    grouped: dict[str, list[PowerSystemAssetOccurrence]] = {}
    for row in rows:
        grouped.setdefault(row.duplicate_group, []).append(row)

    result: list[dict[str, object]] = []
    attention_statuses = {
        PowerSystemAssetOccurrence.ReviewStatus.REVIEW_REQUIRED,
        PowerSystemAssetOccurrence.ReviewStatus.BLOCKED,
    }
    for duplicate_group, members in grouped.items():
        if len(members) < 2:
            continue
        for member in members:
            _decorate_power_system_occurrence(member, parent_labels)
        result.append(
            {
                "code": duplicate_group,
                "title": members[0].dispatcher_name_raw,
                "members": members,
                "blocked": any(
                    member.review_status == PowerSystemAssetOccurrence.ReviewStatus.BLOCKED
                    for member in members
                ),
                "resolved": not any(
                    member.review_status in attention_statuses for member in members
                ),
                "decision_count": sum(
                    member.review_decision
                    != PowerSystemAssetOccurrence.ReviewDecision.NONE
                    for member in members
                ),
            }
        )
    return result


@login_required
def import_list(request: HttpRequest) -> HttpResponse:
    employee = require_import_employee(request.user)
    batches = list(
        ImportBatch.objects.filter(organization=employee.organization)
        .select_related("created_by", "data_profile", "applied_mapping_template")
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
    profiles = available_data_profiles(employee.organization)
    mapping_template_count = ImportMappingTemplate.objects.filter(
        organization=employee.organization,
        is_active=True,
    ).count()
    return render(
        request,
        "imports/list.html",
        {
            "batches": batches,
            "summary": summary,
            "profiles": profiles,
            "mapping_template_count": mapping_template_count,
        },
    )


@login_required
def data_profile_list(request: HttpRequest) -> HttpResponse:
    employee = require_import_employee(request.user)
    profiles = available_data_profiles(employee.organization)
    profile_rows = []
    for profile in profiles:
        profile_rows.append(
            {
                "profile": profile,
                "batch_count": ImportBatch.objects.filter(data_profile=profile).count(),
                "published_count": ImportBatch.objects.filter(
                    data_profile=profile,
                    status=ImportBatch.Status.PUBLISHED,
                ).count(),
            }
        )
    return render(
        request,
        "imports/data_profiles.html",
        {"profile_rows": profile_rows},
    )


@login_required
def import_upload(request: HttpRequest) -> HttpResponse:
    employee = require_import_employee(request.user)
    if request.method == "POST":
        form = ImportUploadForm(
            request.POST,
            request.FILES,
            organization=employee.organization,
        )
        if form.is_valid():
            batch = create_import_batch(
                uploaded_file=form.cleaned_data["source_file"],
                target_registry=form.cleaned_data["target_registry"],
                employee=employee,
                data_profile=form.cleaned_data["data_profile"],
                source_reference=form.cleaned_data["source_reference"],
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
        form = ImportUploadForm(organization=employee.organization)
    return render(
        request,
        "imports/upload.html",
        {
            "form": form,
            "profiles": available_data_profiles(employee.organization),
        },
    )


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


@login_required
def power_system_list(request: HttpRequest) -> HttpResponse:
    employee = require_import_employee(request.user)
    revisions = list(
        source_revision_queryset_for_employee(employee)
        .annotate(stored_occurrences=Count("asset_occurrences"))
        .order_by("-created_at", "-id")[:100]
    )
    return render(
        request,
        "imports/power_system_list.html",
        {
            "employee": employee,
            "revisions": revisions,
            "summary": {
                "total": len(revisions),
                "staged": sum(
                    revision.status == PowerSystemSourceRevision.Status.STAGED
                    for revision in revisions
                ),
                "attention": sum(
                    bool(revision.review_count or revision.blocked_count)
                    for revision in revisions
                    if revision.status != PowerSystemSourceRevision.Status.DISCARDED
                ),
                "published": sum(
                    revision.status
                    in {
                        PowerSystemSourceRevision.Status.PUBLISHED,
                        PowerSystemSourceRevision.Status.PARTIALLY_PUBLISHED,
                    }
                    for revision in revisions
                ),
            },
        },
    )


@login_required
def power_system_upload(request: HttpRequest) -> HttpResponse:
    employee = require_import_employee(request.user)
    if request.method == "POST":
        form = PowerSystemPackageUploadForm(
            request.POST,
            request.FILES,
            organization=employee.organization,
        )
        if form.is_valid():
            try:
                revision, created = stage_power_system_package(
                    uploaded_file=form.cleaned_data["source_file"],
                    employee=employee,
                    data_profile=form.cleaned_data["data_profile"],
                    source_reference=form.cleaned_data["source_reference"],
                    source_approval_status=form.cleaned_data["source_approval_status"],
                    effective_from=form.cleaned_data["effective_from"],
                )
            except (ValidationError, PowerSystemPackageError) as error:
                form.add_error(
                    None,
                    _validation_message(error)
                    if isinstance(error, ValidationError)
                    else str(error),
                )
            else:
                if created:
                    messages.success(
                        request,
                        "Пакет разобран в область предварительной проверки. "
                        "Рабочие справочники не изменены.",
                    )
                else:
                    messages.info(
                        request,
                        "Пакет с тем же SHA-256 уже был загружен. Открыта существующая редакция.",
                    )
                return redirect("imports:power_system_detail", public_id=revision.public_id)
    else:
        form = PowerSystemPackageUploadForm(organization=employee.organization)
    return render(
        request,
        "imports/power_system_upload.html",
        {"form": form},
    )


@login_required
def power_system_detail(request: HttpRequest, public_id) -> HttpResponse:
    employee, revision = power_system_revision_for_user(request.user, public_id)
    raw_status_filter = request.GET.get("status")
    status_filter = "ATTENTION" if raw_status_filter is None else raw_status_filter.strip().upper()
    type_filter = request.GET.get("type", "").strip()
    query = request.GET.get("q", "").strip()
    allowed_statuses = {value for value, _label in PowerSystemAssetOccurrence.ReviewStatus.choices}
    parent_labels = _power_system_parent_labels(revision)
    duplicate_groups = _power_system_duplicate_groups(revision, parent_labels)
    grouped_occurrence_ids = {
        member.pk
        for group in duplicate_groups
        if not group["resolved"]
        for member in group["members"]
    }
    occurrences = revision.asset_occurrences.select_related(
        "merge_target",
        "reviewed_by",
        "published_asset",
    )
    if status_filter == "ATTENTION":
        occurrences = occurrences.filter(
            review_status__in=(
                PowerSystemAssetOccurrence.ReviewStatus.REVIEW_REQUIRED,
                PowerSystemAssetOccurrence.ReviewStatus.BLOCKED,
            )
        ).exclude(pk__in=grouped_occurrence_ids)
    elif status_filter in allowed_statuses:
        occurrences = occurrences.filter(review_status=status_filter)
    elif status_filter in {"", "ALL"}:
        status_filter = "ALL"
    else:
        status_filter = "ATTENTION"
        occurrences = occurrences.filter(
            review_status__in=(
                PowerSystemAssetOccurrence.ReviewStatus.REVIEW_REQUIRED,
                PowerSystemAssetOccurrence.ReviewStatus.BLOCKED,
            )
        )
    if type_filter:
        occurrences = occurrences.filter(asset_type_code=type_filter)
    if query:
        occurrences = filter_power_system_occurrences(
            occurrences,
            query,
        )
    occurrences = occurrences.order_by("source_sheet", "source_row", "occurrence_id")
    page_size = 25 if status_filter == "ATTENTION" else 50
    page = Paginator(occurrences, page_size).get_page(request.GET.get("page"))
    duplicate_members = {
        group["code"]: group["members"]
        for group in duplicate_groups
    }
    for row in page.object_list:
        _decorate_power_system_occurrence(row, parent_labels)
        row.merge_candidates = [
            candidate
            for candidate in duplicate_members.get(row.duplicate_group, [])
            if candidate.pk != row.pk
        ]

    issues = list(revision.issues.order_by("-severity", "issue_code")[:100])
    for issue in issues:
        issue.title_ui = POWER_SYSTEM_ISSUE_LABELS.get(issue.issue_code, issue.issue_code)
        issue.category_ui = POWER_SYSTEM_CATEGORY_LABELS.get(issue.category, issue.category)
        issue.evidence_ui = _power_system_ui_text(issue.evidence)
        issue.risk_ui = _power_system_ui_text(issue.import_risk)
        issue.handling_ui = _power_system_ui_text(issue.recommended_handling)

    hierarchy_counts = {
        "sites": revision.asset_occurrences.filter(asset_type_code="energy_facility").count(),
        "voltage_levels": revision.asset_occurrences.filter(asset_type_code="voltage_level").count(),
        "unit_substations": revision.asset_occurrences.filter(asset_type_code="unit_substation").count(),
        "wind_turbines": revision.asset_occurrences.filter(asset_type_code="wind_turbine").count(),
        "lines": revision.asset_occurrences.filter(
            asset_type_code__in=("overhead_line", "cable_line")
        ).count(),
    }
    hierarchy_examples = []
    for type_code in ("unit_substation", "control_building", "wind_turbine", "cable_line"):
        example = revision.asset_occurrences.filter(asset_type_code=type_code).order_by(
            "source_sheet",
            "source_row",
        ).first()
        if example is not None:
            _decorate_power_system_occurrence(example, parent_labels)
            hierarchy_examples.append(example)

    publications = revision.publications.select_related("actor").order_by("-created_at")
    attention_count = revision.review_count + revision.blocked_count
    root_count = revision.asset_occurrences.filter(
        asset_type_code="energy_facility",
        parent_external_key="",
    ).count()
    orphan_count = revision.asset_occurrences.exclude(
        asset_type_code="energy_facility",
    ).filter(parent_external_key="").count()
    dc_control_equipment_count = revision.asset_occurrences.filter(
        asset_type_code="dc_distribution_board",
    ).count()
    shot_count = revision.asset_occurrences.filter(
        asset_type_code="dc_distribution_board",
        dispatcher_name_raw="ШОТ",
    ).count()
    shpt_count = revision.asset_occurrences.filter(
        asset_type_code="dc_distribution_board",
        dispatcher_name_raw__startswith="ЩПТ",
    ).count()
    return render(
        request,
        "imports/power_system_detail.html",
        {
            "employee": employee,
            "revision": revision,
            "page": page,
            "issues": issues,
            "publications": publications,
            "type_counts": power_system_type_counts(revision),
            "status_filter": status_filter,
            "review_status_choices": PowerSystemAssetOccurrence.ReviewStatus.choices,
            "type_filter": type_filter,
            "query": query,
            "can_publish": can_publish_import(request.user),
            "attention_count": attention_count,
            "hierarchy_counts": hierarchy_counts,
            "hierarchy_examples": hierarchy_examples,
            "duplicate_groups": duplicate_groups,
            "duplicate_group_count": sum(
                not group["resolved"] for group in duplicate_groups
            ),
            "grouped_attention_row_count": len(grouped_occurrence_ids),
            "root_count": root_count,
            "orphan_count": orphan_count,
            "dc_control_equipment_count": dc_control_equipment_count,
            "shot_count": shot_count,
            "shpt_count": shpt_count,
        },
    )


@login_required
def power_system_occurrence_decide(request: HttpRequest, public_id, occurrence_id: int) -> HttpResponse:
    employee, revision = power_system_revision_for_user(request.user, public_id)
    occurrence = get_object_or_404(
        revision.asset_occurrences.select_related("merge_target"),
        pk=occurrence_id,
    )
    if request.method != "POST":
        return redirect("imports:power_system_detail", public_id=revision.public_id)
    form = PowerSystemOccurrenceDecisionForm(request.POST)
    if form.is_valid():
        try:
            decide_power_system_occurrence(
                occurrence=occurrence,
                employee=employee,
                action=form.cleaned_data["action"],
                note=form.cleaned_data["note"],
                merge_target_occurrence_id=form.cleaned_data["merge_target_occurrence_id"],
            )
        except ValidationError as error:
            messages.error(request, _validation_message(error))
        else:
            messages.success(request, "Решение по строке сохранено.")
    else:
        messages.error(
            request,
            " ".join(message for messages_list in form.errors.values() for message in messages_list),
        )
    return redirect("imports:power_system_detail", public_id=revision.public_id)


@login_required
def power_system_duplicate_group_decide(
    request: HttpRequest,
    public_id,
    duplicate_group: str,
) -> HttpResponse:
    employee, revision = power_system_revision_for_user(request.user, public_id)
    if request.method != "POST":
        return redirect("imports:power_system_detail", public_id=revision.public_id)
    form = PowerSystemDuplicateGroupDecisionForm(request.POST)
    if form.is_valid():
        try:
            decide_power_system_duplicate_group(
                revision=revision,
                employee=employee,
                duplicate_group=duplicate_group,
                action=form.cleaned_data["action"],
                primary_occurrence_id=form.cleaned_data["primary_occurrence_id"],
                note=form.cleaned_data["note"],
            )
        except ValidationError as error:
            messages.error(request, _validation_message(error))
        else:
            messages.success(request, "Решение по группе исходных строк сохранено.")
    else:
        messages.error(
            request,
            " ".join(
                message
                for messages_list in form.errors.values()
                for message in messages_list
            ),
        )
    return redirect("imports:power_system_detail", public_id=revision.public_id)


@login_required
def power_system_publication(request: HttpRequest, public_id) -> HttpResponse:
    resolver_url_name = getattr(
        request.resolver_match,
        "url_name",
        "",
    )
    is_snapshot_download = (
        resolver_url_name == "power_system_snapshot_download"
    )
    if is_snapshot_download and request.method != "GET":
        return HttpResponse(status=405)
    employee, revision = power_system_revision_for_user(request.user, public_id)
    can_publish = can_publish_import(request.user)
    initial_date = revision.effective_from or timezone.localdate()
    requested_date = request.GET.get("effective_from", "").strip()
    if requested_date:
        try:
            initial_date = date.fromisoformat(requested_date)
        except ValueError:
            pass
    try:
        preview = build_power_system_publication_preview(
            revision=revision,
            effective_from=initial_date,
        )
        if is_snapshot_download:
            payload = preview.canonical_json.encode("utf-8")
            response = HttpResponse(
                payload,
                content_type="application/json; charset=utf-8",
            )
            response["Content-Disposition"] = (
                f'attachment; filename="power-system-{revision.public_id}-canonical.json"'
            )
            response["X-Content-SHA256"] = preview.digest
            response["Cache-Control"] = "no-store"
            response["X-Content-Type-Options"] = "nosniff"
            response["Content-Length"] = str(len(payload))
            return response
    except ValidationError as error:
        messages.error(request, _validation_message(error))
        return redirect("imports:power_system_detail", public_id=revision.public_id)

    if request.method == "POST":
        form = PowerSystemPublicationConfirmationForm(request.POST)
        if form.is_valid() and can_publish:
            try:
                publication = publish_power_system_revision(
                    revision=revision,
                    actor=employee,
                    user=request.user,
                    password=form.cleaned_data["password"],
                    effective_from=form.cleaned_data["effective_from"],
                    expected_digest=form.cleaned_data["preview_digest"],
                )
            except (ValidationError, PermissionDenied) as error:
                form.add_error(
                    None,
                    _validation_message(error)
                    if isinstance(error, ValidationError)
                    else str(error),
                )
            else:
                messages.success(request, "Готовые строки опубликованы контролируемой транзакцией.")
                return redirect(
                    "imports:power_system_publication_result",
                    public_id=revision.public_id,
                    publication_id=publication.public_id,
                )
    else:
        form = PowerSystemPublicationConfirmationForm(
            initial={
                "effective_from": initial_date,
                "preview_digest": preview.digest,
            }
        )
    return render(
        request,
        "imports/power_system_publication.html",
        {
            "employee": employee,
            "revision": revision,
            "preview": preview,
            "form": form,
            "can_publish": can_publish,
        },
    )


@login_required
def power_system_publication_result(
    request: HttpRequest,
    public_id,
    publication_id,
) -> HttpResponse:
    employee, revision = power_system_revision_for_user(request.user, public_id)
    publication = get_object_or_404(
        revision.publications.select_related("actor"),
        public_id=publication_id,
    )
    summary_labels = {
        "selected": "Выбрано строк",
        "hierarchy": "Узлов иерархии",
        "objects": "Объектных строк",
        "quarantined": "Осталось в карантине",
        "excluded": "Исключено",
        "sites": "Энергообъектов",
        "assets_created": "Создано объектов оборудования",
        "assets_reused": "Повторно использовано объектов",
        "aliases_created": "Создано поисковых алиасов",
        "authority_published": "Опубликовано назначений управления и ведения",
        "authority_review_required": "Назначений оставлено на проверке",
        "authority_skipped": "Назначений без создания редакции",
        "remaining_ready": "Осталось готовых строк",
        "remaining_review": "Осталось строк на проверке",
        "remaining_blocked": "Осталось заблокированных строк",
    }
    summary_rows = [
        (summary_labels.get(key, key), value)
        for key, value in publication.result_summary.items()
        if key != "models"
    ]
    return render(
        request,
        "imports/power_system_publication_result.html",
        {
            "employee": employee,
            "revision": revision,
            "publication": publication,
            "summary_rows": summary_rows,
        },
    )


@login_required
def power_system_discard(request: HttpRequest, public_id) -> HttpResponse:
    employee, revision = power_system_revision_for_user(request.user, public_id)
    if request.method == "POST":
        try:
            discard_power_system_revision(revision=revision, employee=employee)
        except ValidationError as error:
            messages.error(request, _validation_message(error))
        else:
            messages.success(request, "Редакция убрана из рабочего списка без физического удаления.")
    return redirect("imports:power_system_list")


PERSONNEL_GRANT_STATE_LABELS = dict(PersonnelAuthorityCell.GrantState.choices)


def _decorate_personnel_row(row: PersonnelSourceRow) -> None:
    cells = list(row.authority_cells.all())
    row.positive_cells = [cell for cell in cells if cell.is_publishable]
    row.ambiguous_cells_list = [
        cell
        for cell in cells
        if cell.grant_state == PersonnelAuthorityCell.GrantState.AMBIGUOUS
    ]
    row.negative_count = sum(
        cell.grant_state == PersonnelAuthorityCell.GrantState.NOT_GRANTED
        for cell in cells
    )
    row.blank_count = sum(
        cell.grant_state == PersonnelAuthorityCell.GrantState.BLANK
        for cell in cells
    )
    for cell in cells:
        cell.grant_state_label = PERSONNEL_GRANT_STATE_LABELS.get(
            cell.grant_state,
            cell.grant_state,
        )


@login_required
def personnel_list(request: HttpRequest) -> HttpResponse:
    employee = require_import_employee(request.user)
    revisions = list(
        personnel_revision_queryset_for_employee(employee).order_by("-created_at", "-id")[:100]
    )
    summary = {
        "total": len(revisions),
        "staged": sum(item.status == PersonnelSourceRevision.Status.STAGED for item in revisions),
        "attention": sum(
            item.review_rows + item.blocked_rows > 0
            for item in revisions
            if item.status != PersonnelSourceRevision.Status.DISCARDED
        ),
        "published": sum(
            item.status
            in {
                PersonnelSourceRevision.Status.PUBLISHED,
                PersonnelSourceRevision.Status.PARTIALLY_PUBLISHED,
            }
            for item in revisions
        ),
    }
    return render(
        request,
        "imports/personnel_list.html",
        {"revisions": revisions, "summary": summary},
    )


@login_required
def personnel_upload(request: HttpRequest) -> HttpResponse:
    employee = require_import_employee(request.user)
    form = PersonnelWorkbookUploadForm(
        request.POST or None,
        request.FILES or None,
        organization=employee.organization,
    )
    if request.method == "POST" and form.is_valid():
        try:
            revision = stage_personnel_workbook(
                uploaded_file=form.cleaned_data["source_file"],
                employee=employee,
                data_profile=form.cleaned_data["data_profile"],
                source_reference=form.cleaned_data["source_reference"],
                effective_from=form.cleaned_data["effective_from"],
            )
        except (PersonnelWorkbookError, PermissionDenied, ValidationError) as error:
            message = (
                _validation_message(error)
                if isinstance(error, ValidationError)
                else str(error)
            )
            form.add_error(None, message)
        else:
            messages.success(
                request,
                "XLSX разобран в изолированную staging-редакцию. Рабочие карточки не изменены.",
            )
            return redirect("imports:personnel_detail", public_id=revision.public_id)
    return render(request, "imports/personnel_upload.html", {"form": form})


@login_required
def personnel_detail(request: HttpRequest, public_id) -> HttpResponse:
    employee, revision = personnel_revision_for_user(request.user, public_id)
    status_filter = request.GET.get("status", "ALL").upper()
    valid_filters = {"ALL", *PersonnelSourceRow.ReviewStatus.values}
    if status_filter not in valid_filters:
        status_filter = "ALL"
    rows = (
        revision.person_rows.select_related(
            "matched_employee",
            "matched_employee__division",
            "matched_employee__position",
            "published_employee",
        )
        .prefetch_related("authority_cells__right_definition")
        .order_by("source_row_number")
    )
    if status_filter != "ALL":
        rows = rows.filter(review_status=status_filter)
    page = Paginator(rows, 20).get_page(request.GET.get("page"))
    for row in page.object_list:
        _decorate_personnel_row(row)
    return render(
        request,
        "imports/personnel_detail.html",
        {
            "employee": employee,
            "revision": revision,
            "page": page,
            "status_filter": status_filter,
            "can_publish": can_publish_import(request.user),
            "is_development_database": (
                getattr(settings, "EOD_DATABASE_PROFILE", "presentation") == "development"
            ),
        },
    )


@login_required
def personnel_publication(request: HttpRequest, public_id) -> HttpResponse:
    employee, revision = personnel_revision_for_user(request.user, public_id)
    if revision.status != PersonnelSourceRevision.Status.STAGED:
        publication = PersonnelPublication.objects.filter(source_revision=revision).first()
        if publication is not None:
            return redirect(
                "imports:personnel_publication_result",
                public_id=revision.public_id,
                publication_id=publication.public_id,
            )
        messages.error(request, "Эта staging-редакция больше не доступна для публикации.")
        return redirect("imports:personnel_detail", public_id=revision.public_id)

    preview = build_personnel_publication_preview(revision)
    initial = {"preview_digest": preview.digest}
    form = PersonnelPublicationConfirmationForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        try:
            publication = publish_personnel_revision(
                revision=revision,
                actor=employee,
                user=request.user,
                password=form.cleaned_data["password"],
                expected_digest=form.cleaned_data["preview_digest"],
            )
        except (PermissionDenied, ValidationError) as error:
            message = (
                _validation_message(error)
                if isinstance(error, ValidationError)
                else str(error)
            )
            form.add_error(None, message)
        else:
            messages.success(request, "Контролируемая частичная публикация персонала завершена.")
            return redirect(
                "imports:personnel_publication_result",
                public_id=revision.public_id,
                publication_id=publication.public_id,
            )
    return render(
        request,
        "imports/personnel_publication.html",
        {
            "revision": revision,
            "preview": preview,
            "form": form,
            "can_publish": can_publish_import(request.user),
        },
    )


@login_required
def personnel_publication_result(
    request: HttpRequest,
    public_id,
    publication_id,
) -> HttpResponse:
    _employee, revision = personnel_revision_for_user(request.user, public_id)
    publication = get_object_or_404(
        PersonnelPublication.objects.select_related("actor", "source_revision"),
        public_id=publication_id,
        source_revision=revision,
    )
    return render(
        request,
        "imports/personnel_publication_result.html",
        {"revision": revision, "publication": publication},
    )


@login_required
def personnel_discard(request: HttpRequest, public_id) -> HttpResponse:
    if request.method != "POST":
        return redirect("imports:personnel_detail", public_id=public_id)
    employee, revision = personnel_revision_for_user(request.user, public_id)
    try:
        discard_personnel_revision(revision=revision, employee=employee)
    except ValidationError as error:
        messages.error(request, _validation_message(error))
    else:
        messages.success(request, "Staging-редакция убрана из рабочего списка.")
    return redirect("imports:personnel_list")
