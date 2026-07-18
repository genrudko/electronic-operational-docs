from django import forms
from django.core.exceptions import ValidationError

from apps.organizations.models import InterfacePreference

from .editor import (
    EDITOR_SCHEMA_VERSION,
    normalize_editor_document,
)


class JournalDisplayPreferenceForm(forms.ModelForm):
    class Meta:
        model = InterfacePreference
        fields = (
            "journal_heading_mode",
            "journal_width",
            "journal_font_family",
            "journal_font_size",
            "journal_time_font_size",
            "journal_date_font_size",
            "journal_table_header_font_size",
            "journal_title_font_size",
            "journal_density",
            "journal_show_authors",
            "journal_show_links",
        )
        widgets = {
            "journal_heading_mode": forms.RadioSelect(),
            "journal_width": forms.Select(),
            "journal_font_family": forms.Select(),
            "journal_font_size": forms.Select(),
            "journal_time_font_size": forms.Select(),
            "journal_date_font_size": forms.Select(),
            "journal_table_header_font_size": forms.Select(),
            "journal_title_font_size": forms.Select(),
            "journal_density": forms.Select(),
            "journal_show_authors": forms.CheckboxInput(),
            "journal_show_links": forms.CheckboxInput(),
        }
        labels = {
            "journal_heading_mode": "Шапка журнала",
            "journal_width": "Ширина журнала",
            "journal_font_family": "Шрифт записей",
            "journal_font_size": "Текст записей",
            "journal_time_font_size": "Время записи",
            "journal_date_font_size": "Заголовки дат",
            "journal_table_header_font_size": "Шапка таблицы",
            "journal_title_font_size": "Заголовок журнала",
            "journal_density": "Плотность строк",
            "journal_show_authors": "Показывать автора каждой записи",
            "journal_show_links": (
                "Показывать связи с оборудованием и документами"
            ),
        }
        help_texts = {
            "journal_heading_mode": (
                "Полная шапка всегда используется при печати."
            ),
            "journal_show_authors": (
                "Настройка влияет только на рабочий экран."
            ),
            "journal_show_links": (
                "Настройка влияет только на рабочий экран."
            ),
        }


class ShiftOpenForm(forms.Form):
    planned_start_at = forms.DateTimeField(
        label="Плановое начало",
        input_formats=("%Y-%m-%dT%H:%M",),
        widget=forms.DateTimeInput(
            format="%Y-%m-%dT%H:%M",
            attrs={"type": "datetime-local"},
        ),
    )
    planned_end_at = forms.DateTimeField(
        label="Плановое окончание",
        input_formats=("%Y-%m-%dT%H:%M",),
        widget=forms.DateTimeInput(
            format="%Y-%m-%dT%H:%M",
            attrs={"type": "datetime-local"},
        ),
    )

    def clean(self) -> dict[str, object]:
        cleaned = super().clean()
        start_at = cleaned.get("planned_start_at")
        end_at = cleaned.get("planned_end_at")
        if start_at and end_at and end_at <= start_at:
            self.add_error(
                "planned_end_at",
                "Окончание смены должно быть позже её начала.",
            )
        return cleaned


class DraftEntryAutoSaveForm(forms.Form):
    public_id = forms.UUIDField()
    expected_version = forms.IntegerField(min_value=1)
    event_at = forms.DateTimeField(
        input_formats=(
            "%Y-%m-%dT%H:%M",
            "%Y-%m-%dT%H:%M:%S",
        )
    )
    content = forms.CharField(
        required=False,
        max_length=20000,
        widget=forms.Textarea(),
    )
    editor_schema_version = forms.CharField(
        required=False,
        max_length=64,
    )
    editor_payload = forms.JSONField(required=False)

    def clean_editor_payload(self):
        value = self.cleaned_data.get("editor_payload")
        if value in (None, "", {}):
            return None
        try:
            return normalize_editor_document(value)
        except ValidationError as error:
            raise ValidationError(error.messages) from error

    def clean_editor_schema_version(self) -> str:
        value = (
            self.cleaned_data.get("editor_schema_version")
            or EDITOR_SCHEMA_VERSION
        )
        if value != EDITOR_SCHEMA_VERSION:
            raise ValidationError(
                "Неизвестная версия структуры редактора."
            )
        return value
