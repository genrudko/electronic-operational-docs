from django import forms
from django.contrib.auth.forms import AuthenticationForm

from .models import InterfacePreference


class PersonalAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label="Персональное имя пользователя",
        widget=forms.TextInput(
            attrs={
                "autocomplete": "username",
                "autofocus": True,
                "placeholder": "например, operator.demo",
            }
        ),
    )
    password = forms.CharField(
        label="Пароль",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "autocomplete": "current-password",
                "placeholder": "Введите пароль",
            }
        ),
    )


class InterfacePreferenceForm(forms.ModelForm):
    class Meta:
        model = InterfacePreference
        fields = (
            "theme",
            "density",
            "font_scale",
            "content_width",
            "show_technical_details",
            "journal_heading_mode",
            "journal_font_family",
            "journal_font_size",
            "journal_density",
            "journal_width",
            "journal_show_authors",
            "journal_show_links",
        )
        widgets = {
            "theme": forms.Select(),
            "density": forms.Select(),
            "font_scale": forms.Select(),
            "content_width": forms.Select(),
            "show_technical_details": forms.CheckboxInput(),
            "journal_heading_mode": forms.Select(),
            "journal_font_family": forms.Select(),
            "journal_font_size": forms.Select(),
            "journal_density": forms.Select(),
            "journal_width": forms.Select(),
            "journal_show_authors": forms.CheckboxInput(),
            "journal_show_links": forms.CheckboxInput(),
        }
        labels = {
            "theme": "Цветовая схема",
            "density": "Плотность интерфейса",
            "font_scale": "Размер текста интерфейса",
            "content_width": "Ширина рабочей области системы",
            "show_technical_details": "Показывать технические реквизиты",
            "journal_heading_mode": "Режим шапки журнала",
            "journal_font_family": "Шрифт записей",
            "journal_font_size": "Размер текста записей",
            "journal_density": "Плотность строк журнала",
            "journal_width": "Ширина журнала",
            "journal_show_authors": "Показывать автора каждой записи",
            "journal_show_links": "Показывать связи с оборудованием и документами",
        }
        help_texts = {
            "show_technical_details": (
                "Включает внутренние коды, номера редакций, SHA-256 "
                "и диагностические сведения."
            ),
            "journal_heading_mode": "Полная шапка всегда сохраняется в печатной форме.",
            "journal_show_authors": (
                "Скрытие действует только на рабочем экране и не меняет архивные данные."
            ),
            "journal_show_links": "Скрытие действует только на рабочем экране.",
        }
