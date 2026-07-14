from __future__ import annotations

import uuid
from datetime import date
from typing import Any

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone

from apps.organizations.models import Employee, Organization


def validate_window(start: date, end: date | None, field: str) -> None:
    if end is not None and end < start:
        raise ValidationError({field: "Дата окончания не может быть раньше даты начала."})


class RegistryQuerySet(models.QuerySet):
    def update(self, **kwargs: Any) -> int:
        raise ValidationError("Массовое изменение реестровых записей запрещено.")

    def delete(self) -> tuple[int, dict[str, int]]:
        raise ValidationError("Физическое удаление реестровых записей запрещено.")


RegistryManager = models.Manager.from_queryset(RegistryQuerySet)


class PublicationStatus(models.TextChoices):
    DRAFT = "DRAFT", "Черновик"
    PUBLISHED = "PUBLISHED", "Опубликовано"


class EnergySite(models.Model):
    class SiteType(models.TextChoices):
        WIND_POWER_PLANT = "WIND_POWER_PLANT", "Ветроэлектростанция"
        SUBSTATION = "SUBSTATION", "Подстанция"
        CONTROL_CENTER = "CONTROL_CENTER", "Диспетчерский или оперативный центр"
        OTHER = "OTHER", "Другой энергообъект"

    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="energy_sites",
        verbose_name="Организация",
    )
    code = models.SlugField("Системный код", max_length=64)
    name = models.CharField("Полное наименование", max_length=500)
    short_name = models.CharField("Краткое наименование", max_length=255, blank=True)
    site_type = models.CharField("Вид энергообъекта", max_length=32, choices=SiteType.choices)
    is_external = models.BooleanField(
        "Внешний или смежный объект",
        default=False,
        help_text="Объект учитывается для связей, но не принадлежит эксплуатационному контуру прототипа.",
    )
    is_active = models.BooleanField("Действующий", default=True)
    created_at = models.DateTimeField("Создан", auto_now_add=True)

    class Meta:
        ordering = ("organization__name", "name")
        constraints = [
            models.UniqueConstraint(
                fields=("organization", "code"),
                name="uniq_energy_site_code_per_org",
            )
        ]
        verbose_name = "энергообъект"
        verbose_name_plural = "энергообъекты"

    def __str__(self) -> str:
        return self.short_name or self.name

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.code = self.code.strip().lower()
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        raise ValidationError("Физическое удаление энергообъекта запрещено.")


class EquipmentType(models.Model):
    class Category(models.TextChoices):
        KTP = "KTP", "Комплектная трансформаторная подстанция"
        WTG = "WTG", "Ветроэнергетическая установка"
        SWITCHGEAR = "SWITCHGEAR", "Распределительное устройство"
        SUBSTATION = "SUBSTATION", "Подстанционное оборудование"
        LINE = "LINE", "Линия электропередачи или кабельная линия"
        RPA = "RPA", "Релейная защита и автоматика"
        SDTU = "SDTU", "Средства диспетчерского и технологического управления"
        AUXILIARY = "AUXILIARY", "Вспомогательное оборудование"
        OTHER = "OTHER", "Другое оборудование"

    code = models.SlugField("Системный код", max_length=64, unique=True)
    name = models.CharField("Наименование вида оборудования", max_length=255)
    category = models.CharField("Категория", max_length=24, choices=Category.choices)
    description = models.TextField("Описание", blank=True)
    is_active = models.BooleanField("Используется", default=True)

    class Meta:
        ordering = ("category", "name")
        verbose_name = "вид оборудования"
        verbose_name_plural = "виды оборудования"

    def __str__(self) -> str:
        return self.name

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.code = self.code.strip().lower()
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        raise ValidationError("Физическое удаление вида оборудования запрещено.")


class EquipmentAsset(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "В работе"
        RESERVE = "RESERVE", "Резерв"
        OUT_OF_SERVICE = "OUT_OF_SERVICE", "Выведено из работы"
        DECOMMISSIONED = "DECOMMISSIONED", "Выведено из эксплуатации"
        PROJECT = "PROJECT", "Проектное оборудование"

    public_id = models.UUIDField(
        "Публичный идентификатор",
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="equipment_assets",
        verbose_name="Организация",
    )
    site = models.ForeignKey(
        EnergySite,
        on_delete=models.PROTECT,
        related_name="equipment_assets",
        verbose_name="Энергообъект",
    )
    equipment_type = models.ForeignKey(
        EquipmentType,
        on_delete=models.PROTECT,
        related_name="equipment_assets",
        verbose_name="Вид оборудования",
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="children",
        verbose_name="Родительский объект",
    )
    code = models.CharField("Стабильный код", max_length=96)
    technical_name = models.CharField("Техническое наименование", max_length=500)
    status = models.CharField(
        "Состояние",
        max_length=24,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    voltage_level = models.CharField("Класс напряжения", max_length=64, blank=True)
    commissioned_on = models.DateField("Введено в эксплуатацию", null=True, blank=True)
    decommissioned_on = models.DateField("Выведено из эксплуатации", null=True, blank=True)
    attributes = models.JSONField("Дополнительные характеристики", default=dict, blank=True)
    is_external = models.BooleanField("Внешнее или смежное оборудование", default=False)
    created_at = models.DateTimeField("Создано", auto_now_add=True)

    objects = RegistryManager()

    class Meta:
        ordering = ("site__name", "code")
        constraints = [
            models.UniqueConstraint(
                fields=("organization", "code"),
                name="uniq_equipment_code_per_org",
            ),
            models.CheckConstraint(
                condition=(
                    Q(decommissioned_on__isnull=True)
                    | Q(commissioned_on__isnull=True)
                    | Q(decommissioned_on__gte=models.F("commissioned_on"))
                ),
                name="equipment_lifecycle_window_valid",
            ),
        ]
        indexes = [
            models.Index(fields=("organization", "status", "code")),
            models.Index(fields=("site", "equipment_type", "code")),
        ]
        verbose_name = "единица оборудования"
        verbose_name_plural = "единицы оборудования"

    def __str__(self) -> str:
        return f"{self.code} · {self.technical_name}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.code = self.code.strip().upper()
        if self.pk and self.dispatcher_name_revisions.filter(
            status=PublicationStatus.PUBLISHED
        ).exists():
            original = type(self).objects.get(pk=self.pk)
            protected_fields = (
                "organization_id",
                "site_id",
                "equipment_type_id",
                "parent_id",
                "code",
                "technical_name",
            )
            if any(
                getattr(original, field) != getattr(self, field)
                for field in protected_fields
            ):
                raise ValidationError(
                    "Структура оборудования с опубликованным диспетчерским "
                    "наименованием неизменяема."
                )
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        raise ValidationError("Физическое удаление оборудования запрещено.")

    def clean(self) -> None:
        super().clean()
        errors: dict[str, str] = {}
        if self.site_id and self.organization_id:
            if self.site.organization_id != self.organization_id:
                errors["site"] = "Энергообъект относится к другой организации."
        if self.parent_id:
            if self.parent_id == self.pk or self.parent is self:
                errors["parent"] = "Оборудование не может быть родителем само себе."
            elif self.parent.organization_id != self.organization_id:
                errors["parent"] = "Родительское оборудование относится к другой организации."
            elif self.parent.site_id != self.site_id:
                errors["parent"] = "Родительское оборудование относится к другому энергообъекту."
            else:
                ancestor = self.parent
                visited: set[int] = set()
                if self.pk:
                    visited.add(self.pk)
                while ancestor is not None:
                    if ancestor.pk in visited:
                        errors["parent"] = "Иерархия оборудования содержит цикл."
                        break
                    if ancestor.pk:
                        visited.add(ancestor.pk)
                    ancestor = ancestor.parent
        if not isinstance(self.attributes, dict):
            errors["attributes"] = "Дополнительные характеристики должны быть JSON-объектом."
        if (
            self.commissioned_on
            and self.decommissioned_on
            and self.decommissioned_on < self.commissioned_on
        ):
            errors["decommissioned_on"] = (
                "Дата вывода не может быть раньше даты ввода в эксплуатацию."
            )
        if errors:
            raise ValidationError(errors)


class EquipmentNameRevision(models.Model):
    equipment = models.ForeignKey(
        EquipmentAsset,
        on_delete=models.PROTECT,
        related_name="dispatcher_name_revisions",
        verbose_name="Оборудование",
    )
    revision_number = models.PositiveIntegerField("Номер редакции")
    dispatcher_name = models.CharField("Диспетчерское наименование", max_length=1000)
    effective_from = models.DateField("Действует с")
    effective_until = models.DateField("Явно действует по", null=True, blank=True)
    basis_reference = models.CharField("Документ-основание", max_length=1000, blank=True)
    status = models.CharField(
        "Статус публикации",
        max_length=16,
        choices=PublicationStatus.choices,
        default=PublicationStatus.DRAFT,
    )
    published_at = models.DateTimeField("Опубликовано", null=True, blank=True, editable=False)
    approved_by = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="approved_equipment_names",
        verbose_name="Опубликовал",
    )
    digest = models.CharField(
        "SHA-256 редакции наименования",
        max_length=64,
        blank=True,
        editable=False,
    )
    created_at = models.DateTimeField("Создано", auto_now_add=True)

    objects = RegistryManager()

    class Meta:
        ordering = ("equipment", "-effective_from", "-revision_number")
        constraints = [
            models.UniqueConstraint(
                fields=("equipment", "revision_number"),
                name="uniq_equipment_name_revision",
            ),
            models.UniqueConstraint(
                fields=("equipment", "effective_from"),
                name="uniq_equipment_name_effective_start",
            ),
            models.CheckConstraint(
                condition=(
                    Q(status="DRAFT", published_at__isnull=True, digest="")
                    | (
                        Q(status="PUBLISHED", published_at__isnull=False)
                        & ~Q(digest="")
                    )
                ),
                name="equipment_name_publication_consistent",
            ),
        ]
        verbose_name = "редакция диспетчерского наименования"
        verbose_name_plural = "редакции диспетчерских наименований"

    def __str__(self) -> str:
        return f"{self.equipment.code} · {self.dispatcher_name}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.pk:
            original = type(self).objects.get(pk=self.pk)
            if original.status == PublicationStatus.PUBLISHED:
                raise ValidationError(
                    "Опубликованная редакция диспетчерского наименования неизменяема."
                )
        self.dispatcher_name = " ".join(self.dispatcher_name.split())
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        raise ValidationError(
            "Физическое удаление редакции диспетчерского наименования запрещено."
        )

    def clean(self) -> None:
        super().clean()
        validate_window(self.effective_from, self.effective_until, "effective_until")
        errors: dict[str, str] = {}
        if self.approved_by_id:
            if self.approved_by.organization_id != self.equipment.organization_id:
                errors["approved_by"] = "Сотрудник относится к другой организации."
        if self.status == PublicationStatus.PUBLISHED:
            if not self.published_at:
                errors["published_at"] = "Для публикации требуется серверное время."
            if len(self.digest) != 64:
                errors["digest"] = "Для публикации требуется SHA-256 редакции."
        if errors:
            raise ValidationError(errors)


class EquipmentAlias(models.Model):
    class AliasType(models.TextChoices):
        DISPATCHER = "DISPATCHER", "Диспетчерский вариант"
        LEGACY = "LEGACY", "Историческое наименование"
        ABBREVIATION = "ABBREVIATION", "Сокращение"
        LOCAL = "LOCAL", "Локальное наименование"
        SEARCH = "SEARCH", "Поисковый вариант"

    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="equipment_aliases",
        verbose_name="Организация",
    )
    equipment = models.ForeignKey(
        EquipmentAsset,
        on_delete=models.PROTECT,
        related_name="aliases",
        verbose_name="Оборудование",
    )
    alias = models.CharField("Алиас", max_length=1000)
    normalized_alias = models.CharField(
        "Нормализованный алиас",
        max_length=1000,
        editable=False,
    )
    alias_type = models.CharField("Вид алиаса", max_length=24, choices=AliasType.choices)
    valid_from = models.DateField("Действует с", default=timezone.localdate)
    valid_until = models.DateField("Действует по", null=True, blank=True)
    basis_reference = models.CharField("Основание", max_length=1000, blank=True)
    created_by = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        related_name="created_equipment_aliases",
        verbose_name="Создал",
    )
    created_at = models.DateTimeField("Создан", auto_now_add=True)

    objects = RegistryManager()

    class Meta:
        ordering = ("equipment", "alias")
        constraints = [
            models.UniqueConstraint(
                fields=("organization", "normalized_alias", "valid_from"),
                name="uniq_equipment_alias_start_per_org",
            )
        ]
        verbose_name = "алиас оборудования"
        verbose_name_plural = "алиасы оборудования"

    def __str__(self) -> str:
        return self.alias

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.pk:
            raise ValidationError("Алиас оборудования неизменяем; создайте новую запись.")
        self.alias = " ".join(self.alias.split())
        self.normalized_alias = self.alias.casefold()
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        raise ValidationError("Физическое удаление алиаса оборудования запрещено.")

    def clean(self) -> None:
        super().clean()
        validate_window(self.valid_from, self.valid_until, "valid_until")
        errors: dict[str, str] = {}
        if self.equipment_id and self.organization_id:
            if self.equipment.organization_id != self.organization_id:
                errors["equipment"] = "Оборудование относится к другой организации."
        if self.created_by_id and self.created_by.organization_id != self.organization_id:
            errors["created_by"] = "Сотрудник относится к другой организации."
        if errors:
            raise ValidationError(errors)


class EquipmentRelation(models.Model):
    class RelationType(models.TextChoices):
        FEEDS = "FEEDS", "Питает"
        CONNECTS = "CONNECTS", "Соединяет"
        PROTECTS = "PROTECTS", "Защищает"
        MONITORS = "MONITORS", "Контролирует или передаёт телеметрию"
        BACKUP_FOR = "BACKUP_FOR", "Резервирует"
        RELATED = "RELATED", "Связано"

    source_equipment = models.ForeignKey(
        EquipmentAsset,
        on_delete=models.PROTECT,
        related_name="outgoing_equipment_relations",
        verbose_name="Исходное оборудование",
    )
    target_equipment = models.ForeignKey(
        EquipmentAsset,
        on_delete=models.PROTECT,
        related_name="incoming_equipment_relations",
        verbose_name="Связанное оборудование",
    )
    relation_type = models.CharField(
        "Вид связи",
        max_length=24,
        choices=RelationType.choices,
    )
    description = models.TextField("Описание связи", blank=True)
    valid_from = models.DateField("Действует с", default=timezone.localdate)
    valid_until = models.DateField("Действует по", null=True, blank=True)
    basis_reference = models.CharField("Документ-основание", max_length=1000, blank=True)
    created_by = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        related_name="created_equipment_relations",
        verbose_name="Создал",
    )
    created_at = models.DateTimeField("Создана", auto_now_add=True)

    objects = RegistryManager()

    class Meta:
        ordering = ("source_equipment", "relation_type", "target_equipment")
        constraints = [
            models.UniqueConstraint(
                fields=(
                    "source_equipment",
                    "target_equipment",
                    "relation_type",
                    "valid_from",
                ),
                name="uniq_equipment_relation_start",
            ),
            models.CheckConstraint(
                condition=~Q(source_equipment=models.F("target_equipment")),
                name="equipment_relation_not_self",
            ),
        ]
        verbose_name = "связь оборудования"
        verbose_name_plural = "связи оборудования"

    def __str__(self) -> str:
        return (
            f"{self.source_equipment.code} → {self.target_equipment.code} "
            f"({self.get_relation_type_display()})"
        )

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.pk:
            raise ValidationError("Связь оборудования неизменяема; создайте новую запись.")
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        raise ValidationError("Физическое удаление связи оборудования запрещено.")

    def clean(self) -> None:
        super().clean()
        validate_window(self.valid_from, self.valid_until, "valid_until")
        errors: dict[str, str] = {}
        if self.source_equipment_id == self.target_equipment_id:
            errors["target_equipment"] = "Оборудование нельзя связать с самим собой."
        if self.source_equipment_id and self.target_equipment_id:
            if (
                self.source_equipment.organization_id
                != self.target_equipment.organization_id
            ):
                errors["target_equipment"] = (
                    "Связанное оборудование относится к другой организации."
                )
            if (
                self.created_by_id
                and self.created_by.organization_id
                != self.source_equipment.organization_id
            ):
                errors["created_by"] = "Сотрудник относится к другой организации."
        if errors:
            raise ValidationError(errors)


class DocumentEquipmentLink(models.Model):
    document = models.ForeignKey(
        "documents.Document",
        on_delete=models.PROTECT,
        related_name="equipment_links",
        verbose_name="Документ",
    )
    document_version = models.ForeignKey(
        "documents.DocumentVersion",
        on_delete=models.PROTECT,
        related_name="equipment_links",
        verbose_name="Версия документа",
    )
    equipment = models.ForeignKey(
        EquipmentAsset,
        on_delete=models.PROTECT,
        related_name="document_links",
        verbose_name="Оборудование",
    )
    created_by = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        related_name="created_document_equipment_links",
        verbose_name="Добавил",
    )
    created_at = models.DateTimeField("Добавлено", auto_now_add=True)

    objects = RegistryManager()

    class Meta:
        ordering = ("document_version", "equipment__code")
        constraints = [
            models.UniqueConstraint(
                fields=("document_version", "equipment"),
                name="uniq_document_version_equipment",
            )
        ]
        verbose_name = "связь документа с оборудованием"
        verbose_name_plural = "связи документов с оборудованием"

    def __str__(self) -> str:
        return f"{self.document} · {self.equipment.code}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.pk:
            original = type(self).objects.get(pk=self.pk)
            if original.document_version.status != "DRAFT":
                raise ValidationError(
                    "Связь зарегистрированной версии с оборудованием неизменяема."
                )
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        if self.document_version.status != "DRAFT":
            raise ValidationError(
                "Связь зарегистрированной версии с оборудованием нельзя удалить."
            )
        return super().delete(*args, **kwargs)

    def clean(self) -> None:
        super().clean()
        errors: dict[str, str] = {}
        if self.document_version_id and self.document_id:
            if self.document_version.document_id != self.document_id:
                errors["document_version"] = "Версия относится к другому документу."
            if self.document_version.status != "DRAFT":
                errors["document_version"] = (
                    "Оборудование можно назначать только черновой версии."
                )
        if self.equipment_id and self.document_id:
            if self.equipment.organization_id != self.document.organization_id:
                errors["equipment"] = "Оборудование относится к другой организации."
        if self.created_by_id and self.document_id:
            if self.created_by.organization_id != self.document.organization_id:
                errors["created_by"] = "Сотрудник относится к другой организации."
        if errors:
            raise ValidationError(errors)


class DocumentEquipmentSnapshot(models.Model):
    link = models.OneToOneField(
        DocumentEquipmentLink,
        on_delete=models.PROTECT,
        related_name="snapshot",
        verbose_name="Исходная связь",
    )
    document = models.ForeignKey(
        "documents.Document",
        on_delete=models.PROTECT,
        related_name="equipment_snapshots",
        verbose_name="Документ",
    )
    document_version = models.ForeignKey(
        "documents.DocumentVersion",
        on_delete=models.PROTECT,
        related_name="equipment_snapshots",
        verbose_name="Версия документа",
    )
    equipment = models.ForeignKey(
        EquipmentAsset,
        on_delete=models.PROTECT,
        related_name="document_snapshots",
        verbose_name="Оборудование",
    )
    equipment_public_id_snapshot = models.UUIDField("Идентификатор оборудования")
    equipment_code_snapshot = models.CharField("Код оборудования", max_length=96)
    dispatcher_name_snapshot = models.CharField(
        "Диспетчерское наименование",
        max_length=1000,
    )
    technical_name_snapshot = models.CharField(
        "Техническое наименование",
        max_length=500,
    )
    equipment_type_code_snapshot = models.CharField("Код вида оборудования", max_length=64)
    equipment_type_name_snapshot = models.CharField(
        "Вид оборудования",
        max_length=255,
    )
    site_code_snapshot = models.CharField("Код энергообъекта", max_length=64)
    site_name_snapshot = models.CharField("Энергообъект", max_length=500)
    hierarchy_path_snapshot = models.TextField("Иерархический путь")
    name_revision_number_snapshot = models.PositiveIntegerField(
        "Редакция диспетчерского наименования",
        null=True,
        blank=True,
    )
    captured_at = models.DateTimeField(
        "Зафиксировано сервером",
        default=timezone.now,
        editable=False,
    )

    objects = RegistryManager()

    class Meta:
        ordering = ("document_version", "equipment_code_snapshot")
        constraints = [
            models.UniqueConstraint(
                fields=("document_version", "equipment"),
                name="uniq_document_equipment_snapshot",
            )
        ]
        verbose_name = "снимок оборудования документа"
        verbose_name_plural = "снимки оборудования документов"

    def __str__(self) -> str:
        return f"{self.document} · {self.dispatcher_name_snapshot}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.pk:
            raise ValidationError("Снимок оборудования документа неизменяем.")
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        raise ValidationError("Физическое удаление снимка оборудования запрещено.")

    def clean(self) -> None:
        super().clean()
        errors: dict[str, str] = {}
        if self.document_version_id and self.document_id:
            if self.document_version.document_id != self.document_id:
                errors["document_version"] = "Версия относится к другому документу."
        if self.link_id:
            if self.link.document_id != self.document_id:
                errors["link"] = "Связь относится к другому документу."
            if self.link.document_version_id != self.document_version_id:
                errors["link"] = "Связь относится к другой версии."
            if self.link.equipment_id != self.equipment_id:
                errors["link"] = "Связь относится к другому оборудованию."
        if self.equipment_id and self.document_id:
            if self.equipment.organization_id != self.document.organization_id:
                errors["equipment"] = "Оборудование относится к другой организации."
        if errors:
            raise ValidationError(errors)


class EquipmentAuditEvent(models.Model):
    class EventType(models.TextChoices):
        NAME_PUBLISHED = "NAME_PUBLISHED", "Опубликовано диспетчерское наименование"
        DOCUMENT_SNAPSHOT_CREATED = (
            "DOCUMENT_SNAPSHOT_CREATED",
            "Создан снимок оборудования документа",
        )

    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="equipment_audit_events",
        verbose_name="Организация",
    )
    event_type = models.CharField("Событие", max_length=40, choices=EventType.choices)
    occurred_at = models.DateTimeField(
        "Серверное время",
        default=timezone.now,
        editable=False,
    )
    actor_employee = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        related_name="equipment_audit_events",
        verbose_name="Сотрудник",
    )
    equipment = models.ForeignKey(
        EquipmentAsset,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="audit_events",
        verbose_name="Оборудование",
    )
    document_version = models.ForeignKey(
        "documents.DocumentVersion",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="equipment_audit_events",
        verbose_name="Версия документа",
    )
    payload = models.JSONField("Данные события", default=dict, blank=True)

    objects = RegistryManager()

    class Meta:
        ordering = ("-occurred_at", "-pk")
        indexes = [
            models.Index(fields=("organization", "occurred_at")),
            models.Index(fields=("event_type", "occurred_at")),
        ]
        verbose_name = "событие аудита оборудования"
        verbose_name_plural = "события аудита оборудования"

    def __str__(self) -> str:
        return f"{self.get_event_type_display()} · {self.occurred_at}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.pk:
            raise ValidationError("Событие аудита оборудования неизменяемо.")
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        raise ValidationError("Физическое удаление события аудита запрещено.")
