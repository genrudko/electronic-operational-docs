from django import forms
from django.contrib.auth.forms import AuthenticationForm


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
