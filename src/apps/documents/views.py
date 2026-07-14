from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from apps.equipment.services import document_equipment_rows

from .forms import (
    DocumentDraftForm,
    DocumentLinkForm,
    DocumentRegistrationConfirmationForm,
)
from .models import Document
from .services import (
    create_document_draft,
    create_document_link,
    register_document_with_password,
    registration_confirmation_preview,
    require_document_employee,
    update_document_draft,
    verify_document_integrity,
)


def _validation_message(error: ValidationError) -> str:
    if hasattr(error, "message_dict"):
        return "; ".join(
            f"{field}: {', '.join(messages_list)}"
            for field, messages_list in error.message_dict.items()
        )
    return "; ".join(error.messages)


@login_required
def document_list(request: HttpRequest) -> HttpResponse:
    employee = require_document_employee(request.user)
    documents = (
        Document.objects.filter(organization=employee.organization)
        .select_related(
            "document_type",
            "current_version",
            "created_by",
            "registered_by",
        )
        .order_by("-created_at", "-pk")
    )
    counts = {
        "total": documents.count(),
        "drafts": documents.filter(status=Document.Status.DRAFT).count(),
        "registered": documents.filter(status=Document.Status.REGISTERED).count(),
    }
    return render(
        request,
        "documents/list.html",
        {
            "documents": documents,
            "counts": counts,
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def document_create(request: HttpRequest) -> HttpResponse:
    employee = require_document_employee(request.user)
    form = DocumentDraftForm(
        request.POST or None,
        employee=employee,
    )
    if request.method == "POST" and form.is_valid():
        document = create_document_draft(
            document_type=form.cleaned_data["document_type"],
            actor=employee,
            title=form.cleaned_data["title"],
            content={
                "subject": form.cleaned_data["subject"],
                "body": form.cleaned_data["body"],
            },
            equipment_assets=form.cleaned_data["equipment_assets"],
        )
        messages.success(request, "Черновик документа создан.")
        return redirect("documents:detail", public_id=document.public_id)
    return render(
        request,
        "documents/form.html",
        {
            "form": form,
            "page_title": "Новый черновик",
            "submit_label": "Создать черновик",
        },
    )


def _document_for_employee(public_id, employee):
    return get_object_or_404(
        Document.objects.select_related(
            "organization",
            "document_type",
            "current_version",
            "current_version__created_by",
            "registered_by",
            "created_by",
        ),
        public_id=public_id,
        organization=employee.organization,
    )


@login_required
def document_detail(request: HttpRequest, public_id) -> HttpResponse:
    employee = require_document_employee(request.user)
    document = _document_for_employee(public_id, employee)
    versions = document.versions.select_related("created_by", "registered_by").order_by(
        "-version_number"
    )
    audit_events = (
        document.audit_events.select_related(
            "actor_employee",
            "document_version",
        )
        .all()
        .order_by("-occurred_at", "-pk")
    )
    outgoing_links = document.outgoing_links.select_related(
        "target_document",
        "created_by",
    )
    incoming_links = document.incoming_links.select_related(
        "source_document",
        "created_by",
    )
    link_form = (
        DocumentLinkForm(
            employee=employee,
            source_document=document,
        )
        if document.status == Document.Status.REGISTERED
        else None
    )
    return render(
        request,
        "documents/detail.html",
        {
            "document": document,
            "versions": versions,
            "audit_events": audit_events,
            "outgoing_links": outgoing_links,
            "incoming_links": incoming_links,
            "link_form": link_form,
            "equipment_rows": document_equipment_rows(document),
            "integrity": (
                verify_document_integrity(document)
                if document.status == Document.Status.REGISTERED
                else None
            ),
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def document_edit(request: HttpRequest, public_id) -> HttpResponse:
    employee = require_document_employee(request.user)
    document = _document_for_employee(public_id, employee)
    if document.status != Document.Status.DRAFT:
        messages.error(request, "Зарегистрированный документ нельзя редактировать.")
        return redirect("documents:detail", public_id=document.public_id)

    version = document.current_version
    initial = {
        "document_type": document.document_type,
        "title": document.title,
        "subject": version.content.get("subject", "") if version else "",
        "body": version.content.get("body", "") if version else "",
    }
    form = DocumentDraftForm(
        request.POST or None,
        employee=employee,
        document=document,
        initial=initial,
    )
    if request.method == "POST" and form.is_valid():
        try:
            update_document_draft(
                document=document,
                actor=employee,
                title=form.cleaned_data["title"],
                content={
                    "subject": form.cleaned_data["subject"],
                    "body": form.cleaned_data["body"],
                },
                equipment_assets=form.cleaned_data["equipment_assets"],
            )
        except ValidationError as error:
            form.add_error(None, _validation_message(error))
        else:
            messages.success(request, "Черновик обновлён.")
            return redirect("documents:detail", public_id=document.public_id)
    return render(
        request,
        "documents/form.html",
        {
            "form": form,
            "document": document,
            "page_title": "Редактирование черновика",
            "submit_label": "Сохранить черновик",
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def document_register(request: HttpRequest, public_id) -> HttpResponse:
    employee = require_document_employee(request.user)
    document = _document_for_employee(public_id, employee)
    if document.status != Document.Status.DRAFT:
        messages.error(request, "Документ уже зарегистрирован.")
        return redirect("documents:detail", public_id=document.public_id)

    form = DocumentRegistrationConfirmationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            result = register_document_with_password(
                document=document,
                actor=employee,
                user=request.user,
                password=form.cleaned_data["password"],
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
                f"Документ зарегистрирован под номером {result.registration_number}; "
                "созданы неизменяемый снимок и системное подтверждение.",
            )
            return redirect("documents:detail", public_id=document.public_id)

    return render(
        request,
        "documents/register_confirm.html",
        {
            "document": document,
            "employee": employee,
            "confirmation_preview": registration_confirmation_preview(employee, document),
            "form": form,
        },
    )


@login_required
@require_POST
def document_link_create(request: HttpRequest, public_id) -> HttpResponse:
    employee = require_document_employee(request.user)
    document = _document_for_employee(public_id, employee)
    form = DocumentLinkForm(
        request.POST,
        employee=employee,
        source_document=document,
    )
    if form.is_valid():
        try:
            create_document_link(
                source_document=document,
                target_document=form.cleaned_data["target_document"],
                link_type=form.cleaned_data["link_type"],
                actor=employee,
            )
        except ValidationError as error:
            messages.error(request, _validation_message(error))
        else:
            messages.success(request, "Связь документов создана.")
    else:
        messages.error(request, "Не удалось создать связь документов.")
    return redirect("documents:detail", public_id=document.public_id)
