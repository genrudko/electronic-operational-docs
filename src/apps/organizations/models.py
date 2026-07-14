from __future__ import annotations

from datetime import date

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q
from django.utils import timezone


def _validate_window(start: date, end: date | None, field: str = "valid_until") -> None:
    if end is not None and end < start:
        raise ValidationError({field: "Дата окончания не может быть раньше даты начала."})


class Organization(models.Model):
    code = models.CharField("Код", max_length=32, unique=True)
    name = models.CharField("Наименование", max_length=255)
    short_name = models.CharField("Краткое наименование", max_length=120, blank=True)
    is_active = models.BooleanField("Действующая", default=True)
    created_at = models.DateTimeField("Создана", auto_now_add=True)
    updated_at = models.DateTimeField("Изменена", auto_now=True)

    class Meta:
        ordering = ("name",)
        verbose_name = "организация"
        verbose_name_plural = "организации"

    def __str__(self) -> str:
        return self.short_name or self.name


class Division(models.Model):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="divisions",
        verbose_name="Организация",
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="children",
        verbose_name="Вышестоящее подразделение",
    )
    code = models.CharField("Код", max_length=32)
    name = models.CharField("Наименование", max_length=255)
    is_active = models.BooleanField("Действующее", default=True)

    class Meta:
        ordering = ("organization__name", "name")
        constraints = [
            models.UniqueConstraint(
                fields=("organization", "code"),
                name="uniq_division_code_per_organization",
            )
        ]
        verbose_name = "подразделение"
        verbose_name_plural = "подразделения"

    def __str__(self) -> str:
        return f"{self.organization}: {self.name}"

    def clean(self) -> None:
        super().clean()
        if self.parent_id and self.parent_id == self.pk:
            raise ValidationError({"parent": "Подразделение не может быть родителем само себе."})
        if self.parent_id and self.parent.organization_id != self.organization_id:
            raise ValidationError({"parent": "Родительское подразделение относится к другой организации."})


class Workplace(models.Model):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="workplaces",
        verbose_name="Организация",
    )
    division = models.ForeignKey(
        Division,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="workplaces",
        verbose_name="Подразделение",
    )
    code = models.CharField("Код", max_length=32)
    name = models.CharField("Наименование", max_length=255)
    is_active = models.BooleanField("Действующее", default=True)

    class Meta:
        ordering = ("organization__name", "name")
        constraints = [
            models.UniqueConstraint(
                fields=("organization", "code"),
                name="uniq_workplace_code_per_organization",
            )
        ]
        verbose_name = "рабочее место"
        verbose_name_plural = "рабочие места"

    def __str__(self) -> str:
        return f"{self.organization}: {self.name}"

    def clean(self) -> None:
        super().clean()
        if self.division_id and self.division.organization_id != self.organization_id:
            raise ValidationError({"division": "Подразделение относится к другой организации."})


class OperationalArea(models.Model):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="operational_areas",
        verbose_name="Организация",
    )
    division = models.ForeignKey(
        Division,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="operational_areas",
        verbose_name="Подразделение",
    )
    code = models.CharField("Код", max_length=32)
    name = models.CharField("Наименование", max_length=255)
    workplaces = models.ManyToManyField(
        Workplace,
        blank=True,
        related_name="operational_areas",
        verbose_name="Рабочие места",
    )
    is_active = models.BooleanField("Действующая", default=True)

    class Meta:
        ordering = ("organization__name", "name")
        constraints = [
            models.UniqueConstraint(
                fields=("organization", "code"),
                name="uniq_area_code_per_organization",
            )
        ]
        verbose_name = "оперативная область"
        verbose_name_plural = "оперативные области"

    def __str__(self) -> str:
        return f"{self.organization}: {self.name}"

    def clean(self) -> None:
        super().clean()
        if self.division_id and self.division.organization_id != self.organization_id:
            raise ValidationError({"division": "Подразделение относится к другой организации."})


class Position(models.Model):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="positions",
        verbose_name="Организация",
    )
    code = models.CharField("Код", max_length=32)
    name = models.CharField("Наименование", max_length=255)
    is_operational = models.BooleanField("Оперативная должность", default=False)
    is_active = models.BooleanField("Действующая", default=True)

    class Meta:
        ordering = ("organization__name", "name")
        constraints = [
            models.UniqueConstraint(
                fields=("organization", "code"),
                name="uniq_position_code_per_organization",
            )
        ]
        verbose_name = "должность"
        verbose_name_plural = "должности"

    def __str__(self) -> str:
        return f"{self.organization}: {self.name}"


class Employee(models.Model):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="employees",
        verbose_name="Организация",
    )
    division = models.ForeignKey(
        Division,
        on_delete=models.PROTECT,
        related_name="employees",
        verbose_name="Подразделение",
    )
    position = models.ForeignKey(
        Position,
        on_delete=models.PROTECT,
        related_name="employees",
        verbose_name="Должность",
    )
    workplace = models.ForeignKey(
        Workplace,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="employees",
        verbose_name="Основное рабочее место",
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="employee_profile",
        verbose_name="Персональная учётная запись",
    )
    personnel_number = models.CharField("Табельный номер", max_length=64)
    last_name = models.CharField("Фамилия", max_length=150)
    first_name = models.CharField("Имя", max_length=150)
    middle_name = models.CharField("Отчество", max_length=150, blank=True)
    employment_start = models.DateField("Начало работы", default=timezone.localdate)
    employment_end = models.DateField("Окончание работы", null=True, blank=True)
    is_active = models.BooleanField("Действующий сотрудник", default=True)

    class Meta:
        ordering = ("last_name", "first_name", "middle_name")
        constraints = [
            models.UniqueConstraint(
                fields=("organization", "personnel_number"),
                name="uniq_employee_number_per_organization",
            ),
            models.CheckConstraint(
                condition=Q(employment_end__isnull=True) | Q(employment_end__gte=F("employment_start")),
                name="employee_valid_employment_window",
            ),
        ]
        verbose_name = "сотрудник"
        verbose_name_plural = "сотрудники"

    def __str__(self) -> str:
        return self.full_name

    @property
    def full_name(self) -> str:
        return " ".join(part for part in (self.last_name, self.first_name, self.middle_name) if part)

    def clean(self) -> None:
        super().clean()
        _validate_window(self.employment_start, self.employment_end, "employment_end")
        errors: dict[str, str] = {}
        if self.division_id and self.division.organization_id != self.organization_id:
            errors["division"] = "Подразделение относится к другой организации."
        if self.position_id and self.position.organization_id != self.organization_id:
            errors["position"] = "Должность относится к другой организации."
        if self.workplace_id and self.workplace.organization_id != self.organization_id:
            errors["workplace"] = "Рабочее место относится к другой организации."
        if errors:
            raise ValidationError(errors)


class Role(models.Model):
    code = models.SlugField("Код", max_length=64, unique=True)
    name = models.CharField("Наименование", max_length=255)
    description = models.TextField("Описание", blank=True)
    is_system = models.BooleanField("Системная роль", default=False)
    is_active = models.BooleanField("Действующая", default=True)

    class Meta:
        ordering = ("name",)
        verbose_name = "роль"
        verbose_name_plural = "роли"

    def __str__(self) -> str:
        return self.name


class ResponsibilityScope(models.Model):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="responsibility_scopes",
        verbose_name="Организация",
    )
    operational_area = models.ForeignKey(
        OperationalArea,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="responsibility_scopes",
        verbose_name="Оперативная область",
    )
    code = models.CharField("Код", max_length=64)
    name = models.CharField("Наименование", max_length=255)
    is_active = models.BooleanField("Действующая", default=True)

    class Meta:
        ordering = ("organization__name", "name")
        constraints = [
            models.UniqueConstraint(
                fields=("organization", "code"),
                name="uniq_scope_code_per_organization",
            )
        ]
        verbose_name = "область ответственности"
        verbose_name_plural = "области ответственности"

    def __str__(self) -> str:
        return f"{self.organization}: {self.name}"

    def clean(self) -> None:
        super().clean()
        if self.operational_area_id and self.operational_area.organization_id != self.organization_id:
            raise ValidationError(
                {"operational_area": "Оперативная область относится к другой организации."}
            )


class RoleAssignment(models.Model):
    employee = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        related_name="role_assignments",
        verbose_name="Сотрудник",
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.PROTECT,
        related_name="assignments",
        verbose_name="Роль",
    )
    scope = models.ForeignKey(
        ResponsibilityScope,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="role_assignments",
        verbose_name="Область ответственности",
    )
    valid_from = models.DateField("Действует с", default=timezone.localdate)
    valid_until = models.DateField("Действует по", null=True, blank=True)
    is_active = models.BooleanField("Действующее назначение", default=True)
    granted_at = models.DateTimeField("Назначено", auto_now_add=True)

    class Meta:
        ordering = ("employee__last_name", "role__name", "valid_from")
        constraints = [
            models.CheckConstraint(
                condition=Q(valid_until__isnull=True) | Q(valid_until__gte=F("valid_from")),
                name="role_assignment_valid_window",
            ),
            models.UniqueConstraint(
                fields=("employee", "role", "scope", "valid_from"),
                name="uniq_scoped_role_assignment_start",
            ),
            models.UniqueConstraint(
                fields=("employee", "role", "valid_from"),
                condition=Q(scope__isnull=True),
                name="uniq_global_role_assignment_start",
            ),
        ]
        verbose_name = "назначение роли"
        verbose_name_plural = "назначения ролей"

    def __str__(self) -> str:
        scope = f" · {self.scope}" if self.scope_id else ""
        return f"{self.employee}: {self.role}{scope}"

    def clean(self) -> None:
        super().clean()
        _validate_window(self.valid_from, self.valid_until)
        if self.scope_id and self.scope.organization_id != self.employee.organization_id:
            raise ValidationError({"scope": "Область ответственности относится к другой организации."})

    def is_effective_on(self, day: date | None = None) -> bool:
        current = day or timezone.localdate()
        return self.is_active and self.valid_from <= current and (
            self.valid_until is None or self.valid_until >= current
        )


class Substitution(models.Model):
    replaced_employee = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        related_name="substitutions_as_replaced",
        verbose_name="Замещаемый сотрудник",
    )
    substitute_employee = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        related_name="substitutions_as_substitute",
        verbose_name="Замещающий сотрудник",
    )
    scope = models.ForeignKey(
        ResponsibilityScope,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="substitutions",
        verbose_name="Ограничение области ответственности",
    )
    valid_from = models.DateField("Действует с")
    valid_until = models.DateField("Действует по")
    reason = models.CharField("Основание", max_length=500)
    is_active = models.BooleanField("Действующее замещение", default=True)
    created_at = models.DateTimeField("Создано", auto_now_add=True)

    class Meta:
        ordering = ("-valid_from", "replaced_employee__last_name")
        constraints = [
            models.CheckConstraint(
                condition=Q(valid_until__gte=F("valid_from")),
                name="substitution_valid_window",
            ),
            models.UniqueConstraint(
                fields=("replaced_employee", "substitute_employee", "scope", "valid_from"),
                name="uniq_substitution_start",
            ),
        ]
        verbose_name = "временное замещение"
        verbose_name_plural = "временные замещения"

    def __str__(self) -> str:
        return f"{self.substitute_employee} замещает {self.replaced_employee}"

    def clean(self) -> None:
        super().clean()
        _validate_window(self.valid_from, self.valid_until)
        errors: dict[str, str] = {}
        if self.replaced_employee_id == self.substitute_employee_id:
            errors["substitute_employee"] = "Сотрудник не может замещать сам себя."
        if (
            self.replaced_employee_id
            and self.substitute_employee_id
            and self.replaced_employee.organization_id != self.substitute_employee.organization_id
        ):
            errors["substitute_employee"] = "Сотрудники относятся к разным организациям."
        if self.scope_id and self.scope.organization_id != self.replaced_employee.organization_id:
            errors["scope"] = "Область ответственности относится к другой организации."
        if errors:
            raise ValidationError(errors)

    def is_effective_on(self, day: date | None = None) -> bool:
        current = day or timezone.localdate()
        return self.is_active and self.valid_from <= current <= self.valid_until


class AuthenticationEvent(models.Model):
    class EventType(models.TextChoices):
        LOGIN_SUCCESS = "LOGIN_SUCCESS", "Успешный вход"
        LOGIN_FAILURE = "LOGIN_FAILURE", "Неуспешный вход"
        LOGOUT = "LOGOUT", "Выход"

    event_type = models.CharField("Событие", max_length=32, choices=EventType.choices)
    occurred_at = models.DateTimeField("Время", auto_now_add=True, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="authentication_events",
        verbose_name="Учётная запись",
    )
    employee = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="authentication_events",
        verbose_name="Сотрудник",
    )
    username_snapshot = models.CharField("Имя пользователя", max_length=150, blank=True)
    ip_address = models.GenericIPAddressField("IP-адрес", null=True, blank=True)
    user_agent = models.CharField("User-Agent", max_length=512, blank=True)
    session_key = models.CharField("Ключ сессии", max_length=64, blank=True)

    class Meta:
        ordering = ("-occurred_at", "-pk")
        indexes = [models.Index(fields=("event_type", "occurred_at"))]
        verbose_name = "событие аутентификации"
        verbose_name_plural = "события аутентификации"

    def __str__(self) -> str:
        identity = self.username_snapshot or "неизвестная учётная запись"
        return f"{self.get_event_type_display()}: {identity}"
