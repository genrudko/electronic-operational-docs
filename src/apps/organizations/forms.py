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
        )
        widgets = {
            "theme": forms.Select(),
            "density": forms.Select(),
            "font_scale": forms.Select(),
            "content_width": forms.Select(),
            "show_technical_details": forms.CheckboxInput(),
        }
        labels = {
            "theme": "Цветовая схема",
            "density": "Плотность интерфейса",
            "font_scale": "Размер текста",
            "content_width": "Ширина рабочей области",
            "show_technical_details": "Показывать технические реквизиты",
        }
        help_texts = {
            "show_technical_details": (
                "Включает внутренние коды, номера редакций, SHA-256 и диагностические сведения."
            ),
        }
