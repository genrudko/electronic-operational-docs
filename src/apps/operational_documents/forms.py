from __future__ import annotations

from typing import Any

from django import forms
from django.forms import BaseFormSet, formset_factory

from apps.documents.models import Document
from apps.equipment.models import EquipmentAsset
from apps.organizations.models import Employee, Workplace

from .journal_forms import APPROVED_JOURNAL_FORM_CODES
from .models import (
    FieldType,
    OperationalDocumentRecord,
    OperationalDocumentType,
    OperationalDocumentTypeRevision,
    SchemaPublicationStatus,
)


class OperationalDocumentTypeForm(forms.Form):
    code = forms.SlugField(
        label="Системный код",
        max_length=64,
        help_text="Латинские буквы, цифры, дефис или подчёркивание.",
    )
    name = forms.CharField(label="Наименование", max_length=255)
    short_name = forms.CharField(label="Краткое наименование", max_length=120, required=False)
    description = forms.CharField(
        label="Назначение",
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
    )
    number_prefix = forms.CharField(
        label="Префикс номера",
        max_length=24,
        help_text="Например: ЗАП, РСП, ДЕФ.",
    )
    number_width = forms.IntegerField(
        label="Разрядность порядкового номера",
        min_value=1,
        max_value=12,
        initial=4,
    )
    requires_workplace = forms.BooleanField(
        label="Для записи обязательно рабочее место",
        required=False,
        initial=True,
    )

    def clean_code(self) -> str:
        return self.cleaned_data["code"].strip().lower()

    def clean_number_prefix(self) -> str:
        value = self.cleaned_data["number_prefix"].strip().upper()
        if not value:
            raise forms.ValidationError("Префикс обязателен.")
        return value


class OperationalFieldDefinitionForm(forms.Form):
    label = forms.CharField(label="Наименование поля", max_length=255, required=False)
    code = forms.CharField(
        label="Код поля",
        max_length=64,
        help_text="Технический идентификатор поля.",
        required=False,
    )
    field_type = forms.ChoiceField(label="Тип значения", choices=FieldType.choices)
    required = forms.BooleanField(label="Обязательное", required=False)
    show_in_list = forms.BooleanField(label="Показывать в общем реестре", required=False)
    searchable = forms.BooleanField(label="Учитывать в поиске", required=False)
    choice_options = forms.CharField(
        label="Варианты выбора",
        required=False,
        help_text="Только для поля «Выбор»: варианты через точку с запятой.",
        widget=forms.TextInput(attrs={"placeholder": "Низкий; Средний; Высокий"}),
    )
    help_text = forms.CharField(label="Подсказка", max_length=500, required=False)

    def clean_code(self) -> str:
        return str(self.cleaned_data.get("code") or "").strip().upper()

    def clean(self) -> dict[str, Any]:
        cleaned = super().clean()
        label = str(cleaned.get("label") or "").strip()
        code = str(cleaned.get("code") or "").strip().upper()
        options = str(cleaned.get("choice_options") or "").strip()
        help_text = str(cleaned.get("help_text") or "").strip()
        meaningful = bool(
            label
            or code
            or options
            or help_text
            or cleaned.get("required")
            or cleaned.get("show_in_list")
            or cleaned.get("searchable")
        )
        cleaned["_empty_definition"] = not meaningful
        if not meaningful:
            return cleaned
        if not label:
            self.add_error("label", "Укажите наименование поля.")
        if not code:
            self.add_error("code", "Укажите код поля.")
        field_type = cleaned.get("field_type")
        if field_type == FieldType.CHOICE and not options:
            self.add_error("choice_options", "Укажите хотя бы один вариант.")
        if field_type != FieldType.CHOICE and options:
            self.add_error("choice_options", "Варианты допустимы только для поля «Выбор».")
        return cleaned


class OperationalFieldDefinitionBaseFormSet(BaseFormSet):
    def clean(self) -> None:
        super().clean()
        if any(self.errors):
            return
        codes: set[str] = set()
        visible_count = 0
        active_count = 0
        for form in self.forms:
            if not hasattr(form, "cleaned_data") or not form.cleaned_data:
                continue
            if form.cleaned_data.get("DELETE") or form.cleaned_data.get("_empty_definition"):
                continue
            active_count += 1
            code = form.cleaned_data["code"]
            if code in codes:
                raise forms.ValidationError(f"Код поля {code} указан более одного раза.")
            codes.add(code)
            visible_count += int(bool(form.cleaned_data.get("show_in_list")))
        if active_count < 1:
            raise forms.ValidationError("Добавьте хотя бы одно предметное поле.")
        if visible_count > 4:
            raise forms.ValidationError("В общем реестре можно показывать не более четырёх полей.")


OperationalFieldDefinitionFormSet = formset_factory(
    OperationalFieldDefinitionForm,
    formset=OperationalFieldDefinitionBaseFormSet,
    extra=1,
    min_num=1,
    max_num=12,
    validate_min=True,
    validate_max=True,
    can_delete=True,
)


def field_definitions_from_formset(formset: BaseFormSet) -> list[dict[str, Any]]:
    definitions: list[dict[str, Any]] = []
    for form in formset.forms:
        if (
            not form.cleaned_data
            or form.cleaned_data.get("DELETE")
            or form.cleaned_data.get("_empty_definition")
        ):
            continue
        options = [
            item.strip()
            for item in str(form.cleaned_data.get("choice_options") or "").split(";")
            if item.strip()
        ]
        definitions.append(
            {
                "code": form.cleaned_data["code"],
                "label": form.cleaned_data["label"].strip(),
                "type": form.cleaned_data["field_type"],
                "required": bool(form.cleaned_data.get("required")),
                "show_in_list": bool(form.cleaned_data.get("show_in_list")),
                "searchable": bool(form.cleaned_data.get("searchable")),
                "help_text": str(form.cleaned_data.get("help_text") or "").strip(),
                "choices": [{"value": item, "label": item} for item in options],
            }
        )
    return definitions


class OperationalDocumentTypeChoiceForm(forms.Form):
    document_type = forms.ModelChoiceField(
        label="Тип оперативного документа",
        queryset=OperationalDocumentType.objects.none(),
        empty_label="Выберите тип документа",
    )

    def __init__(self, *args: Any, employee: Employee, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.fields["document_type"].queryset = (
            OperationalDocumentType.objects.filter(
                organization=employee.organization,
                is_active=True,
                revisions__status=SchemaPublicationStatus.PUBLISHED,
                code__in=APPROVED_JOURNAL_FORM_CODES,
            )
            .distinct()
            .order_by("name")
        )


class OperationalDocumentRecordForm(forms.Form):
    title = forms.CharField(
        label="Заголовок",
        max_length=500,
        widget=forms.TextInput(attrs={"placeholder": "Кратко сформулируйте содержание записи"}),
    )
    summary = forms.CharField(
        label="Краткое содержание",
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
    )
    event_at = forms.DateTimeField(
        label="Дата и время события",
        input_formats=("%Y-%m-%dT%H:%M", "%Y-%m-%dT%H:%M:%S"),
        widget=forms.DateTimeInput(
            format="%Y-%m-%dT%H:%M",
            attrs={"type": "datetime-local"},
        ),
    )
    workplace = forms.ModelChoiceField(
        label="Рабочее место",
        queryset=Workplace.objects.none(),
        required=False,
        empty_label="Не выбрано",
    )
    equipment_assets = forms.ModelMultipleChoiceField(
        label="Оборудование",
        queryset=EquipmentAsset.objects.none(),
        required=False,
        widget=forms.SelectMultiple(attrs={"size": 8, "class": "opdoc-multi-select"}),
    )
    related_documents = forms.ModelMultipleChoiceField(
        label="Документы-основания",
        queryset=Document.objects.none(),
        required=False,
        widget=forms.SelectMultiple(attrs={"size": 6, "class": "opdoc-multi-select"}),
    )
    related_records = forms.ModelMultipleChoiceField(
        label="Связанные оперативные записи",
        queryset=OperationalDocumentRecord.objects.none(),
        required=False,
        widget=forms.SelectMultiple(attrs={"size": 6, "class": "opdoc-multi-select"}),
    )
    change_comment = forms.CharField(
        label="Комментарий к изменению",
        required=False,
        widget=forms.Textarea(attrs={"rows": 2}),
    )

    def __init__(
        self,
        *args: Any,
        employee: Employee,
        revision: OperationalDocumentTypeRevision,
        record: OperationalDocumentRecord | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.employee = employee
        self.revision = revision
        self.record = record
        organization = employee.organization
        self.fields["workplace"].queryset = Workplace.objects.filter(
            organization=organization,
            is_active=True,
        ).order_by("name")
        self.fields["workplace"].required = revision.requires_workplace
        self.fields["equipment_assets"].queryset = (
            EquipmentAsset.objects.filter(organization=organization)
            .select_related("site", "equipment_type")
            .order_by("site__name", "code")
        )
        self.fields["related_documents"].queryset = Document.objects.filter(
            organization=organization,
            status=Document.Status.REGISTERED,
        ).order_by("-registered_at", "-pk")
        related_records = OperationalDocumentRecord.objects.filter(
            organization=organization,
        ).order_by("-event_at", "-pk")
        if record is not None:
            related_records = related_records.exclude(pk=record.pk)
        self.fields["related_records"].queryset = related_records
        if record is None:
            self.fields.pop("change_comment")
        self.dynamic_field_names: dict[str, str] = {}
        self.participant_field_names: dict[str, str] = {}
        self._add_dynamic_fields()
        self._add_participant_fields()
        if record is not None and not self.is_bound:
            self._set_record_initial(record)

    def _add_dynamic_fields(self) -> None:
        for definition in self.revision.field_definitions:
            code = str(definition["code"])
            name = f"field__{code}"
            self.dynamic_field_names[code] = name
            common = {
                "label": str(definition["label"]),
                "required": bool(definition.get("required")),
                "help_text": str(definition.get("help_text") or ""),
            }
            field_type = str(definition["type"])
            if field_type == FieldType.TEXT:
                field = forms.CharField(max_length=1000, **common)
            elif field_type == FieldType.LONG_TEXT:
                field = forms.CharField(widget=forms.Textarea(attrs={"rows": 5}), **common)
            elif field_type == FieldType.INTEGER:
                field = forms.IntegerField(**common)
            elif field_type == FieldType.DECIMAL:
                field = forms.DecimalField(max_digits=20, decimal_places=6, **common)
            elif field_type == FieldType.BOOLEAN:
                field = forms.TypedChoiceField(
                    choices=(("", "Не указано"), ("1", "Да"), ("0", "Нет")),
                    coerce=lambda value: value == "1",
                    empty_value=None,
                    **common,
                )
            elif field_type == FieldType.DATE:
                field = forms.DateField(
                    input_formats=("%Y-%m-%d",),
                    widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
                    **common,
                )
            elif field_type == FieldType.DATETIME:
                field = forms.DateTimeField(
                    input_formats=("%Y-%m-%dT%H:%M", "%Y-%m-%dT%H:%M:%S"),
                    widget=forms.DateTimeInput(
                        format="%Y-%m-%dT%H:%M",
                        attrs={"type": "datetime-local"},
                    ),
                    **common,
                )
            elif field_type == FieldType.CHOICE:
                choices = [("", "Не выбрано")]
                choices.extend(
                    (str(item["value"]), str(item["label"]))
                    for item in definition.get("choices", [])
                )
                field = forms.ChoiceField(choices=choices, **common)
            else:
                raise ValueError(f"Неизвестный тип поля {field_type}")
            self.fields[name] = field

    def _add_participant_fields(self) -> None:
        queryset = Employee.objects.filter(
            organization=self.employee.organization,
            is_active=True,
        ).select_related("position", "division", "workplace").order_by(
            "last_name", "first_name", "middle_name"
        )
        for role in self.revision.participant_role_definitions:
            code = str(role["code"])
            name = f"participant__{code}"
            self.participant_field_names[code] = name
            if role.get("multiple"):
                field: forms.Field = forms.ModelMultipleChoiceField(
                    label=str(role["name"]),
                    queryset=queryset,
                    required=bool(role.get("required")),
                    widget=forms.SelectMultiple(attrs={"size": 6, "class": "opdoc-multi-select"}),
                )
            else:
                field = forms.ModelChoiceField(
                    label=str(role["name"]),
                    queryset=queryset,
                    required=bool(role.get("required")),
                    empty_label="Не назначен",
                )
            self.fields[name] = field

    def _set_record_initial(self, record: OperationalDocumentRecord) -> None:
        self.initial.update(
            {
                "title": record.title,
                "summary": record.summary,
                "event_at": record.event_at,
                "workplace": record.workplace,
                "equipment_assets": list(
                    record.equipment_links.values_list("equipment_id", flat=True)
                ),
                "related_documents": list(
                    record.document_links.values_list("document_id", flat=True)
                ),
                "related_records": list(
                    record.outgoing_relations.values_list("target_record_id", flat=True)
                ),
            }
        )
        for code, name in self.dynamic_field_names.items():
            self.initial[name] = record.field_values.get(code, {}).get("value")
        participants: dict[str, list[int]] = {}
        for item in record.participants.all():
            participants.setdefault(item.role_code, []).append(item.employee_id)
        role_map = {
            str(item["code"]): item for item in self.revision.participant_role_definitions
        }
        for code, name in self.participant_field_names.items():
            employee_ids = participants.get(code, [])
            self.initial[name] = employee_ids if role_map[code].get("multiple") else (
                employee_ids[0] if employee_ids else None
            )

    def field_values_payload(self) -> dict[str, Any]:
        return {
            code: self.cleaned_data.get(name)
            for code, name in self.dynamic_field_names.items()
        }

    def participant_map(self) -> dict[str, list[Employee]]:
        result: dict[str, list[Employee]] = {}
        for role in self.revision.participant_role_definitions:
            code = str(role["code"])
            value = self.cleaned_data.get(self.participant_field_names[code])
            if role.get("multiple"):
                result[code] = list(value or [])
            else:
                result[code] = [value] if value is not None else []
        return result

    def bound_fields(self, names: tuple[str, ...] | list[str]):
        return [self[name] for name in names if name in self.fields]

    @property
    def main_fields(self):
        return self.bound_fields(("title", "event_at", "workplace", "summary"))

    @property
    def subject_fields(self):
        return self.bound_fields(list(self.dynamic_field_names.values()))

    @property
    def participant_fields(self):
        return self.bound_fields(list(self.participant_field_names.values()))

    @property
    def relation_fields(self):
        return self.bound_fields(
            ("equipment_assets", "related_documents", "related_records")
        )

    @property
    def change_fields(self):
        return self.bound_fields(("change_comment",))


class OperationalDocumentTransitionForm(forms.Form):
    transition_code = forms.CharField(widget=forms.HiddenInput())
    comment = forms.CharField(
        label="Комментарий",
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
    )
