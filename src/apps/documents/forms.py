from __future__ import annotations

from typing import Any

from django import forms

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
