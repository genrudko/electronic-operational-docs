from __future__ import annotations

from datetime import date
from typing import Any

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from apps.documents.models import Document
from apps.equipment.models import EquipmentAsset
from apps.organizations.models import Employee, Organization


def validate_window(start: date, end: date | None, field: str = "effective_until") -> None:
    if end is not None and end < start:
        raise ValidationError({field: "Дата окончания не может быть раньше даты начала."})


def windows_overlap(
    first_start: date,
    first_end: date | None,
    second_start: date,
    second_end: date | None,
) -> bool:
    return first_start <= (second_end or date.max) and second_start <= (first_end or date.max)


class ProtectedQuerySet(models.QuerySet):
    def update(self, **kwargs: Any) -> int:
        raise ValidationError("Массовое изменение диспетчерского реестра запрещено.")

    def delete(self) -> tuple[int, dict[str, int]]:
        raise ValidationError("Физическое удаление диспетчерского реестра запрещено.")


ProtectedManager = models.Manager.from_queryset(ProtectedQuerySet)


class PublicationStatus(models.TextChoices):
    DRAFT = "DRAFT", "Черновик"
    PUBLISHED = "PUBLISHED", "Опубликовано"


class DispatchLevel(models.Model):
    class LevelType(models.TextChoices):
        DISPATCH = "DISPATCH", "Диспетчерский уровень"
        TECHNOLOGICAL = "TECHNOLOGICAL", "Технологический уровень"

    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="dispatch_levels",
        verbose_name="Организация",
    )
    code = models.SlugField("Системный код", max_length=96)
    name = models.CharField("Наименование уровня", max_length=500)
    level_type = models.CharField("Тип уровня", max_length=24, choices=LevelType.choices)
    rank = models.PositiveIntegerField(
        "Порядок уровня",
        default=100,
        help_text="Меньшее число означает более высокий уровень.",
    )
    description = models.TextField("Описание", blank=True)
    is_active = models.BooleanField("Используется", default=True)
    created_at = models.DateTimeField("Создан", auto_now_add=True)

    objects = ProtectedManager()

    class Meta:
        ordering = ("organization__name", "rank", "name")
        constraints = [
            models.UniqueConstraint(
                fields=("organization", "code"),
                name="uniq_dispatch_level_code_per_org",
            )
        ]
        verbose_name = "уровень управления или ведения"
        verbose_name_plural = "уровни управления и ведения"

    def __str__(self) -> str:
        return self.name

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.code = self.code.strip().lower()
        if self.pk:
            original = type(self).objects.get(pk=self.pk)
            if self._is_used_by_published_revision():
                protected = ("organization_id", "code", "name", "level_type", "rank")
                if any(getattr(original, field) != getattr(self, field) for field in protected):
                    raise ValidationError("Уровень, используемый опубликованной редакцией, неизменяем.")
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        raise ValidationError("Физическое удаление уровня запрещено.")

    def _is_used_by_published_revision(self) -> bool:
        management_used = self.management_revisions.filter(status=PublicationStatus.PUBLISHED).exists()
        supervision_used = self.supervision_revisions.filter(status=PublicationStatus.PUBLISHED).exists()
        return management_used or supervision_used

    @property
    def presentation_label(self) -> str:
        """Безопасная подпись UI без изменения опубликованного справочника."""
        if self.organization.code != "DEMO":
            return self.name
        return {
            "regional-dispatch": "Региональный диспетчерский уровень",
            "station-operational": "Оперативно-технологический уровень Кочубеевской ВЭС",
        }.get(self.code, self.name)


class DispatchSubject(models.Model):
    class SubjectType(models.TextChoices):
        INTERNAL = "INTERNAL", "Субъект организации"
        HIGHER = "HIGHER", "Вышестоящий субъект"
        ADJACENT = "ADJACENT", "Смежный субъект"
        OTHER = "OTHER", "Другой субъект"

    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="dispatch_subjects",
        verbose_name="Организация-владелец реестра",
    )
    code = models.SlugField("Системный код", max_length=96)
    name = models.CharField("Полное наименование", max_length=1000)
    short_name = models.CharField("Краткое наименование", max_length=255, blank=True)
    subject_type = models.CharField("Вид субъекта", max_length=24, choices=SubjectType.choices)
    is_external = models.BooleanField("Внешний субъект", default=False)
    description = models.TextField("Описание", blank=True)
    is_active = models.BooleanField("Используется", default=True)
    created_at = models.DateTimeField("Создан", auto_now_add=True)

    objects = ProtectedManager()

    class Meta:
        ordering = ("organization__name", "subject_type", "name")
        constraints = [
            models.UniqueConstraint(
                fields=("organization", "code"),
                name="uniq_dispatch_subject_code_per_org",
            )
        ]
        verbose_name = "субъект управления или ведения"
        verbose_name_plural = "субъекты управления и ведения"

    def __str__(self) -> str:
        return self.short_name or self.name

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.code = self.code.strip().lower()
        if self.subject_type in {self.SubjectType.HIGHER, self.SubjectType.ADJACENT}:
            self.is_external = True
        if self.pk:
            original = type(self).objects.get(pk=self.pk)
            if self._is_used_by_published_revision():
                protected = (
                    "organization_id",
                    "code",
                    "name",
                    "short_name",
                    "subject_type",
                    "is_external",
                )
                if any(getattr(original, field) != getattr(self, field) for field in protected):
                    raise ValidationError("Субъект, используемый опубликованной редакцией, неизменяем.")
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        raise ValidationError("Физическое удаление субъекта запрещено.")

    def _is_used_by_published_revision(self) -> bool:
        return (
            self.management_revisions.filter(status=PublicationStatus.PUBLISHED).exists()
            or self.supervision_revisions.filter(status=PublicationStatus.PUBLISHED).exists()
            or self.outgoing_adjacent_relations.filter(revisions__status=PublicationStatus.PUBLISHED).exists()
            or self.incoming_adjacent_relations.filter(revisions__status=PublicationStatus.PUBLISHED).exists()
        )

    @property
    def presentation_label(self) -> str:
        """Безопасная подпись UI без изменения опубликованного справочника."""
        stored_label = self.short_name or self.name
        if self.organization.code != "DEMO":
            return stored_label
        return {
            "demo-station-shift": "Смена Кочубеевской ВЭС",
            "demo-regional-center": "Региональный ДЦ",
            "demo-adjacent-center": "Смежный ДЦ ПС 330 кВ",
        }.get(self.code, stored_label)


class ManagementObject(models.Model):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="management_objects",
        verbose_name="Организация",
    )
    equipment = models.OneToOneField(
        EquipmentAsset,
        on_delete=models.PROTECT,
        related_name="management_object",
        verbose_name="Оборудование — объект управления",
    )
    notes = models.TextField("Примечание", blank=True)
    is_active = models.BooleanField("Используется", default=True)
    created_at = models.DateTimeField("Создан", auto_now_add=True)

    objects = ProtectedManager()

    class Meta:
        ordering = ("organization__name", "equipment__code")
        verbose_name = "объект управления"
        verbose_name_plural = "объекты управления"

    def __str__(self) -> str:
        return f"Объект управления: {self.equipment}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.pk and self.revisions.filter(status=PublicationStatus.PUBLISHED).exists():
            original = type(self).objects.get(pk=self.pk)
            if original.organization_id != self.organization_id or original.equipment_id != self.equipment_id:
                raise ValidationError("Оборудование опубликованного объекта управления неизменяемо.")
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        raise ValidationError("Физическое удаление объекта управления запрещено.")

    def clean(self) -> None:
        super().clean()
        if self.equipment_id and self.organization_id:
            if self.equipment.organization_id != self.organization_id:
                raise ValidationError({"equipment": "Оборудование относится к другой организации."})


class SupervisionObject(models.Model):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="supervision_objects",
        verbose_name="Организация",
    )
    equipment = models.OneToOneField(
        EquipmentAsset,
        on_delete=models.PROTECT,
        related_name="supervision_object",
        verbose_name="Оборудование — объект ведения",
    )
    notes = models.TextField("Примечание", blank=True)
    is_active = models.BooleanField("Используется", default=True)
    created_at = models.DateTimeField("Создан", auto_now_add=True)

    objects = ProtectedManager()

    class Meta:
        ordering = ("organization__name", "equipment__code")
        verbose_name = "объект ведения"
        verbose_name_plural = "объекты ведения"

    def __str__(self) -> str:
        return f"Объект ведения: {self.equipment}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.pk and self.revisions.filter(status=PublicationStatus.PUBLISHED).exists():
            original = type(self).objects.get(pk=self.pk)
            if original.organization_id != self.organization_id or original.equipment_id != self.equipment_id:
                raise ValidationError("Оборудование опубликованного объекта ведения неизменяемо.")
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        raise ValidationError("Физическое удаление объекта ведения запрещено.")

    def clean(self) -> None:
        super().clean()
        if self.equipment_id and self.organization_id:
            if self.equipment.organization_id != self.organization_id:
                raise ValidationError({"equipment": "Оборудование относится к другой организации."})


class ManagementRevision(models.Model):
    management_object = models.ForeignKey(
        ManagementObject,
        on_delete=models.PROTECT,
        related_name="revisions",
        verbose_name="Объект управления",
    )
    revision_number = models.PositiveIntegerField("Номер редакции")
    level = models.ForeignKey(
        DispatchLevel,
        on_delete=models.PROTECT,
        related_name="management_revisions",
        verbose_name="Уровень управления",
    )
    subject = models.ForeignKey(
        DispatchSubject,
        on_delete=models.PROTECT,
        related_name="management_revisions",
        verbose_name="Управляющий субъект",
    )
    effective_from = models.DateField("Действует с")
    effective_until = models.DateField("Действует по", null=True, blank=True)
    basis_document = models.ForeignKey(
        Document,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="management_basis_revisions",
        verbose_name="Документ-основание в системе",
    )
    basis_reference = models.CharField("Реквизиты документа-основания", max_length=1000)
    change_summary = models.TextField("Содержание изменения", blank=True)
    status = models.CharField(
        "Статус публикации",
        max_length=16,
        choices=PublicationStatus.choices,
        default=PublicationStatus.DRAFT,
        db_index=True,
    )
    published_at = models.DateTimeField("Опубликовано", null=True, blank=True, editable=False)
    published_by = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="published_management_revisions",
        verbose_name="Опубликовал",
    )
    digest = models.CharField("SHA-256 редакции управления", max_length=64, blank=True, editable=False)
    created_at = models.DateTimeField("Создано", auto_now_add=True)

    objects = ProtectedManager()

    class Meta:
        ordering = ("management_object", "-effective_from", "-revision_number")
        constraints = [
            models.UniqueConstraint(
                fields=("management_object", "revision_number"),
                name="uniq_management_revision_number",
            ),
            models.CheckConstraint(
                condition=(
                    Q(
                        status="DRAFT",
                        published_at__isnull=True,
                        published_by__isnull=True,
                        digest="",
                    )
                    | (
                        Q(
                            status="PUBLISHED",
                            published_at__isnull=False,
                            published_by__isnull=False,
                        )
                        & ~Q(digest="")
                    )
                ),
                name="management_publication_consistent",
            ),
        ]
        indexes = [
            models.Index(fields=("management_object", "level", "status", "effective_from")),
        ]
        verbose_name = "редакция управления"
        verbose_name_plural = "редакции управления"

    def __str__(self) -> str:
        return f"{self.management_object.equipment} · управление № {self.revision_number}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.pk:
            original = type(self).objects.get(pk=self.pk)
            if original.status == PublicationStatus.PUBLISHED:
                raise ValidationError("Опубликованная редакция управления неизменяема.")
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        raise ValidationError("Физическое удаление редакции управления запрещено.")

    def clean(self) -> None:
        super().clean()
        validate_window(self.effective_from, self.effective_until)
        errors: dict[str, str] = {}
        organization_id = self.management_object.organization_id if self.management_object_id else None
        if organization_id and self.level_id and self.level.organization_id != organization_id:
            errors["level"] = "Уровень относится к другой организации."
        if organization_id and self.subject_id and self.subject.organization_id != organization_id:
            errors["subject"] = "Субъект относится к другой организации."
        if organization_id and self.basis_document_id:
            if self.basis_document.organization_id != organization_id:
                errors["basis_document"] = "Документ-основание относится к другой организации."
        if organization_id and self.published_by_id:
            if self.published_by.organization_id != organization_id:
                errors["published_by"] = "Публикующий сотрудник относится к другой организации."
        if not self.basis_reference.strip():
            errors["basis_reference"] = "Реквизиты документа-основания обязательны."
        if self.status == PublicationStatus.PUBLISHED:
            if not self.published_at or not self.published_by_id or len(self.digest) != 64:
                errors["status"] = "Опубликованная редакция требует автора, времени и SHA-256."
            if self.management_object_id and self.level_id:
                conflicts = (
                    type(self)
                    .objects.filter(
                        management_object=self.management_object,
                        level=self.level,
                        status=PublicationStatus.PUBLISHED,
                        effective_from__lte=self.effective_until or date.max,
                    )
                    .filter(Q(effective_until__isnull=True) | Q(effective_until__gte=self.effective_from))
                )
                if self.pk:
                    conflicts = conflicts.exclude(pk=self.pk)
                if conflicts.exists():
                    errors["effective_from"] = (
                        "На этом уровне уже действует управляющий субъект для данного объекта."
                    )
        if errors:
            raise ValidationError(errors)


class SupervisionRevision(models.Model):
    supervision_object = models.ForeignKey(
        SupervisionObject,
        on_delete=models.PROTECT,
        related_name="revisions",
        verbose_name="Объект ведения",
    )
    revision_number = models.PositiveIntegerField("Номер редакции")
    level = models.ForeignKey(
        DispatchLevel,
        on_delete=models.PROTECT,
        related_name="supervision_revisions",
        verbose_name="Уровень ведения",
    )
    subject = models.ForeignKey(
        DispatchSubject,
        on_delete=models.PROTECT,
        related_name="supervision_revisions",
        verbose_name="Субъект ведения",
    )
    is_information_only = models.BooleanField(
        "Информационное ведение",
        default=False,
        help_text="Субъект получает сведения, но не осуществляет оперативное ведение режима.",
    )
    effective_from = models.DateField("Действует с")
    effective_until = models.DateField("Действует по", null=True, blank=True)
    basis_document = models.ForeignKey(
        Document,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="supervision_basis_revisions",
        verbose_name="Документ-основание в системе",
    )
    basis_reference = models.CharField("Реквизиты документа-основания", max_length=1000)
    change_summary = models.TextField("Содержание изменения", blank=True)
    status = models.CharField(
        "Статус публикации",
        max_length=16,
        choices=PublicationStatus.choices,
        default=PublicationStatus.DRAFT,
        db_index=True,
    )
    published_at = models.DateTimeField("Опубликовано", null=True, blank=True, editable=False)
    published_by = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="published_supervision_revisions",
        verbose_name="Опубликовал",
    )
    digest = models.CharField("SHA-256 редакции ведения", max_length=64, blank=True, editable=False)
    created_at = models.DateTimeField("Создано", auto_now_add=True)

    objects = ProtectedManager()

    class Meta:
        ordering = ("supervision_object", "-effective_from", "-revision_number")
        constraints = [
            models.UniqueConstraint(
                fields=("supervision_object", "revision_number"),
                name="uniq_supervision_revision_number",
            ),
            models.CheckConstraint(
                condition=(
                    Q(
                        status="DRAFT",
                        published_at__isnull=True,
                        published_by__isnull=True,
                        digest="",
                    )
                    | (
                        Q(
                            status="PUBLISHED",
                            published_at__isnull=False,
                            published_by__isnull=False,
                        )
                        & ~Q(digest="")
                    )
                ),
                name="supervision_publication_consistent",
            ),
        ]
        indexes = [
            models.Index(fields=("supervision_object", "level", "status", "effective_from")),
        ]
        verbose_name = "редакция ведения"
        verbose_name_plural = "редакции ведения"

    def __str__(self) -> str:
        label = "информационное ведение" if self.is_information_only else "ведение"
        return f"{self.supervision_object.equipment} · {label} № {self.revision_number}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.pk:
            original = type(self).objects.get(pk=self.pk)
            if original.status == PublicationStatus.PUBLISHED:
                raise ValidationError("Опубликованная редакция ведения неизменяема.")
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        raise ValidationError("Физическое удаление редакции ведения запрещено.")

    def clean(self) -> None:
        super().clean()
        validate_window(self.effective_from, self.effective_until)
        errors: dict[str, str] = {}
        organization_id = self.supervision_object.organization_id if self.supervision_object_id else None
        if organization_id and self.level_id and self.level.organization_id != organization_id:
            errors["level"] = "Уровень относится к другой организации."
        if organization_id and self.subject_id and self.subject.organization_id != organization_id:
            errors["subject"] = "Субъект относится к другой организации."
        if organization_id and self.basis_document_id:
            if self.basis_document.organization_id != organization_id:
                errors["basis_document"] = "Документ-основание относится к другой организации."
        if organization_id and self.published_by_id:
            if self.published_by.organization_id != organization_id:
                errors["published_by"] = "Публикующий сотрудник относится к другой организации."
        if not self.basis_reference.strip():
            errors["basis_reference"] = "Реквизиты документа-основания обязательны."
        if self.status == PublicationStatus.PUBLISHED:
            if not self.published_at or not self.published_by_id or len(self.digest) != 64:
                errors["status"] = "Опубликованная редакция требует автора, времени и SHA-256."
        if errors:
            raise ValidationError(errors)


class AdjacentSubjectRelation(models.Model):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="adjacent_subject_relations",
        verbose_name="Организация",
    )
    code = models.SlugField("Системный код", max_length=96)
    source_subject = models.ForeignKey(
        DispatchSubject,
        on_delete=models.PROTECT,
        related_name="outgoing_adjacent_relations",
        verbose_name="Первый субъект",
    )
    target_subject = models.ForeignKey(
        DispatchSubject,
        on_delete=models.PROTECT,
        related_name="incoming_adjacent_relations",
        verbose_name="Смежный субъект",
    )
    is_active = models.BooleanField("Используется", default=True)
    created_at = models.DateTimeField("Создано", auto_now_add=True)

    objects = ProtectedManager()

    class Meta:
        ordering = ("organization__name", "code")
        constraints = [
            models.UniqueConstraint(
                fields=("organization", "code"),
                name="uniq_adjacent_relation_code_per_org",
            ),
            models.UniqueConstraint(
                fields=("organization", "source_subject", "target_subject"),
                name="uniq_directed_adjacent_subject_relation",
            ),
            models.CheckConstraint(
                condition=~Q(source_subject=models.F("target_subject")),
                name="adjacent_subjects_must_differ",
            ),
        ]
        verbose_name = "взаимодействие смежных субъектов"
        verbose_name_plural = "взаимодействия смежных субъектов"

    def __str__(self) -> str:
        return f"{self.source_subject} ↔ {self.target_subject}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.code = self.code.strip().lower()
        if self.pk and self.revisions.filter(status=PublicationStatus.PUBLISHED).exists():
            original = type(self).objects.get(pk=self.pk)
            protected = ("organization_id", "code", "source_subject_id", "target_subject_id")
            if any(getattr(original, field) != getattr(self, field) for field in protected):
                raise ValidationError("Опубликованная связь смежных субъектов неизменяема.")
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        raise ValidationError("Физическое удаление связи смежных субъектов запрещено.")

    def clean(self) -> None:
        super().clean()
        errors: dict[str, str] = {}
        if self.source_subject_id == self.target_subject_id and self.source_subject_id:
            errors["target_subject"] = "Субъект не может быть смежным сам себе."
        if self.organization_id and self.source_subject_id:
            if self.source_subject.organization_id != self.organization_id:
                errors["source_subject"] = "Первый субъект относится к другой организации."
        if self.organization_id and self.target_subject_id:
            if self.target_subject.organization_id != self.organization_id:
                errors["target_subject"] = "Смежный субъект относится к другой организации."
        if errors:
            raise ValidationError(errors)


class AdjacentSubjectRelationRevision(models.Model):
    relation = models.ForeignKey(
        AdjacentSubjectRelation,
        on_delete=models.PROTECT,
        related_name="revisions",
        verbose_name="Связь смежных субъектов",
    )
    revision_number = models.PositiveIntegerField("Номер редакции")
    effective_from = models.DateField("Действует с")
    effective_until = models.DateField("Действует по", null=True, blank=True)
    interaction_scope = models.TextField("Область взаимодействия")
    communication_rules = models.TextField("Правила взаимодействия")
    basis_document = models.ForeignKey(
        Document,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="adjacent_relation_basis_revisions",
        verbose_name="Документ-основание в системе",
    )
    basis_reference = models.CharField("Реквизиты документа-основания", max_length=1000)
    change_summary = models.TextField("Содержание изменения", blank=True)
    status = models.CharField(
        "Статус публикации",
        max_length=16,
        choices=PublicationStatus.choices,
        default=PublicationStatus.DRAFT,
        db_index=True,
    )
    published_at = models.DateTimeField("Опубликовано", null=True, blank=True, editable=False)
    published_by = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="published_adjacent_relation_revisions",
        verbose_name="Опубликовал",
    )
    digest = models.CharField("SHA-256 редакции взаимодействия", max_length=64, blank=True, editable=False)
    created_at = models.DateTimeField("Создано", auto_now_add=True)

    objects = ProtectedManager()

    class Meta:
        ordering = ("relation", "-effective_from", "-revision_number")
        constraints = [
            models.UniqueConstraint(
                fields=("relation", "revision_number"),
                name="uniq_adjacent_relation_revision_number",
            ),
            models.CheckConstraint(
                condition=(
                    Q(
                        status="DRAFT",
                        published_at__isnull=True,
                        published_by__isnull=True,
                        digest="",
                    )
                    | (
                        Q(
                            status="PUBLISHED",
                            published_at__isnull=False,
                            published_by__isnull=False,
                        )
                        & ~Q(digest="")
                    )
                ),
                name="adjacent_relation_publication_consistent",
            ),
        ]
        verbose_name = "редакция взаимодействия смежных субъектов"
        verbose_name_plural = "редакции взаимодействия смежных субъектов"

    def __str__(self) -> str:
        return f"{self.relation} · редакция № {self.revision_number}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.pk:
            original = type(self).objects.get(pk=self.pk)
            if original.status == PublicationStatus.PUBLISHED:
                raise ValidationError("Опубликованная редакция взаимодействия неизменяема.")
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        raise ValidationError("Физическое удаление редакции взаимодействия запрещено.")

    def clean(self) -> None:
        super().clean()
        validate_window(self.effective_from, self.effective_until)
        errors: dict[str, str] = {}
        organization_id = self.relation.organization_id if self.relation_id else None
        if organization_id and self.basis_document_id:
            if self.basis_document.organization_id != organization_id:
                errors["basis_document"] = "Документ-основание относится к другой организации."
        if organization_id and self.published_by_id:
            if self.published_by.organization_id != organization_id:
                errors["published_by"] = "Публикующий сотрудник относится к другой организации."
        if not self.interaction_scope.strip():
            errors["interaction_scope"] = "Область взаимодействия обязательна."
        if not self.communication_rules.strip():
            errors["communication_rules"] = "Правила взаимодействия обязательны."
        if not self.basis_reference.strip():
            errors["basis_reference"] = "Реквизиты документа-основания обязательны."
        if self.status == PublicationStatus.PUBLISHED:
            if not self.published_at or not self.published_by_id or len(self.digest) != 64:
                errors["status"] = "Опубликованная редакция требует автора, времени и SHA-256."
        if errors:
            raise ValidationError(errors)


class DispatchingAuditEvent(models.Model):
    class EventType(models.TextChoices):
        MANAGEMENT_PUBLISHED = "MANAGEMENT_PUBLISHED", "Опубликовано управление"
        SUPERVISION_PUBLISHED = "SUPERVISION_PUBLISHED", "Опубликовано ведение"
        ADJACENCY_PUBLISHED = "ADJACENCY_PUBLISHED", "Опубликовано взаимодействие"

    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="dispatching_audit_events",
        verbose_name="Организация",
    )
    event_type = models.CharField("Событие", max_length=40, choices=EventType.choices)
    actor_employee = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        related_name="dispatching_audit_events",
        verbose_name="Сотрудник",
    )
    management_revision = models.ForeignKey(
        ManagementRevision,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="audit_events",
        verbose_name="Редакция управления",
    )
    supervision_revision = models.ForeignKey(
        SupervisionRevision,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="audit_events",
        verbose_name="Редакция ведения",
    )
    adjacent_revision = models.ForeignKey(
        AdjacentSubjectRelationRevision,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="audit_events",
        verbose_name="Редакция взаимодействия",
    )
    payload = models.JSONField("Данные события", default=dict, blank=True)
    created_at = models.DateTimeField("Зафиксировано", auto_now_add=True)

    objects = ProtectedManager()

    class Meta:
        ordering = ("-created_at", "-pk")
        verbose_name = "событие аудита управления и ведения"
        verbose_name_plural = "события аудита управления и ведения"

    def __str__(self) -> str:
        return f"{self.get_event_type_display()} · {self.created_at:%d.%m.%Y %H:%M:%S}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.pk:
            raise ValidationError("Событие аудита неизменяемо.")
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        raise ValidationError("Физическое удаление события аудита запрещено.")

    def clean(self) -> None:
        super().clean()
        if not isinstance(self.payload, dict):
            raise ValidationError({"payload": "Данные аудита должны быть JSON-объектом."})
        linked = sum(
            value is not None
            for value in (
                self.management_revision_id,
                self.supervision_revision_id,
                self.adjacent_revision_id,
            )
        )
        if linked != 1:
            raise ValidationError("Событие аудита должно ссылаться ровно на одну редакцию.")
