from __future__ import annotations

from typing import Any

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_http_methods, require_POST

from apps.equipment.models import EquipmentAsset
from apps.operational_documents.models import OperationalDocumentRecord
from apps.operational_documents.services import (
    normalize_search_text,
    require_operational_document_employee,
)
from apps.operational_log.models import OperationalLogEntry
from apps.organizations.models import Employee

from .constants import (
    APPROVED_PRINT_COLUMNS,
    DOCUMENT_TYPE_CODE,
    DOCUMENT_TYPE_NAME,
    FIELD_DEFECT_DESCRIPTION,
    FIELD_DETECTED_AT,
    FIELD_ELIMINATION_DEADLINE,
    FIELD_RESOLUTION_WORK_SUMMARY,
    FIELD_RESOLVED_AT,
    ROLE_DISCOVERED_BY,
    ROLE_OPERATIONAL_ACKNOWLEDGER,
    ROLE_OPERATIONS_RESPONSIBLE,
    ROLE_RESOLUTION_RESPONSIBLE,
    SOURCE_APPENDIX,
    SOURCE_DOCUMENT,
    SOURCE_SECTION,
    STATUS_CLOSED,
    STATUS_IN_PROGRESS,
    STATUS_REGISTERED,
    STATUS_RESOLVED,
)
from .forms import (
    DeadlineConfirmationForm,
    DeadlineExtensionForm,
    DefectRegistrationForm,
    ResolutionConfirmationForm,
)
from .models import DefectActionCode, EquipmentDefectVolume
from .services import (
    acknowledge_resolution,
    close_defect,
    confirm_deadline,
    confirm_resolution,
    defect_field_display,
    ensure_defect_document_type,
    extend_deadline,
    participant_for_role,
    register_defect,
)


def _validation_message(error: ValidationError) -> str:
    if hasattr(error, "message_dict"):
        return "; ".join(
            f"{field}: {', '.join(values)}"
            for field, values in error.message_dict.items()
        )
    return "; ".join(error.messages)


def _record_queryset(employee: Employee) -> QuerySet[OperationalDocumentRecord]:
    return (
        OperationalDocumentRecord.objects.filter(
            organization=employee.organization,
            document_type__code=DOCUMENT_TYPE_CODE,
            equipment_defect_context__isnull=False,
        )
        .select_related(
            "document_type",
            "schema_revision",
            "workplace",
            "created_by",
            "updated_by",
            "equipment_defect_context",
            "equipment_defect_context__volume",
        )
        .prefetch_related(
            "participants",
            "participants__employee",
            "equipment_links",
            "equipment_links__equipment",
            "equipment_defect_actions",
            "revisions",
        )
    )


def _record_for_employee(public_id: Any, employee: Employee) -> OperationalDocumentRecord:
    return get_object_or_404(_record_queryset(employee), public_id=public_id)


def _participant(record: OperationalDocumentRecord, role_code: str):
    return participant_for_role(record, role_code)


def _operational_log_link(record: OperationalDocumentRecord):
    try:
        return record.equipment_defect_operational_log_link
    except ObjectDoesNotExist:
        return None


def _extension_rows(record: OperationalDocumentRecord) -> list[Any]:
    return list(
        record.equipment_defect_actions.filter(
            action_code=DefectActionCode.DEADLINE_EXTENDED
        ).order_by("occurred_at", "pk")
    )


def _acknowledgement_rows(record: OperationalDocumentRecord) -> list[Any]:
    return list(
        record.equipment_defect_actions.filter(
            action_code=DefectActionCode.ACKNOWLEDGED
        ).order_by("occurred_at", "pk")
    )


def _row(record: OperationalDocumentRecord) -> dict[str, Any]:
    equipment_links = list(record.equipment_links.all())
    return {
        "record": record,
        "equipment": equipment_links[0] if equipment_links else None,
        "discovered_by": _participant(record, ROLE_DISCOVERED_BY),
        "operations_responsible": _participant(record, ROLE_OPERATIONS_RESPONSIBLE),
        "resolution_responsible": _participant(record, ROLE_RESOLUTION_RESPONSIBLE),
        "acknowledgers": _acknowledgement_rows(record),
        "extensions": _extension_rows(record),
        "detected_at": defect_field_display(record, FIELD_DETECTED_AT),
        "description": defect_field_display(record, FIELD_DEFECT_DESCRIPTION),
        "deadline": defect_field_display(record, FIELD_ELIMINATION_DEADLINE),
        "resolved_at": defect_field_display(record, FIELD_RESOLVED_AT),
        "work_summary": defect_field_display(record, FIELD_RESOLUTION_WORK_SUMMARY),
        "operational_log_link": _operational_log_link(record),
    }


def _source_context() -> dict[str, str]:
    return {
        "document": SOURCE_DOCUMENT,
        "section": SOURCE_SECTION,
        "appendix": SOURCE_APPENDIX,
    }


def _valid_date_filter(request: HttpRequest, key: str):
    raw_value = request.GET.get(key, "").strip()
    if not raw_value:
        return "", None
    parsed = parse_date(raw_value)
    if parsed is None:
        messages.warning(request, "Некорректная дата фильтра проигнорирована.")
        return "", None
    return raw_value, parsed


@login_required
def registry(request: HttpRequest) -> HttpResponse:
    employee = require_operational_document_employee(request.user)
    ensure_defect_document_type(employee)
    records = _record_queryset(employee)

    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip().upper()
    equipment_id = request.GET.get("equipment", "").strip()
    date_from_raw, date_from = _valid_date_filter(request, "date_from")
    date_to_raw, date_to = _valid_date_filter(request, "date_to")

    allowed_statuses = {
        STATUS_REGISTERED,
        STATUS_IN_PROGRESS,
        STATUS_RESOLVED,
        STATUS_CLOSED,
    }
    if status and status not in allowed_statuses:
        messages.warning(request, "Неизвестное состояние фильтра проигнорировано.")
        status = ""
    if query:
        records = records.filter(search_text__contains=normalize_search_text(query))
    if status:
        records = records.filter(status_code=status)
    if equipment_id:
        records = records.filter(equipment_links__equipment__public_id=equipment_id)
    if date_from is not None:
        records = records.filter(event_at__date__gte=date_from)
    if date_to is not None:
        records = records.filter(event_at__date__lte=date_to)

    records = records.distinct().order_by("-event_at", "-pk")
    all_records = _record_queryset(employee)
    return render(
        request,
        "equipment_defects/registry.html",
        {
            "rows": [_row(record) for record in records],
            "source": _source_context(),
            "document_type_name": DOCUMENT_TYPE_NAME,
            "counts": {
                "total": all_records.count(),
                "registered": all_records.filter(status_code=STATUS_REGISTERED).count(),
                "in_progress": all_records.filter(status_code=STATUS_IN_PROGRESS).count(),
                "resolved": all_records.filter(status_code=STATUS_RESOLVED).count(),
                "closed": all_records.filter(status_code=STATUS_CLOSED).count(),
            },
            "equipment_assets": EquipmentAsset.objects.filter(
                organization=employee.organization
            ).order_by("code")[:500],
            "status_options": (
                (STATUS_REGISTERED, "Зарегистрирован"),
                (STATUS_IN_PROGRESS, "В работе"),
                (STATUS_RESOLVED, "Устранён"),
                (STATUS_CLOSED, "Закрыт"),
            ),
            "volumes": EquipmentDefectVolume.objects.filter(
                organization=employee.organization
            ).select_related("workplace"),
            "filters": {
                "q": query,
                "status": status,
                "equipment": equipment_id,
                "date_from": date_from_raw,
                "date_to": date_to_raw,
            },
        },
    )


def _registration_view(
    request: HttpRequest,
    *,
    source_entry: OperationalLogEntry | None = None,
) -> HttpResponse:
    employee = require_operational_document_employee(request.user)
    ensure_defect_document_type(employee)
    form = DefectRegistrationForm(
        request.POST or None,
        employee=employee,
        source_entry=source_entry,
    )
    if request.method == "POST" and form.is_valid():
        try:
            record = register_defect(
                actor=employee,
                workplace=form.cleaned_data["workplace"],
                equipment=form.cleaned_data["equipment"],
                discovered_by=form.cleaned_data["discovered_by"],
                detected_at=form.cleaned_data["detected_at"],
                defect_description=form.cleaned_data["defect_description"],
                operational_log_entry=form.cleaned_data["operational_log_entry"],
            )
        except ValidationError as error:
            form.add_error(None, _validation_message(error))
        else:
            messages.success(
                request,
                f"Дефект {record.registration_number} зарегистрирован.",
            )
            return redirect("equipment_defects:detail", public_id=record.public_id)
    return render(
        request,
        "equipment_defects/registration_form.html",
        {
            "form": form,
            "source_entry": source_entry,
            "source": _source_context(),
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def create(request: HttpRequest) -> HttpResponse:
    return _registration_view(request)


@login_required
@require_http_methods(["GET", "POST"])
def create_from_operational_log(request: HttpRequest, entry_id: int) -> HttpResponse:
    employee = require_operational_document_employee(request.user)
    source_entry = get_object_or_404(
        OperationalLogEntry.objects.select_related("journal", "journal__workplace"),
        pk=entry_id,
        journal__organization=employee.organization,
    )
    return _registration_view(request, source_entry=source_entry)


@login_required
def detail(request: HttpRequest, public_id: Any) -> HttpResponse:
    employee = require_operational_document_employee(request.user)
    record = _record_for_employee(public_id, employee)
    return render(
        request,
        "equipment_defects/detail.html",
        {
            "row": _row(record),
            "record": record,
            "actions": list(
                record.equipment_defect_actions.select_related(
                    "actor",
                    "record_revision",
                ).order_by("occurred_at", "pk")
            ),
            "source": _source_context(),
            "can_confirm_deadline": record.status_code == STATUS_REGISTERED,
            "can_extend_deadline": record.status_code == STATUS_IN_PROGRESS,
            "can_confirm_resolution": record.status_code == STATUS_IN_PROGRESS,
            "can_acknowledge": (
                record.status_code == STATUS_RESOLVED
                and employee.position.is_operational
                and not record.equipment_defect_actions.filter(
                    action_code=DefectActionCode.ACKNOWLEDGED,
                    actor=employee,
                ).exists()
            ),
            "can_close": (
                record.status_code == STATUS_RESOLVED
                and record.equipment_defect_actions.filter(
                    action_code=DefectActionCode.ACKNOWLEDGED
                ).exists()
            ),
        },
    )


def _action_form_context(
    *,
    form: Any,
    record: OperationalDocumentRecord,
    page_title: str,
    submit_label: str,
) -> dict[str, Any]:
    return {
        "form": form,
        "record": record,
        "page_title": page_title,
        "submit_label": submit_label,
        "source": _source_context(),
    }


@login_required
@require_http_methods(["GET", "POST"])
def confirm_deadline_view(request: HttpRequest, public_id: Any) -> HttpResponse:
    employee = require_operational_document_employee(request.user)
    record = _record_for_employee(public_id, employee)
    form = DeadlineConfirmationForm(request.POST or None, employee=employee)
    if request.method == "POST" and form.is_valid():
        try:
            updated = confirm_deadline(
                record=record,
                actor=employee,
                responsible=form.cleaned_data["responsible"],
                deadline=form.cleaned_data["elimination_deadline"],
            )
        except ValidationError as error:
            form.add_error(None, _validation_message(error))
        else:
            messages.success(request, "Срок устранения подтверждён.")
            return redirect("equipment_defects:detail", public_id=updated.public_id)
    return render(
        request,
        "equipment_defects/action_form.html",
        _action_form_context(
            form=form,
            record=record,
            page_title="Подтвердить срок устранения",
            submit_label="Подтвердить срок",
        ),
    )


@login_required
@require_http_methods(["GET", "POST"])
def extend_deadline_view(request: HttpRequest, public_id: Any) -> HttpResponse:
    employee = require_operational_document_employee(request.user)
    record = _record_for_employee(public_id, employee)
    form = DeadlineExtensionForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            updated = extend_deadline(
                record=record,
                actor=employee,
                new_deadline=form.cleaned_data["new_deadline"],
                reason=form.cleaned_data["reason"],
            )
        except ValidationError as error:
            form.add_error(None, _validation_message(error))
        else:
            messages.success(request, "Срок устранения продлён с сохранением истории.")
            return redirect("equipment_defects:detail", public_id=updated.public_id)
    return render(
        request,
        "equipment_defects/action_form.html",
        _action_form_context(
            form=form,
            record=record,
            page_title="Продлить срок устранения",
            submit_label="Зафиксировать продление",
        ),
    )


@login_required
@require_http_methods(["GET", "POST"])
def confirm_resolution_view(request: HttpRequest, public_id: Any) -> HttpResponse:
    employee = require_operational_document_employee(request.user)
    record = _record_for_employee(public_id, employee)
    form = ResolutionConfirmationForm(request.POST or None, employee=employee)
    if request.method == "POST" and form.is_valid():
        try:
            updated = confirm_resolution(
                record=record,
                actor=employee,
                responsible=form.cleaned_data["responsible"],
                resolved_at=form.cleaned_data["resolved_at"],
                work_summary=form.cleaned_data["work_summary"],
            )
        except ValidationError as error:
            form.add_error(None, _validation_message(error))
        else:
            messages.success(request, "Устранение дефекта подтверждено.")
            return redirect("equipment_defects:detail", public_id=updated.public_id)
    return render(
        request,
        "equipment_defects/action_form.html",
        _action_form_context(
            form=form,
            record=record,
            page_title="Подтвердить устранение дефекта",
            submit_label="Подтвердить устранение",
        ),
    )


@login_required
@require_POST
def acknowledge_view(request: HttpRequest, public_id: Any) -> HttpResponse:
    employee = require_operational_document_employee(request.user)
    record = _record_for_employee(public_id, employee)
    try:
        updated = acknowledge_resolution(record=record, actor=employee)
    except ValidationError as error:
        messages.error(request, _validation_message(error))
    else:
        messages.success(request, "Ознакомление зафиксировано персональным действием.")
        return redirect("equipment_defects:detail", public_id=updated.public_id)
    return redirect("equipment_defects:detail", public_id=record.public_id)


@login_required
@require_POST
def close_view(request: HttpRequest, public_id: Any) -> HttpResponse:
    employee = require_operational_document_employee(request.user)
    record = _record_for_employee(public_id, employee)
    try:
        updated = close_defect(record=record, actor=employee)
    except ValidationError as error:
        messages.error(request, _validation_message(error))
    else:
        messages.success(request, "Дефект закрыт. Запись переведена в конечное состояние.")
        return redirect("equipment_defects:detail", public_id=updated.public_id)
    return redirect("equipment_defects:detail", public_id=record.public_id)


def _volume_for_print(
    request: HttpRequest,
    employee: Employee,
) -> EquipmentDefectVolume:
    volume_id = request.GET.get("volume", "").strip()
    volumes = EquipmentDefectVolume.objects.filter(
        organization=employee.organization
    ).select_related("workplace")
    if volume_id:
        return get_object_or_404(volumes, public_id=volume_id)
    if employee.workplace_id:
        current = volumes.filter(workplace=employee.workplace).order_by(
            "-sequence_number"
        ).first()
        if current is not None:
            return current
    volume = volumes.order_by("workplace__name", "-sequence_number").first()
    if volume is None:
        raise ValidationError("Нет тома журнала дефектов для печати.")
    return volume


@login_required
def print_view(request: HttpRequest) -> HttpResponse:
    employee = require_operational_document_employee(request.user)
    try:
        volume = _volume_for_print(request, employee)
    except ValidationError as error:
        messages.error(request, _validation_message(error))
        return redirect("equipment_defects:registry")
    records = _record_queryset(employee).filter(
        equipment_defect_context__volume=volume
    ).order_by("event_at", "pk")
    return render(
        request,
        "equipment_defects/print.html",
        {
            "volume": volume,
            "rows": [_row(record) for record in records],
            "columns": APPROVED_PRINT_COLUMNS,
            "source": _source_context(),
            "printed_at": timezone.localtime(),
        },
    )
