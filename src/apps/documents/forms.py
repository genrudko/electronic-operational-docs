from __future__ import annotations

from typing import Any

from django import forms

from apps.equipment.models import EquipmentAsset
from apps.equipment.services import equipment_selection_rows
from apps.organizations.models import Employee

from .models import Document, DocumentLink, DocumentType


class DocumentDraftForm(forms.Form):
    document_type = forms.ModelChoiceField(
        label="Тип документа",
        queryset=DocumentType.objects.none(),
    )
    title = forms.CharField(
        label="Заголовок",
        max_length=500,
        widget=forms.TextInput(attrs={"placeholder": "Краткий заголовок документа"}),
    )
    subject = forms.CharField(
        label="Тема",
        max_length=500,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Необязательная тема"}),
    )
    body = forms.CharField(
        label="Содержимое",
        widget=forms.Textarea(
            attrs={
                "rows": 12,
                "placeholder": "Введите содержимое черновика",
            }
        ),
    )
    equipment_assets = forms.ModelMultipleChoiceField(
        label="Оборудование документа",
        queryset=EquipmentAsset.objects.none(),
        required=False,
        help_text=(
            "Используйте поиск, категории и фильтры. В форму передаются только "
            "идентификаторы выбранного оборудования."
        ),
        widget=forms.MultipleHiddenInput(),
    )

    def __init__(
        self,
        *args: Any,
        employee: Employee,
        document: Document | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.document = document
        self.fields["document_type"].queryset = DocumentType.objects.filter(
            organization=employee.organization,
            is_active=True,
        )
        equipment_queryset = (
            EquipmentAsset.objects.filter(organization=employee.organization)
            .select_related("site", "equipment_type", "parent")
            .order_by("site__name", "code")
        )
        self.fields["equipment_assets"].queryset = equipment_queryset

        selected_ids: list[str] = []
        if self.is_bound:
            field_name = self.add_prefix("equipment_assets")
            if hasattr(self.data, "getlist"):
                submitted_values = self.data.getlist(field_name)
            else:
                raw_value = self.data.get(field_name, [])
                if isinstance(raw_value, (list, tuple, set)):
                    submitted_values = raw_value
                elif raw_value in (None, ""):
                    submitted_values = []
                else:
                    submitted_values = [raw_value]
            selected_ids = [
                str(value)
                for value in submitted_values
                if value not in (None, "")
            ]
        elif document is not None and document.current_version_id:
            selected_ids = [
                str(value)
                for value in EquipmentAsset.objects.filter(
                    document_links__document_version_id=document.current_version_id
                ).values_list("pk", flat=True)
            ]
            self.fields["equipment_assets"].initial = selected_ids

        selected_assets = equipment_queryset.filter(pk__in=selected_ids)
        self.selected_equipment_rows = equipment_selection_rows(selected_assets)

        if document is not None:
            self.fields["document_type"].initial = document.document_type
            self.fields["document_type"].disabled = True


class DocumentLinkForm(forms.Form):
    target_document = forms.ModelChoiceField(
        label="Связанный документ",
        queryset=Document.objects.none(),
    )
    link_type = forms.ChoiceField(
        label="Тип связи",
        choices=DocumentLink.LinkType.choices,
    )

    def __init__(
        self,
        *args: Any,
        employee: Employee,
        source_document: Document,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.fields["target_document"].queryset = (
            Document.objects.filter(
                organization=employee.organization,
                status=Document.Status.REGISTERED,
            )
            .exclude(pk=source_document.pk)
            .order_by("-registered_at", "-pk")
        )


class DocumentRegistrationConfirmationForm(forms.Form):
    password = forms.CharField(
        label="Текущий пароль",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "autocomplete": "current-password",
                "placeholder": "Введите пароль своей учётной записи",
            }
        ),
    )
    confirm = forms.BooleanField(
        label=(
            "Я проверил(а) отображённое содержимое и подтверждаю регистрацию "
            "этой версии от своего имени"
        )
    )
