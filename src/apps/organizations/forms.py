from __future__ import annotations

from django import forms
from django.contrib.auth.forms import AuthenticationForm

from .models import (
    Division,
    Employee,
    EmployeeOperationalRight,
    EmployeeQualification,
    InterfacePreference,
    Organization,
    Position,
    Workplace,
)
from .personnel_management_models import (
    EmployeeContactProfile,
    EmployeeSpecialQualification,
    ExternalOperationalContact,
    OrganizationOperationalProfile,
    PersonnelImportBatch,
)


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
            "font_scale": "Размер текста интерфейса",
            "content_width": "Ширина рабочей области системы",
            "show_technical_details": "Показывать технические реквизиты",
        }
        help_texts = {
            "show_technical_details": (
                "Включает внутренние коды, номера редакций, SHA-256 "
                "и диагностические сведения."
            ),
        }


class EmployeeCardForm(forms.ModelForm):
    change_reason = forms.CharField(
        label="Основание изменения",
        max_length=1000,
        widget=forms.Textarea(attrs={"rows": 2}),
        help_text=(
            "Укажите документ, заявку или рабочую причину изменения карточки."
        ),
    )

    class Meta:
        model = Employee
        fields = (
            "organization",
            "division",
            "position",
            "workplace",
            "personnel_number",
            "last_name",
            "first_name",
            "middle_name",
            "employment_start",
            "employment_end",
            "is_active",
        )
        widgets = {
            "employment_start": forms.DateInput(attrs={"type": "date"}),
            "employment_end": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        organization_id = None
        if self.is_bound:
            organization_id = self.data.get(self.add_prefix("organization"))
        elif self.instance and self.instance.pk:
            organization_id = self.instance.organization_id
        if organization_id:
            self.fields["division"].queryset = Division.objects.filter(
                organization_id=organization_id,
                is_active=True,
            ).order_by("name")
            self.fields["position"].queryset = Position.objects.filter(
                organization_id=organization_id,
                is_active=True,
            ).order_by("name")
            self.fields["workplace"].queryset = Workplace.objects.filter(
                organization_id=organization_id,
                is_active=True,
            ).order_by("name")
        else:
            self.fields["division"].queryset = Division.objects.none()
            self.fields["position"].queryset = Position.objects.none()
            self.fields["workplace"].queryset = Workplace.objects.none()
        self.fields["organization"].queryset = Organization.objects.filter(
            is_active=True,
        ).order_by("name")

    def clean(self):
        cleaned = super().clean()
        organization = cleaned.get("organization")
        for field_name in ("division", "position", "workplace"):
            value = cleaned.get(field_name)
            if (
                value
                and organization
                and value.organization_id != organization.id
            ):
                self.add_error(
                    field_name,
                    "Значение относится к другой организации.",
                )
        return cleaned


class EmployeeContactForm(forms.ModelForm):
    class Meta:
        model = EmployeeContactProfile
        fields = (
            "primary_phone",
            "operational_phone",
            "email",
            "availability_schedule",
            "is_round_the_clock",
            "note",
        )
        widgets = {"note": forms.Textarea(attrs={"rows": 3})}


class EmployeeQualificationForm(forms.ModelForm):
    change_reason = forms.CharField(
        label="Основание изменения",
        max_length=1000,
        widget=forms.Textarea(attrs={"rows": 2}),
    )

    class Meta:
        model = EmployeeQualification
        fields = (
            "personnel_category",
            "electrical_safety_group",
            "voltage_scope",
            "electrical_installation_scope",
            "valid_from",
            "valid_until",
            "is_active",
            "source_reference",
        )
        widgets = {
            "valid_from": forms.DateInput(attrs={"type": "date"}),
            "valid_until": forms.DateInput(attrs={"type": "date"}),
            "electrical_installation_scope": forms.Textarea(
                attrs={"rows": 3}
            ),
            "source_reference": forms.Textarea(attrs={"rows": 2}),
        }
        labels = {
            "electrical_safety_group": "Группа по электробезопасности",
            "voltage_scope": (
                "Класс напряжения для группы по электробезопасности"
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.source_file_sha256:
            self.instance.source_file_sha256 = "0" * 64
        if self.instance.source_row_number is None:
            self.instance.source_row_number = 0


class EmployeeSpecialQualificationForm(forms.ModelForm):
    change_reason = forms.CharField(
        label="Основание изменения",
        max_length=1000,
        widget=forms.Textarea(attrs={"rows": 2}),
    )

    class Meta:
        model = EmployeeSpecialQualification
        fields = (
            "kind",
            "level",
            "scope_text",
            "valid_from",
            "valid_until",
            "basis_reference",
            "is_active",
        )
        widgets = {
            "scope_text": forms.Textarea(attrs={"rows": 3}),
            "basis_reference": forms.Textarea(attrs={"rows": 2}),
            "valid_from": forms.DateInput(attrs={"type": "date"}),
            "valid_until": forms.DateInput(attrs={"type": "date"}),
        }


class EmployeeOperationalRightForm(forms.ModelForm):
    change_reason = forms.CharField(
        label="Основание изменения",
        max_length=1000,
        widget=forms.Textarea(attrs={"rows": 2}),
    )

    class Meta:
        model = EmployeeOperationalRight
        fields = (
            "right_definition",
            "source_marker",
            "qualifier",
            "scope_text",
            "valid_from",
            "valid_until",
            "source_reference",
            "is_active",
        )
        widgets = {
            "qualifier": forms.Textarea(attrs={"rows": 2}),
            "scope_text": forms.Textarea(attrs={"rows": 3}),
            "source_reference": forms.Textarea(attrs={"rows": 2}),
            "valid_from": forms.DateInput(attrs={"type": "date"}),
            "valid_until": forms.DateInput(attrs={"type": "date"}),
        }
        help_texts = {
            "source_marker": "+ — без условия; +1, +2, +3 — с условием.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.source_file_sha256:
            self.instance.source_file_sha256 = "0" * 64
        if self.instance.source_row_number is None:
            self.instance.source_row_number = 0


class ExternalOperationalContactForm(forms.ModelForm):
    change_reason = forms.CharField(
        label="Основание изменения",
        max_length=1000,
        widget=forms.Textarea(attrs={"rows": 2}),
    )

    class Meta:
        model = ExternalOperationalContact
        fields = (
            "host_organization",
            "relation_kind",
            "operational_scope",
            "authority_summary",
            "valid_from",
            "valid_until",
            "basis_reference",
            "is_active",
        )
        widgets = {
            "operational_scope": forms.Textarea(attrs={"rows": 3}),
            "authority_summary": forms.Textarea(attrs={"rows": 3}),
            "basis_reference": forms.Textarea(attrs={"rows": 2}),
            "valid_from": forms.DateInput(attrs={"type": "date"}),
            "valid_until": forms.DateInput(attrs={"type": "date"}),
        }


class OrganizationOperationalProfileForm(forms.ModelForm):
    class Meta:
        model = OrganizationOperationalProfile
        fields = ("relation_kind", "directory_scope", "is_active")
        widgets = {"directory_scope": forms.Textarea(attrs={"rows": 3})}


class PersonnelImportUploadForm(forms.ModelForm):
    workbook = forms.FileField(
        label="Файл Excel",
        help_text=(
            "Поддерживается XLSX. Сначала формируется предварительный просмотр."
        ),
        widget=forms.FileInput(attrs={"accept": ".xlsx"}),
    )

    class Meta:
        model = PersonnelImportBatch
        fields = (
            "target_organization",
            "source_organization",
            "import_kind",
            "source_reference",
            "effective_from",
        )
        widgets = {
            "source_reference": forms.Textarea(attrs={"rows": 2}),
            "effective_from": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.file_sha256:
            self.instance.file_sha256 = "0" * 64
        if not self.instance.uploaded_name:
            self.instance.uploaded_name = "pending.xlsx"

    def clean_workbook(self):
        workbook = self.cleaned_data["workbook"]
        if not workbook.name.lower().endswith(".xlsx"):
            raise forms.ValidationError("Требуется файл XLSX.")
        if workbook.size > 10 * 1024 * 1024:
            raise forms.ValidationError(
                "Размер файла не должен превышать 10 МБ."
            )
        return workbook

    def clean(self):
        cleaned = super().clean()
        if (
            cleaned.get("import_kind") == "EXTERNAL_DIRECTORY"
            and not cleaned.get("source_organization")
        ):
            self.add_error(
                "source_organization",
                "Для внешнего справочника требуется организация-источник.",
            )
        return cleaned


class DeactivationForm(forms.Form):
    reason = forms.CharField(
        label="Основание деактивации",
        max_length=1000,
        widget=forms.Textarea(attrs={"rows": 3}),
    )
