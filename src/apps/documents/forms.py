from __future__ import annotations

from typing import Any

from django import forms

from apps.equipment.models import EquipmentAsset
from apps.equipment.services import equipment_label
from apps.organizations.models import Employee

from .models import Document, DocumentLink, DocumentType


class EquipmentMultipleChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj: EquipmentAsset) -> str:
        return equipment_label(obj)


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
    equipment_assets = EquipmentMultipleChoiceField(
        label="Оборудование документа",
        queryset=EquipmentAsset.objects.none(),
        required=False,
        help_text=(
            "Выбранные объекты будут зафиксированы вместе с действующими "
            "диспетчерскими наименованиями при регистрации."
        ),
        widget=forms.SelectMultiple(attrs={"size": 8}),
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
        self.fields["equipment_assets"].queryset = (
            EquipmentAsset.objects.filter(organization=employee.organization)
            .select_related("site", "equipment_type")
            .order_by("site__name", "code")
        )
        if document is not None:
            self.fields["document_type"].initial = document.document_type
            self.fields["document_type"].disabled = True
            if document.current_version_id:
                self.fields["equipment_assets"].initial = EquipmentAsset.objects.filter(
                    document_links__document_version_id=document.current_version_id
                ).order_by("code")


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
