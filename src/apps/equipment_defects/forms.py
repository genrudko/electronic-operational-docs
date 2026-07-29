from __future__ import annotations

from typing import Any

from django import forms
from django.utils import timezone

from apps.equipment.models import EquipmentAsset
from apps.operational_log.models import OperationalLogEntry
from apps.organizations.models import Employee, Workplace


class DateTimeLocalField(forms.DateTimeField):
    """Server-authoritative datetime input progressively enhanced in the browser."""

    def __init__(
        self,
        *args: Any,
        allow_server_now: bool = False,
        **kwargs: Any,
    ) -> None:
        kwargs.setdefault("input_formats", ("%Y-%m-%dT%H:%M", "%Y-%m-%dT%H:%M:%S"))
        widget = kwargs.pop("widget", None)
        if widget is None:
            attrs = {
                "type": "datetime-local",
                "step": "60",
                "autocomplete": "off",
                "class": "defect-datetime-native",
                "data-defect-datetime": "true",
            }
            if allow_server_now:
                attrs["data-allow-server-now"] = "true"
            widget = forms.DateTimeInput(format="%Y-%m-%dT%H:%M", attrs=attrs)
        kwargs["widget"] = widget
        super().__init__(*args, **kwargs)


class EquipmentTreeSelect(forms.Select):
    """Native select fallback enriched with equipment hierarchy metadata."""

    def __init__(self, attrs: dict[str, Any] | None = None) -> None:
        merged = {
            "data-defect-tree-select": "equipment",
            "data-tree-placeholder": "Введите код или название оборудования",
            "autocomplete": "off",
        }
        if attrs:
            merged.update(attrs)
        super().__init__(attrs=merged)

    def create_option(
        self,
        name: str,
        value: Any,
        label: str,
        selected: bool,
        index: int,
        subindex: int | None = None,
        attrs: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        option = super().create_option(
            name,
            value,
            label,
            selected,
            index,
            subindex=subindex,
            attrs=attrs,
        )
        instance = getattr(value, "instance", None)
        if instance is not None:
            option["attrs"].update(
                {
                    "data-tree-id": str(instance.pk),
                    "data-tree-parent": str(instance.parent_id or ""),
                    "data-tree-site-id": str(instance.site_id),
                    "data-tree-site": instance.site.short_name or instance.site.name,
                    "data-tree-type": instance.equipment_type.name,
                    "data-tree-code": instance.code,
                }
            )
        return option


class PersonnelTreeSelect(forms.Select):
    """Native select fallback enriched with division and position metadata."""

    def __init__(self, attrs: dict[str, Any] | None = None) -> None:
        merged = {
            "data-defect-tree-select": "personnel",
            "data-tree-placeholder": "Введите Ф.И.О. или должность",
            "autocomplete": "off",
        }
        if attrs:
            merged.update(attrs)
        super().__init__(attrs=merged)

    def create_option(
        self,
        name: str,
        value: Any,
        label: str,
        selected: bool,
        index: int,
        subindex: int | None = None,
        attrs: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        option = super().create_option(
            name,
            value,
            label,
            selected,
            index,
            subindex=subindex,
            attrs=attrs,
        )
        instance = getattr(value, "instance", None)
        if instance is not None:
            option["attrs"].update(
                {
                    "data-tree-id": str(instance.pk),
                    "data-tree-division-id": str(instance.division_id),
                    "data-tree-division-parent": str(instance.division.parent_id or ""),
                    "data-tree-division": instance.division.name,
                    "data-tree-position-id": str(instance.position_id),
                    "data-tree-position": instance.position.name,
                    "data-tree-workplace": (
                        instance.workplace.name if instance.workplace_id else ""
                    ),
                }
            )
        return option


class EquipmentChoiceField(forms.ModelChoiceField):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs.setdefault("widget", EquipmentTreeSelect())
        super().__init__(*args, **kwargs)

    def label_from_instance(self, obj: EquipmentAsset) -> str:
        return f"{obj.code} · {obj.technical_name}"


class PersonnelChoiceField(forms.ModelChoiceField):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs.setdefault("widget", PersonnelTreeSelect())
        super().__init__(*args, **kwargs)

    def label_from_instance(self, obj: Employee) -> str:
        return f"{obj.full_name} · {obj.position.name}"


class OperationalLogEntryChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj: OperationalLogEntry) -> str:
        event_at = timezone.localtime(obj.event_at)
        content = " ".join(obj.content.split())
        if len(content) > 110:
            content = f"{content[:107]}…"
        return f"Запись № {obj.sequence_number} · {event_at:%d.%m.%Y %H:%M} · {content}"


class DefectRegistrationForm(forms.Form):
    detected_at = DateTimeLocalField(
        label="Дата и время обнаружения",
        allow_server_now=True,
    )
    workplace = forms.ModelChoiceField(
        label="ВЭС / ПС и рабочее место",
        queryset=Workplace.objects.none(),
        empty_label="Выберите рабочее место",
    )
    equipment = EquipmentChoiceField(
        label="ЛЭП, оборудование или устройство",
        queryset=EquipmentAsset.objects.none(),
        empty_label="Выберите оборудование",
    )
    defect_description = forms.CharField(
        label="Содержание дефекта",
        widget=forms.Textarea(
            attrs={
                "rows": 5,
                "placeholder": "Кратко и однозначно опишите выявленную неисправность",
            }
        ),
    )
    discovered_by = PersonnelChoiceField(
        label="Лицо, обнаружившее дефект",
        queryset=Employee.objects.none(),
        empty_label="Выберите сотрудника",
        help_text=(
            "Обнаруживший дефект может отличаться от оперативного работника, "
            "который регистрирует запись."
        ),
    )
    operational_log_entry = OperationalLogEntryChoiceField(
        label="Связанная запись оперативного журнала",
        queryset=OperationalLogEntry.objects.none(),
        required=False,
        empty_label="Не связывать с оперативным журналом",
        help_text=(
            "Основной сценарий — создать дефект непосредственно из записи оперативного "
            "журнала. Ручная привязка нужна только для уже существующей записи."
        ),
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
            .select_related("site", "equipment_type", "parent")
            .order_by("site__name", "parent_id", "code")
        )
        self.fields["discovered_by"].queryset = (
            Employee.objects.filter(organization=organization, is_active=True)
            .select_related("position", "division", "workplace")
            .order_by(
                "division__name",
                "position__name",
                "last_name",
                "first_name",
                "middle_name",
            )
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
                f"Связь установлена автоматически с записью № {source_entry.sequence_number}."
            )


class DeadlineConfirmationForm(forms.Form):
    elimination_deadline = DateTimeLocalField(label="Срок устранения")
    responsible = PersonnelChoiceField(
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
            .select_related("position", "division", "workplace")
            .order_by(
                "division__name",
                "position__name",
                "last_name",
                "first_name",
                "middle_name",
            )
        )


class DeadlineExtensionForm(forms.Form):
    new_deadline = DateTimeLocalField(label="Новый срок устранения")
    reason = forms.CharField(
        label="Причина или комментарий",
        widget=forms.Textarea(attrs={"rows": 3}),
    )


class ResolutionConfirmationForm(forms.Form):
    resolved_at = DateTimeLocalField(
        label="Дата и время устранения",
        allow_server_now=True,
    )
    responsible = PersonnelChoiceField(
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
            .select_related("position", "division", "workplace")
            .order_by(
                "division__name",
                "position__name",
                "last_name",
                "first_name",
                "middle_name",
            )
        )
        if not self.is_bound:
            self.initial.setdefault(
                "resolved_at",
                timezone.localtime().replace(second=0, microsecond=0),
            )
