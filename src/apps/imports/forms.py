from __future__ import annotations

from pathlib import Path

from django import forms

from .models import (
    DataProfile,
    ImportBatch,
    ImportRow,
    PowerSystemSourceRevision,
)
from .power_system import (
    MAX_POWER_SYSTEM_PACKAGE_SIZE,
    available_power_system_profiles,
)
from .services import (
    MAX_FILE_SIZE,
    available_data_profiles,
    registry_field_specs,
    suggest_column_mapping,
)


class DataProfileChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj: DataProfile) -> str:
        suffix = " · профиль по умолчанию" if obj.is_default else ""
        return f"{obj.name} · {obj.get_export_policy_display()}{suffix}"


class ImportUploadForm(forms.Form):
    data_profile = DataProfileChoiceField(
        label="Профиль данных",
        queryset=DataProfile.objects.none(),
        required=False,
        help_text=(
            "Презентационный профиль безопасен для показа. Локальный проверочный "
            "профиль не предназначен для обычного экспорта."
        ),
    )
    target_registry = forms.ChoiceField(
        label="Назначение импорта",
        choices=ImportBatch.TargetRegistry.choices,
    )
    source_reference = forms.CharField(
        label="Источник или основание",
        required=False,
        max_length=1000,
        help_text=(
            "Например: «Перечень объектов диспетчеризации Кочубеевской ВЭС» "
            "или реквизиты документа-основания."
        ),
    )
    source_file = forms.FileField(
        label="Файл",
        help_text="Поддерживаются CSV и XLSX размером до 10 МБ.",
        widget=forms.ClearableFileInput(attrs={"accept": ".csv,.xlsx"}),
    )

    def __init__(self, *args, organization, **kwargs):
        super().__init__(*args, **kwargs)
        profiles = available_data_profiles(organization)
        self.fields["data_profile"].queryset = DataProfile.objects.filter(
            pk__in=[profile.pk for profile in profiles]
        ).order_by("-is_default", "name")
        default_profile = next((profile for profile in profiles if profile.is_default), None)
        if default_profile is not None:
            self.fields["data_profile"].initial = default_profile

    def clean_source_file(self):
        uploaded = self.cleaned_data["source_file"]
        extension = Path(uploaded.name).suffix.lower()
        if extension not in {".csv", ".xlsx"}:
            raise forms.ValidationError("Допустимы только файлы CSV и XLSX.")
        if uploaded.size > MAX_FILE_SIZE:
            raise forms.ValidationError("Размер файла превышает 10 МБ.")
        if uploaded.size == 0:
            raise forms.ValidationError("Нельзя загрузить пустой файл.")
        return uploaded


class ImportColumnMappingForm(forms.Form):
    def __init__(self, *args, batch: ImportBatch, **kwargs):
        super().__init__(*args, **kwargs)
        self.batch = batch
        specs = registry_field_specs(batch.target_registry)
        choices = [("", "Не использовать эту колонку")] + [
            (spec.key, f"{spec.label}{' *' if spec.required else ''}")
            for spec in specs
        ]
        for column in batch.columns.order_by("position"):
            field_name = f"column_{column.position}"
            initial = column.mapped_key or suggest_column_mapping(
                batch.target_registry,
                column.normalized_name,
            )
            self.fields[field_name] = forms.ChoiceField(
                label=column.source_name or f"Колонка {column.position}",
                choices=choices,
                required=False,
                initial=initial,
                help_text=(
                    f"Нормализованный заголовок: {column.normalized_name}. "
                    f"Позиция в файле: {column.position}."
                ),
            )

    @property
    def mapping(self) -> dict[int, str]:
        return {
            int(name.removeprefix("column_")): value
            for name, value in self.cleaned_data.items()
            if name.startswith("column_")
        }


class ImportRowCorrectionForm(forms.Form):
    note = forms.CharField(
        label="Комментарий к решению",
        required=False,
        max_length=2000,
        widget=forms.Textarea(attrs={"rows": 3}),
    )

    def __init__(self, *args, row: ImportRow, **kwargs):
        super().__init__(*args, **kwargs)
        self.row = row
        initial_values = row.decision_values or row.mapped_values
        fields: dict[str, forms.Field] = {}
        for spec in registry_field_specs(row.batch.target_registry):
            initial = initial_values.get(spec.key, "")
            if spec.kind == "choice":
                choices = list(spec.choices)
                if not spec.required:
                    choices.insert(0, ("", "Не указано"))
                field: forms.Field = forms.ChoiceField(
                    label=spec.label,
                    choices=choices,
                    required=spec.required,
                    initial=initial,
                )
            elif spec.kind == "boolean":
                boolean_choices = [("", "Не указано"), ("Да", "Да"), ("Нет", "Нет")]
                field = forms.ChoiceField(
                    label=spec.label,
                    choices=boolean_choices,
                    required=spec.required,
                    initial=initial,
                )
            else:
                field = forms.CharField(
                    label=spec.label,
                    required=spec.required,
                    max_length=spec.max_length,
                    initial=initial,
                    help_text=(
                        "Допустимо ГГГГ-ММ-ДД или ДД.ММ.ГГГГ."
                        if spec.kind == "date"
                        else ""
                    ),
                )
            fields[spec.key] = field

        note = self.fields.pop("note")
        self.fields = {**fields, "note": note}
        if not self.is_bound:
            self.initial["note"] = row.decision_note

    @property
    def corrected_values(self) -> dict[str, str]:
        return {
            key: str(value or "")
            for key, value in self.cleaned_data.items()
            if key != "note"
        }



class ImportPublicationConfirmationForm(forms.Form):
    preview_digest = forms.CharField(widget=forms.HiddenInput())
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
            "Я проверил(а) итог публикации и подтверждаю создание записей "
            "в рабочем справочнике от своего имени"
        )
    )


class PowerSystemPackageUploadForm(forms.Form):
    data_profile = DataProfileChoiceField(
        label="Профиль данных",
        queryset=DataProfile.objects.none(),
        required=False,
    )
    source_reference = forms.CharField(
        label="Источник или основание",
        max_length=1000,
        help_text="Например: перечень объектов диспетчеризации и реквизиты редакции.",
    )
    source_approval_status = forms.ChoiceField(
        label="Статус исходной редакции",
        choices=PowerSystemSourceRevision.SourceApprovalStatus.choices,
        initial=PowerSystemSourceRevision.SourceApprovalStatus.UNKNOWN,
    )
    effective_from = forms.DateField(
        label="Дата начала действия",
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
        help_text="Оставьте пустым, если дата редакции не подтверждена.",
    )
    source_file = forms.FileField(
        label="Контролируемый ZIP-пакет",
        help_text=(
            "Пакет должен содержать аналитический MD и пять CSV установленной структуры. "
            "Рабочие справочники при загрузке не изменяются."
        ),
        widget=forms.ClearableFileInput(attrs={"accept": ".zip"}),
    )

    def __init__(self, *args, organization, **kwargs):
        super().__init__(*args, **kwargs)
        profiles = available_power_system_profiles(organization)
        self.fields["data_profile"].queryset = DataProfile.objects.filter(
            pk__in=[profile.pk for profile in profiles]
        ).order_by("-is_default", "name")
        default_profile = next((profile for profile in profiles if profile.is_default), None)
        if default_profile is not None:
            self.fields["data_profile"].initial = default_profile

    def clean_source_file(self):
        uploaded = self.cleaned_data["source_file"]
        if Path(uploaded.name).suffix.lower() != ".zip":
            raise forms.ValidationError("Для предметного импорта требуется ZIP-пакет.")
        if uploaded.size == 0:
            raise forms.ValidationError("Нельзя загрузить пустой ZIP-пакет.")
        if uploaded.size > MAX_POWER_SYSTEM_PACKAGE_SIZE:
            raise forms.ValidationError("Размер ZIP-пакета превышает 25 МБ.")
        return uploaded


class PowerSystemOccurrenceDecisionForm(forms.Form):
    action = forms.ChoiceField(
        label="Решение",
        choices=(
            ("ACCEPT_AS_NEW", "Принять как отдельный объект"),
            ("MERGE_WITH", "Объединить с другой строкой"),
            ("EXCLUDE", "Исключить из публикации"),
            ("RESET", "Сбросить ручное решение"),
        ),
    )
    merge_target_occurrence_id = forms.CharField(
        label="occurrence_id целевой строки",
        max_length=128,
        required=False,
    )
    note = forms.CharField(
        label="Комментарий",
        max_length=2000,
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
    )

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("action") == "MERGE_WITH" and not cleaned.get(
            "merge_target_occurrence_id"
        ):
            self.add_error(
                "merge_target_occurrence_id",
                "Для объединения укажите occurrence_id целевой строки.",
            )
        return cleaned


class PowerSystemPublicationConfirmationForm(forms.Form):
    effective_from = forms.DateField(
        label="Дата начала действия публикуемой редакции",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    preview_digest = forms.CharField(widget=forms.HiddenInput())
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
            "Я проверил(а) готовые строки и подтверждаю их контролируемую "
            "публикацию от своего имени"
        )
    )
