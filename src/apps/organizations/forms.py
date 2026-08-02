from __future__ import annotations

import hashlib

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


SOURCE_903N = (
    "Правила по охране труда при эксплуатации электроустановок, "
    "утверждённые приказом Минтруда России от 15.12.2020 № 903н"
)
CONDITION_FORM_DEFAULTS = {
    "+1": (
        "Условие по пункту 5.4 Правил по охране труда",
        "Право применяется в соответствии с пунктом 5.4 Правил по охране "
        "труда при эксплуатации электроустановок.",
        "пункт 5.4",
    ),
    "+2": (
        "Условие по пункту 5.13 Правил по охране труда",
        "Право применяется в соответствии с пунктом 5.13 Правил по охране "
        "труда при эксплуатации электроустановок.",
        "пункт 5.13",
    ),
}


def _catalog_code(prefix: str, organization: Organization, value: str) -> str:
    payload = f"{organization.code}|{value.strip().casefold()}"
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:10].upper()
    return f"{prefix}-{digest}"


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
    new_division_name = forms.CharField(
        label="Новое подразделение",
        max_length=500,
        required=False,
        help_text="Заполните, когда нужного подразделения ещё нет в списке.",
    )
    new_position_name = forms.CharField(
        label="Новая должность",
        max_length=500,
        required=False,
        help_text="Заполните, когда нужной должности ещё нет в списке.",
    )
    new_workplace_name = forms.CharField(
        label="Новое рабочее место",
        max_length=500,
        required=False,
        help_text="Необязательно. Создаётся внутри выбранного подразделения.",
    )
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
        help_texts = {
            "division": (
                "Выберите существующее подразделение или введите новое ниже."
            ),
            "position": (
                "Выберите существующую должность или введите новую ниже."
            ),
            "workplace": (
                "Выберите существующее рабочее место или введите новое ниже."
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["organization"].queryset = Organization.objects.filter(
            is_active=True,
        ).order_by("name")
        self.fields["division"].required = False
        self.fields["position"].required = False
        self.fields["workplace"].required = False

        organization_id = None
        if self.is_bound:
            organization_id = self.data.get(self.add_prefix("organization"))
        elif self.instance and self.instance.pk:
            organization_id = self.instance.organization_id
        else:
            demo = Organization.objects.filter(code="DEMO", is_active=True).first()
            if demo:
                organization_id = demo.id
                self.initial.setdefault("organization", demo)

        divisions = Division.objects.filter(is_active=True)
        positions = Position.objects.filter(is_active=True)
        workplaces = Workplace.objects.filter(is_active=True)
        if organization_id:
            divisions = divisions.filter(organization_id=organization_id)
            positions = positions.filter(organization_id=organization_id)
            workplaces = workplaces.filter(organization_id=organization_id)
        self.fields["division"].queryset = divisions.order_by(
            "organization__name",
            "name",
        )
        self.fields["position"].queryset = positions.order_by(
            "organization__name",
            "name",
        )
        self.fields["workplace"].queryset = workplaces.order_by(
            "organization__name",
            "name",
        )

    def _get_validation_exclusions(self):
        exclusions = super()._get_validation_exclusions()
        if self.data.get(self.add_prefix("new_division_name"), "").strip():
            exclusions.add("division")
        if self.data.get(self.add_prefix("new_position_name"), "").strip():
            exclusions.add("position")
        return exclusions

    def clean(self):
        cleaned = super().clean()
        organization = cleaned.get("organization")
        new_division = " ".join(cleaned.get("new_division_name", "").split())
        new_position = " ".join(cleaned.get("new_position_name", "").split())
        new_workplace = " ".join(cleaned.get("new_workplace_name", "").split())
        cleaned["new_division_name"] = new_division
        cleaned["new_position_name"] = new_position
        cleaned["new_workplace_name"] = new_workplace

        if not cleaned.get("division") and not new_division:
            self.add_error(
                "division",
                "Выберите существующее подразделение или введите новое.",
            )
        if not cleaned.get("position") and not new_position:
            self.add_error(
                "position",
                "Выберите существующую должность или введите новую.",
            )
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
        if new_workplace and not (cleaned.get("division") or new_division):
            self.add_error(
                "new_workplace_name",
                "Для нового рабочего места требуется подразделение.",
            )
        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        organization = self.cleaned_data["organization"]
        division = self.cleaned_data.get("division")
        position = self.cleaned_data.get("position")
        workplace = self.cleaned_data.get("workplace")

        new_division = self.cleaned_data.get("new_division_name", "")
        if new_division:
            division, _ = Division.objects.get_or_create(
                organization=organization,
                name__iexact=new_division,
                defaults={
                    "code": _catalog_code("DIV", organization, new_division),
                    "name": new_division,
                    "is_active": True,
                },
            )
        new_position = self.cleaned_data.get("new_position_name", "")
        if new_position:
            position, _ = Position.objects.get_or_create(
                organization=organization,
                name__iexact=new_position,
                defaults={
                    "code": _catalog_code("POS", organization, new_position),
                    "name": new_position,
                    "is_operational": any(
                        marker in new_position.casefold()
                        for marker in (
                            "оператив",
                            "диспетчер",
                            "дежурн",
                            "начальник смены",
                        )
                    ),
                    "is_active": True,
                },
            )
        new_workplace = self.cleaned_data.get("new_workplace_name", "")
        if new_workplace:
            workplace, _ = Workplace.objects.get_or_create(
                organization=organization,
                name__iexact=new_workplace,
                defaults={
                    "division": division,
                    "code": _catalog_code("WP", organization, new_workplace),
                    "name": new_workplace,
                    "is_active": True,
                },
            )

        instance.division = division
        instance.position = position
        instance.workplace = workplace
        if commit:
            instance.save()
            self.save_m2m()
        return instance


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
    condition_title = forms.CharField(
        label="Краткое название условия",
        max_length=500,
        required=False,
    )
    condition_description = forms.CharField(
        label="Точное содержание условия",
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
        help_text=(
            "Для +1 и +2 система подставляет пункты 5.4 и 5.13 приказа "
            "Минтруда № 903н. Для иного индекса текст обязателен."
        ),
    )
    condition_source_clause = forms.CharField(
        label="Пункт документа",
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "например, пункт 5.4"}),
    )
    condition_source_reference = forms.CharField(
        label="Источник условия",
        max_length=1000,
        required=False,
        widget=forms.Textarea(attrs={"rows": 2}),
    )
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
        labels = {
            "source_marker": "Отметка в матрице",
            "qualifier": "Краткое уточнение права",
        }
        help_texts = {
            "source_marker": (
                "+ — без условия; +1, +2 или иной индекс — с условием."
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.source_file_sha256:
            self.instance.source_file_sha256 = "0" * 64
        if self.instance.source_row_number is None:
            self.instance.source_row_number = 0

        detail = getattr(self.instance, "condition_detail", None)
        if detail:
            self.initial.update(
                {
                    "condition_title": detail.title,
                    "condition_description": detail.description,
                    "condition_source_clause": detail.source_clause,
                    "condition_source_reference": detail.source_reference,
                }
            )
            return
        marker = self.initial.get("source_marker", "")
        defaults = CONDITION_FORM_DEFAULTS.get(marker)
        if defaults:
            title, description, clause = defaults
            self.initial.setdefault("condition_title", title)
            self.initial.setdefault("condition_description", description)
            self.initial.setdefault("condition_source_clause", clause)
            self.initial.setdefault("condition_source_reference", SOURCE_903N)
        elif marker and marker != "+" and self.initial.get("qualifier"):
            self.initial.setdefault(
                "condition_title",
                f"Дополнительное условие {marker}",
            )
            self.initial.setdefault(
                "condition_description",
                self.initial["qualifier"],
            )
            self.initial.setdefault(
                "condition_source_reference",
                self.initial.get("source_reference", ""),
            )

    def clean(self):
        cleaned = super().clean()
        marker = " ".join(cleaned.get("source_marker", "").split())
        description = " ".join(
            cleaned.get("condition_description", "").split()
        )
        cleaned["condition_description"] = description
        if marker and marker != "+" and marker not in {"+1", "+2"}:
            if not description:
                self.add_error(
                    "condition_description",
                    "Для этого индекса требуется точный текст условия.",
                )
            if not cleaned.get("condition_source_reference", "").strip():
                self.add_error(
                    "condition_source_reference",
                    "Укажите документ, в котором установлено условие.",
                )
        return cleaned


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
