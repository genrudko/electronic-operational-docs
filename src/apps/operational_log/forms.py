from django import forms

from apps.organizations.models import InterfacePreference


class JournalDisplayPreferenceForm(forms.ModelForm):
    class Meta:
        model = InterfacePreference
        fields = (
            "journal_heading_mode",
            "journal_width",
            "journal_font_family",
            "journal_font_size",
            "journal_density",
            "journal_show_authors",
            "journal_show_links",
        )
        widgets = {
            "journal_heading_mode": forms.RadioSelect(),
            "journal_width": forms.Select(),
            "journal_font_family": forms.Select(),
            "journal_font_size": forms.Select(),
            "journal_density": forms.Select(),
            "journal_show_authors": forms.CheckboxInput(),
            "journal_show_links": forms.CheckboxInput(),
        }
        labels = {
            "journal_heading_mode": "Шапка журнала",
            "journal_width": "Ширина журнала",
            "journal_font_family": "Шрифт записей",
            "journal_font_size": "Размер текста",
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
