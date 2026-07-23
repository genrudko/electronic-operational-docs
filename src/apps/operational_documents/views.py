from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST

from .forms import (
    OperationalDocumentRecordForm,
    OperationalDocumentTransitionForm,
    OperationalDocumentTypeChoiceForm,
    OperationalDocumentTypeForm,
    OperationalFieldDefinitionFormSet,
    field_definitions_from_formset,
)
from .models import (
    OperationalDocumentRecord,
    OperationalDocumentType,
    OperationalDocumentTypeRevision,
    SchemaPublicationStatus,
)
from .services import (
    available_transitions,
    can_administer_operational_document_types,
    create_and_publish_type,
    create_record,
    current_published_revision,
    field_display_rows,
    normalize_search_text,
    require_operational_document_employee,
    require_operational_document_type_administrator,
    transition_record,
    update_record,
)


def _validation_message(error: ValidationError) -> str:
    if hasattr(error, "message_dict"):
        return "; ".join(
            f"{field}: {', '.join(values)}"
            for field, values in error.message_dict.items()
        )
    return "; ".join(error.messages)


def _record_for_employee(public_id, employee):
    return get_object_or_404(
        OperationalDocumentRecord.objects.select_related(
            "organization",
            "document_type",
            "schema_revision",
            "workplace",
            "created_by",
            "updated_by",
        ).prefetch_related(
            "participants",
            "equipment_links",
            "document_links",
            "outgoing_relations",
        ),
        public_id=public_id,
        organization=employee.organization,
    )


def _revision_for_type(document_type: OperationalDocumentType) -> OperationalDocumentTypeRevision:
    revision = current_published_revision(document_type)
    if revision is None:
        raise ValidationError("Для типа документа отсутствует опубликованная редакция.")
    return revision


@login_required
def registry(request: HttpRequest) -> HttpResponse:
    employee = require_operational_document_employee(request.user)
    records = (
        OperationalDocumentRecord.objects.filter(organization=employee.organization)
        .select_related("document_type", "schema_revision", "workplace", "created_by")
        .prefetch_related("equipment_links", "participants")
    )
    q = request.GET.get("q", "").strip()
    document_type_id = request.GET.get("type", "").strip()
    status_code = request.GET.get("status", "").strip().upper()
    workplace_code = request.GET.get("workplace", "").strip()
    equipment_id = request.GET.get("equipment", "").strip()
    date_from = request.GET.get("date_from", "").strip()
    date_to = request.GET.get("date_to", "").strip()
    if q:
        records = records.filter(search_text__contains=normalize_search_text(q))
    if document_type_id:
        records = records.filter(document_type__public_id=document_type_id)
    if status_code:
        records = records.filter(status_code=status_code)
    if workplace_code:
        records = records.filter(workplace__code=workplace_code)
    if equipment_id:
        records = records.filter(equipment_links__equipment__public_id=equipment_id)
    if date_from:
        records = records.filter(event_at__date__gte=date_from)
    if date_to:
        records = records.filter(event_at__date__lte=date_to)
    records = records.distinct().order_by("-event_at", "-pk")
    record_rows = list(records)
    for record in record_rows:
        visible_values = [
            value
            for value in record.field_values.values()
            if value.get("show_in_list") and value.get("display") not in (None, "")
        ]
        record.visible_values = visible_values[:4]
    all_records = OperationalDocumentRecord.objects.filter(organization=employee.organization)
    status_options = sorted(
        {
            (record.status_code, record.status_name_snapshot)
            for record in all_records.only("status_code", "status_name_snapshot")
        },
        key=lambda item: item[1],
    )
    return render(
        request,
        "operational_documents/registry.html",
        {
            "records": record_rows,
            "counts": {
                "total": all_records.count(),
                "active": all_records.filter(status_is_terminal=False).count(),
                "closed": all_records.filter(status_is_terminal=True).count(),
                "types": OperationalDocumentType.objects.filter(
                    organization=employee.organization,
                    is_active=True,
                ).count(),
            },
            "document_types": OperationalDocumentType.objects.filter(
                organization=employee.organization,
                is_active=True,
            ).order_by("name"),
            "workplaces": employee.organization.workplaces.filter(is_active=True).order_by("name"),
            "equipment_assets": employee.organization.equipment_assets.order_by("code")[:500],
            "status_options": status_options,
            "filters": {
                "q": q,
                "type": document_type_id,
                "status": status_code,
                "workplace": workplace_code,
                "equipment": equipment_id,
                "date_from": date_from,
                "date_to": date_to,
            },
        },
    )


@login_required
def type_registry(request: HttpRequest) -> HttpResponse:
    employee = require_operational_document_employee(request.user)
    document_types = list(
        OperationalDocumentType.objects.filter(organization=employee.organization)
        .prefetch_related("revisions")
        .order_by("name")
    )
    for document_type in document_types:
        published = [
            revision
            for revision in document_type.revisions.all()
            if revision.status == SchemaPublicationStatus.PUBLISHED
        ]
        document_type.current_published_revision = max(
            published,
            key=lambda revision: revision.revision_number,
            default=None,
        )
    return render(
        request,
        "operational_documents/type_registry.html",
        {
            "document_types": document_types,
            "can_administer": can_administer_operational_document_types(request.user),
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def type_create(request: HttpRequest) -> HttpResponse:
    employee = require_operational_document_type_administrator(request.user)
    form = OperationalDocumentTypeForm(request.POST or None)
    formset = OperationalFieldDefinitionFormSet(
        request.POST or None,
        prefix="fields",
        initial=(
            [
                {
                    "label": "Описание",
                    "code": "DESCRIPTION",
                    "field_type": "LONG_TEXT",
                    "required": True,
                    "show_in_list": True,
                    "searchable": True,
                }
            ]
            if request.method == "GET"
            else None
        ),
    )
    if request.method == "POST" and form.is_valid() and formset.is_valid():
        try:
            document_type = create_and_publish_type(
                actor=employee,
                code=form.cleaned_data["code"],
                name=form.cleaned_data["name"],
                short_name=form.cleaned_data["short_name"],
                description=form.cleaned_data["description"],
                number_prefix=form.cleaned_data["number_prefix"],
                number_width=form.cleaned_data["number_width"],
                requires_workplace=form.cleaned_data["requires_workplace"],
                field_definitions=field_definitions_from_formset(formset),
            )
        except ValidationError as error:
            form.add_error(None, _validation_message(error))
        else:
            messages.success(
                request,
                "Тип оперативного документа и его первая неизменяемая редакция опубликованы.",
            )
            return redirect("operational_documents:type_detail", public_id=document_type.public_id)
    return render(
        request,
        "operational_documents/type_form.html",
        {
            "form": form,
            "formset": formset,
        },
    )


@login_required
def type_detail(request: HttpRequest, public_id) -> HttpResponse:
    employee = require_operational_document_employee(request.user)
    document_type = get_object_or_404(
        OperationalDocumentType.objects.prefetch_related("revisions"),
        public_id=public_id,
        organization=employee.organization,
    )
    revisions = document_type.revisions.select_related("created_by", "published_by").order_by(
        "-revision_number"
    )
    current_revision = current_published_revision(document_type)
    return render(
        request,
        "operational_documents/type_detail.html",
        {
            "document_type": document_type,
            "revisions": revisions,
            "current_revision": current_revision,
            "can_administer": can_administer_operational_document_types(request.user),
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def record_choose_type(request: HttpRequest) -> HttpResponse:
    employee = require_operational_document_employee(request.user)
    form = OperationalDocumentTypeChoiceForm(request.POST or None, employee=employee)
    if request.method == "POST" and form.is_valid():
        return redirect(
            "operational_documents:record_create",
            type_public_id=form.cleaned_data["document_type"].public_id,
        )
    return render(
        request,
        "operational_documents/choose_type.html",
        {"form": form},
    )


@login_required
@require_http_methods(["GET", "POST"])
def record_create(request: HttpRequest, type_public_id) -> HttpResponse:
    employee = require_operational_document_employee(request.user)
    document_type = get_object_or_404(
        OperationalDocumentType,
        public_id=type_public_id,
        organization=employee.organization,
        is_active=True,
    )
    try:
        revision = _revision_for_type(document_type)
    except ValidationError as error:
        messages.error(request, _validation_message(error))
        return redirect("operational_documents:type_registry")
    initial = {"event_at": timezone.localtime().replace(second=0, microsecond=0)}
    if employee.workplace_id:
        initial["workplace"] = employee.workplace
    form = OperationalDocumentRecordForm(
        request.POST or None,
        employee=employee,
        revision=revision,
        initial=initial,
    )
    if request.method == "POST" and form.is_valid():
        try:
            record = create_record(
                revision=revision,
                actor=employee,
                title=form.cleaned_data["title"],
                summary=form.cleaned_data["summary"],
                event_at=form.cleaned_data["event_at"],
                workplace=form.cleaned_data["workplace"],
                field_values=form.field_values_payload(),
                participant_map=form.participant_map(),
                equipment_assets=form.cleaned_data["equipment_assets"],
                documents=form.cleaned_data["related_documents"],
                related_records=form.cleaned_data["related_records"],
            )
        except ValidationError as error:
            form.add_error(None, _validation_message(error))
        else:
            messages.success(
                request,
                f"Оперативная запись {record.registration_number} создана.",
            )
            return redirect("operational_documents:record_detail", public_id=record.public_id)
    return render(
        request,
        "operational_documents/record_form.html",
        {
            "form": form,
            "document_type": document_type,
            "revision": revision,
            "page_title": "Новая оперативная запись",
            "submit_label": "Создать запись",
        },
    )


@login_required
def record_detail(request: HttpRequest, public_id) -> HttpResponse:
    employee = require_operational_document_employee(request.user)
    record = _record_for_employee(public_id, employee)
    revisions = record.revisions.select_related("actor").order_by("-revision_number")
    audit_events = record.audit_events.select_related("actor").order_by("-occurred_at", "-pk")
    outgoing_relations = record.outgoing_relations.select_related("target_record", "created_by")
    incoming_relations = record.incoming_relations.select_related("source_record", "created_by")
    return render(
        request,
        "operational_documents/record_detail.html",
        {
            "record": record,
            "field_rows": field_display_rows(record),
            "participants": record.participants.select_related("employee").all(),
            "equipment_links": record.equipment_links.select_related("equipment").all(),
            "document_links": record.document_links.select_related("document").all(),
            "outgoing_relations": outgoing_relations,
            "incoming_relations": incoming_relations,
            "revisions": revisions,
            "audit_events": audit_events,
            "transitions": available_transitions(record),
            "transition_form": OperationalDocumentTransitionForm(),
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def record_edit(request: HttpRequest, public_id) -> HttpResponse:
    employee = require_operational_document_employee(request.user)
    record = _record_for_employee(public_id, employee)
    if record.status_is_terminal:
        messages.error(request, "Запись в конечном состоянии нельзя редактировать.")
        return redirect("operational_documents:record_detail", public_id=record.public_id)
    form = OperationalDocumentRecordForm(
        request.POST or None,
        employee=employee,
        revision=record.schema_revision,
        record=record,
    )
    if request.method == "POST" and form.is_valid():
        try:
            updated = update_record(
                record=record,
                actor=employee,
                title=form.cleaned_data["title"],
                summary=form.cleaned_data["summary"],
                event_at=form.cleaned_data["event_at"],
                workplace=form.cleaned_data["workplace"],
                field_values=form.field_values_payload(),
                participant_map=form.participant_map(),
                equipment_assets=form.cleaned_data["equipment_assets"],
                documents=form.cleaned_data["related_documents"],
                related_records=form.cleaned_data["related_records"],
                comment=form.cleaned_data["change_comment"],
            )
        except ValidationError as error:
            form.add_error(None, _validation_message(error))
        else:
            messages.success(request, f"Запись обновлена; создана редакция № {updated.version}.")
            return redirect("operational_documents:record_detail", public_id=updated.public_id)
    return render(
        request,
        "operational_documents/record_form.html",
        {
            "form": form,
            "record": record,
            "document_type": record.document_type,
            "revision": record.schema_revision,
            "page_title": f"Изменение {record.registration_number}",
            "submit_label": "Сохранить новую редакцию",
        },
    )


@login_required
@require_POST
def record_transition(request: HttpRequest, public_id) -> HttpResponse:
    employee = require_operational_document_employee(request.user)
    record = _record_for_employee(public_id, employee)
    form = OperationalDocumentTransitionForm(request.POST)
    if form.is_valid():
        try:
            updated = transition_record(
                record=record,
                actor=employee,
                transition_code=form.cleaned_data["transition_code"],
                comment=form.cleaned_data["comment"],
            )
        except ValidationError as error:
            messages.error(request, _validation_message(error))
        else:
            messages.success(request, f"Состояние изменено: {updated.status_name_snapshot}.")
    else:
        messages.error(request, "Переход состояния не выполнен.")
    return redirect("operational_documents:record_detail", public_id=record.public_id)
