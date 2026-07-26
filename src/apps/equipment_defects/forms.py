from __future__ import annotations

from typing import Any

from django import forms
from django.utils import timezone

from apps.equipment.models import EquipmentAsset
from apps.operational_log.models import OperationalLogEntry
from apps.organizations.models import Employee, Workplace


class DateTimeLocalField(forms.DateTimeField):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs.setdefault("input_formats", ("%Y-%m-%dT%H:%M", "%Y-%m-%dT%H:%M:%S"))
        kwargs.setdefault(
            "widget",
            forms.DateTimeInput(
                format="%Y-%m-%dT%H:%M",
                attrs={"type": "datetime-local"},
            ),
        )
        super().__init__(*args, **kwargs)


class DefectRegistrationForm(forms.Form):
    detected_at = DateTimeLocalField(label="Дата и время обнаружения")
    workplace = forms.ModelChoiceField(
        label="ВЭС / ПС и рабочее место",
        queryset=Workplace.objects.none(),
        empty_label="Выберите рабочее место",
    )
    equipment = forms.ModelChoiceField(
        label="ЛЭП, оборудование или устройство",
        queryset=EquipmentAsset.objects.none(),
        empty_label="Выберите оборудование",
    )
    defect_description = forms.CharField(
        label="Содержание дефекта",
        widget=forms.Textarea(
            attrs={
                "rows": 5,
                "placeholder": "Опишите обнаруженный дефект или неисправность",
            }
        ),
    )
    discovered_by = forms.ModelChoiceField(
        label="Лицо, обнаружившее дефект",
        queryset=Employee.objects.none(),
        empty_label="Выберите сотрудника",
        help_text=(
            "Обнаруживший дефект может отличаться от оперативного работника, "
            "который регистрирует запись."
        ),
    )
    operational_log_entry = forms.ModelChoiceField(
        label="Основание в оперативном журнале",
        queryset=OperationalLogEntry.objects.none(),
        required=False,
        empty_label="Без связи с оперативным журналом",
    )

    def __init__(
        self,
        *args: Any,
        employee: Employee,
        source_entry: OperationalLogEntry | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        organization = employee.organization
        self.fields["workplace"].queryset = Workplace.objects.filter(
            organization=organization,
            is_active=True,
        ).order_by("name")
        self.fields["equipment"].queryset = (
            EquipmentAsset.objects.filter(organization=organization)
            .select_related("site", "equipment_type")
            .order_by("site__name", "code")
        )
        self.fields["discovered_by"].queryset = (
            Employee.objects.filter(organization=organization, is_active=True)
            .select_related("position", "division")
            .order_by("last_name", "first_name", "middle_name")
        )
        self.fields["operational_log_entry"].queryset = (
            OperationalLogEntry.objects.filter(journal__organization=organization)
            .select_related("journal", "journal__workplace")
            .order_by("-registered_at", "-pk")
        )
        if not self.is_bound:
            self.initial.setdefault(
                "detected_at",
                timezone.localtime().replace(second=0, microsecond=0),
            )
            if employee.workplace_id:
                self.initial.setdefault("workplace", employee.workplace)
        if source_entry is not None:
            self.initial["operational_log_entry"] = source_entry
            self.initial["detected_at"] = source_entry.event_at
            self.initial["workplace"] = source_entry.journal.workplace
            equipment_links = list(source_entry.equipment_links.select_related("equipment")[:2])
            if len(equipment_links) == 1:
                self.initial["equipment"] = equipment_links[0].equipment
            self.fields["operational_log_entry"].disabled = True
            self.fields["operational_log_entry"].help_text = (
                f"Запись № {source_entry.sequence_number}: {source_entry.content[:180]}"
            )


class DeadlineConfirmationForm(forms.Form):
    elimination_deadline = DateTimeLocalField(label="Срок устранения")
    responsible = forms.ModelChoiceField(
        label="Ответственный за эксплуатацию",
        queryset=Employee.objects.none(),
        empty_label="Выберите сотрудника",
    )

    def __init__(self, *args: Any, employee: Employee, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.fields["responsible"].queryset = (
            Employee.objects.filter(
                organization=employee.organization,
                is_active=True,
            )
            .select_related("position", "division")
            .order_by("last_name", "first_name", "middle_name")
        )


class DeadlineExtensionForm(forms.Form):
    new_deadline = DateTimeLocalField(label="Новый срок устранения")
    reason = forms.CharField(
        label="Причина или комментарий",
        widget=forms.Textarea(attrs={"rows": 3}),
    )


class ResolutionConfirmationForm(forms.Form):
    resolved_at = DateTimeLocalField(label="Дата и время устранения")
    responsible = forms.ModelChoiceField(
        label="Ответственный за устранение",
        queryset=Employee.objects.none(),
        empty_label="Выберите сотрудника",
    )
    work_summary = forms.CharField(
        label="Содержание выполненных работ",
        widget=forms.Textarea(attrs={"rows": 5}),
    )

    def __init__(self, *args: Any, employee: Employee, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.fields["responsible"].queryset = (
            Employee.objects.filter(
                organization=employee.organization,
                is_active=True,
            )
            .select_related("position", "division")
            .order_by("last_name", "first_name", "middle_name")
        )
        if not self.is_bound:
            self.initial.setdefault(
                "resolved_at",
                timezone.localtime().replace(second=0, microsecond=0),
            )
