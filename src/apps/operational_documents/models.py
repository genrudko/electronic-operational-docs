from __future__ import annotations

import uuid
from typing import Any

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q
from django.utils import timezone

from apps.documents.models import Document
from apps.equipment.models import EquipmentAsset
from apps.organizations.models import Employee, Organization, Workplace


class ProtectedQuerySet(models.QuerySet):
    def update(self, **kwargs: Any) -> int:
        raise ValidationError("Массовое изменение защищённых записей оперативной документации запрещено.")

    def delete(self, *args: Any, **kwargs: Any):
        raise ValidationError("Физическое удаление записей оперативной документации запрещено.")


class ProtectedManager(models.Manager.from_queryset(ProtectedQuerySet)):
    pass


class SchemaPublicationStatus(models.TextChoices):
    DRAFT = "DRAFT", "Черновик"
    PUBLISHED = "PUBLISHED", "Опубликована"
    RETIRED = "RETIRED", "Выведена из действия"


class FieldType(models.TextChoices):
    TEXT = "TEXT", "Короткий текст"
    LONG_TEXT = "LONG_TEXT", "Многострочный текст"
    INTEGER = "INTEGER", "Целое число"
    DECIMAL = "DECIMAL", "Число"
    BOOLEAN = "BOOLEAN", "Да / нет"
    DATE = "DATE", "Дата"
    DATETIME = "DATETIME", "Дата и время"
    CHOICE = "CHOICE", "Выбор из списка"


class RecordRevisionAction(models.TextChoices):
    CREATED = "CREATED", "Создание"
    UPDATED = "UPDATED", "Изменение"
    TRANSITION = "TRANSITION", "Переход состояния"


class DocumentLinkType(models.TextChoices):
    BASIS = "BASIS", "Документ-основание"
    ATTACHMENT = "ATTACHMENT", "Связанный документ"
    RESULT = "RESULT", "Результирующий документ"


class RecordRelationType(models.TextChoices):
    BASIS = "BASIS", "Основание"
    RESULT = "RESULT", "Результат"
    RELATED = "RELATED", "Связано"
    CONTINUES = "CONTINUES", "Продолжает"
    SUPERSEDES = "SUPERSEDES", "Заменяет"


class OperationalDocumentType(models.Model):
    public_id = models.UUIDField(
        "Публичный идентификатор",
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="operational_document_types",
        verbose_name="Организация",
    )
    code = models.SlugField("Код", max_length=64)
    name = models.CharField("Наименование", max_length=255)
    short_name = models.CharField("Краткое наименование", max_length=120, blank=True)
    description = models.TextField("Описание", blank=True)
    is_active = models.BooleanField("Действующий", default=True)
    created_by = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        related_name="created_operational_document_types",
        verbose_name="Создал",
    )
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    updated_at = models.DateTimeField("Изменён", auto_now=True)

    objects = ProtectedManager()

    class Meta:
        ordering = ("name", "code")
        constraints = [
            models.UniqueConstraint(
                fields=("organization", "code"),
                name="uniq_opdoc_type_code_per_org",
            )
        ]
        verbose_name = "тип оперативного документа"
        verbose_name_plural = "типы оперативных документов"

    def __str__(self) -> str:
        return self.short_name or self.name

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.code = self.code.strip().lower()
        self.name = self.name.strip()
        self.short_name = self.short_name.strip()
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any):
        raise ValidationError("Физическое удаление типа оперативного документа запрещено.")

    def clean(self) -> None:
        super().clean()
        if self.created_by_id and self.created_by.organization_id != self.organization_id:
            raise ValidationError({"created_by": "Создатель относится к другой организации."})


class OperationalDocumentTypeRevision(models.Model):
    public_id = models.UUIDField(
        "Публичный идентификатор",
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )
    document_type = models.ForeignKey(
        OperationalDocumentType,
        on_delete=models.PROTECT,
        related_name="revisions",
        verbose_name="Тип документа",
    )
    revision_number = models.PositiveIntegerField("Номер редакции")
    status = models.CharField(
        "Состояние",
        max_length=16,
        choices=SchemaPublicationStatus.choices,
        default=SchemaPublicationStatus.DRAFT,
        db_index=True,
    )
    number_prefix = models.CharField("Префикс номера", max_length=24)
    number_width = models.PositiveSmallIntegerField("Разрядность номера", default=4)
    requires_workplace = models.BooleanField("Требуется рабочее место", default=True)
    field_definitions = models.JSONField("Поля", default=list)
    status_definitions = models.JSONField("Статусы", default=list)
    transition_definitions = models.JSONField("Переходы", default=list)
    participant_role_definitions = models.JSONField("Роли участников", default=list)
    canonical_snapshot = models.JSONField("Канонический снимок", default=dict, blank=True)
    sha256 = models.CharField("SHA-256", max_length=64, blank=True, editable=False)
    created_by = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        related_name="created_operational_document_type_revisions",
        verbose_name="Создал редакцию",
    )
    created_at = models.DateTimeField("Создана", auto_now_add=True)
    published_by = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="published_operational_document_type_revisions",
        verbose_name="Опубликовал",
    )
    published_at = models.DateTimeField("Опубликована", null=True, blank=True)

    objects = ProtectedManager()

    class Meta:
        ordering = ("document_type__name", "-revision_number")
        constraints = [
            models.UniqueConstraint(
                fields=("document_type", "revision_number"),
                name="uniq_opdoc_type_revision_number",
            ),
            models.CheckConstraint(
                condition=Q(revision_number__gte=1),
                name="opdoc_type_revision_positive",
            ),
            models.CheckConstraint(
                condition=Q(number_width__gte=1) & Q(number_width__lte=12),
                name="opdoc_number_width_range",
            ),
        ]
        verbose_name = "редакция типа оперативного документа"
        verbose_name_plural = "редакции типов оперативных документов"

    def __str__(self) -> str:
        return f"{self.document_type} · редакция {self.revision_number}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.pk:
            original = type(self).objects.get(pk=self.pk)
            if original.status == SchemaPublicationStatus.PUBLISHED:
                raise ValidationError("Опубликованная редакция типа неизменяема.")
        self.number_prefix = self.number_prefix.strip().upper()
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any):
        raise ValidationError("Физическое удаление редакции типа запрещено.")

    def clean(self) -> None:
        super().clean()
        errors: dict[str, str] = {}
        organization_id = self.document_type.organization_id if self.document_type_id else None
        if self.created_by_id and self.created_by.organization_id != organization_id:
            errors["created_by"] = "Создатель редакции относится к другой организации."
        if self.published_by_id and self.published_by.organization_id != organization_id:
            errors["published_by"] = "Публикующий относится к другой организации."
        if self.status == SchemaPublicationStatus.PUBLISHED:
            if not self.published_by_id or not self.published_at or not self.sha256:
                errors["status"] = "Опубликованная редакция должна иметь автора, время и SHA-256."
        elif self.published_by_id or self.published_at or self.sha256:
            errors["status"] = "Реквизиты публикации допустимы только для опубликованной редакции."
        if errors:
            raise ValidationError(errors)


class OperationalDocumentNumberSequence(models.Model):
    document_type = models.ForeignKey(
        OperationalDocumentType,
        on_delete=models.PROTECT,
        related_name="number_sequences",
        verbose_name="Тип документа",
    )
    year = models.PositiveSmallIntegerField("Год")
    last_value = models.PositiveBigIntegerField("Последнее значение", default=0)
    updated_at = models.DateTimeField("Изменён", auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("document_type", "year"),
                name="uniq_opdoc_sequence_type_year",
            )
        ]
        verbose_name = "нумератор оперативных документов"
        verbose_name_plural = "нумераторы оперативных документов"

    def __str__(self) -> str:
        return f"{self.document_type} · {self.year}: {self.last_value}"


class OperationalDocumentRecord(models.Model):
    public_id = models.UUIDField(
        "Публичный идентификатор",
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="operational_document_records",
        verbose_name="Организация",
    )
    document_type = models.ForeignKey(
        OperationalDocumentType,
        on_delete=models.PROTECT,
        related_name="records",
        verbose_name="Тип документа",
    )
    schema_revision = models.ForeignKey(
        OperationalDocumentTypeRevision,
        on_delete=models.PROTECT,
        related_name="records",
        verbose_name="Редакция структуры",
    )
    sequence_year = models.PositiveSmallIntegerField("Год нумерации")
    sequence_value = models.PositiveBigIntegerField("Порядковый номер")
    registration_number = models.CharField("Регистрационный номер", max_length=128)
    title = models.CharField("Заголовок", max_length=500)
    summary = models.TextField("Краткое содержание", blank=True)
    workplace = models.ForeignKey(
        Workplace,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="operational_document_records",
        verbose_name="Рабочее место",
    )
    workplace_name_snapshot = models.CharField(
        "Снимок рабочего места",
        max_length=500,
        blank=True,
        editable=False,
    )
    event_at = models.DateTimeField("Время события", default=timezone.now, db_index=True)
    status_code = models.CharField("Код состояния", max_length=64, db_index=True)
    status_name_snapshot = models.CharField("Наименование состояния", max_length=255)
    status_is_terminal = models.BooleanField("Конечное состояние", default=False, db_index=True)
    field_values = models.JSONField("Значения полей", default=dict)
    search_text = models.TextField("Поисковый текст", blank=True, editable=False)
    created_by = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        related_name="created_operational_document_records",
        verbose_name="Создал",
    )
    created_by_full_name_snapshot = models.CharField(
        "Ф.И.О. создателя",
        max_length=500,
        editable=False,
    )
    created_by_position_snapshot = models.CharField(
        "Должность создателя",
        max_length=500,
        editable=False,
    )
    created_by_division_snapshot = models.CharField(
        "Подразделение создателя",
        max_length=500,
        editable=False,
    )
    updated_by = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        related_name="updated_operational_document_records",
        verbose_name="Последним изменил",
    )
    version = models.PositiveBigIntegerField("Версия", default=1)
    created_at = models.DateTimeField("Создана", auto_now_add=True)
    updated_at = models.DateTimeField("Изменена", auto_now=True)
    closed_at = models.DateTimeField("Закрыта", null=True, blank=True)

    objects = ProtectedManager()

    class Meta:
        ordering = ("-event_at", "-pk")
        constraints = [
            models.UniqueConstraint(
                fields=("organization", "registration_number"),
                name="uniq_opdoc_registration_number_org",
            ),
            models.UniqueConstraint(
                fields=("document_type", "sequence_year", "sequence_value"),
                name="uniq_opdoc_sequence_components",
            ),
            models.CheckConstraint(
                condition=Q(version__gte=1),
                name="opdoc_record_version_positive",
            ),
            models.CheckConstraint(
                condition=(
                    Q(status_is_terminal=True, closed_at__isnull=False)
                    | Q(status_is_terminal=False, closed_at__isnull=True)
                ),
                name="opdoc_terminal_closed_consistent",
            ),
        ]
        indexes = [
            models.Index(
                fields=("organization", "document_type", "status_code", "event_at"),
                name="opdoc_registry_filter_idx",
            ),
            models.Index(
                fields=("organization", "workplace", "event_at"),
                name="opdoc_workplace_time_idx",
            ),
        ]
        verbose_name = "запись оперативной документации"
        verbose_name_plural = "записи оперативной документации"

    def __str__(self) -> str:
        return f"{self.registration_number}: {self.title}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.pk:
            original = type(self).objects.get(pk=self.pk)
            protected = (
                "public_id",
                "organization_id",
                "document_type_id",
                "schema_revision_id",
                "sequence_year",
                "sequence_value",
                "registration_number",
                "created_by_id",
                "created_by_full_name_snapshot",
                "created_by_position_snapshot",
                "created_by_division_snapshot",
                "created_at",
            )
            if any(getattr(original, field) != getattr(self, field) for field in protected):
                raise ValidationError("Идентификационные реквизиты записи неизменяемы.")
        self.title = self.title.strip()
        self.summary = self.summary.strip()
        self.status_code = self.status_code.strip().upper()
        self.status_name_snapshot = self.status_name_snapshot.strip()
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any):
        raise ValidationError("Физическое удаление оперативной записи запрещено.")

    def clean(self) -> None:
        super().clean()
        errors: dict[str, str] = {}
        if self.document_type_id and self.document_type.organization_id != self.organization_id:
            errors["document_type"] = "Тип документа относится к другой организации."
        if self.schema_revision_id and self.schema_revision.document_type_id != self.document_type_id:
            errors["schema_revision"] = "Редакция структуры относится к другому типу документа."
        if self.workplace_id and self.workplace.organization_id != self.organization_id:
            errors["workplace"] = "Рабочее место относится к другой организации."
        for field_name in ("created_by", "updated_by"):
            employee = getattr(self, field_name, None)
            if employee and employee.organization_id != self.organization_id:
                errors[field_name] = "Сотрудник относится к другой организации."
        if self.status_is_terminal and self.closed_at is None:
            errors["closed_at"] = "Конечное состояние требует времени закрытия."
        if not self.status_is_terminal and self.closed_at is not None:
            errors["closed_at"] = "Время закрытия допустимо только в конечном состоянии."
        if self.schema_revision_id and self.schema_revision.requires_workplace and not self.workplace_id:
            errors["workplace"] = "Для этого типа документа требуется рабочее место."
        if not self.title:
            errors["title"] = "Заголовок обязателен."
        if errors:
            raise ValidationError(errors)


class OperationalDocumentParticipant(models.Model):
    record = models.ForeignKey(
        OperationalDocumentRecord,
        on_delete=models.PROTECT,
        related_name="participants",
        verbose_name="Запись",
    )
    role_code = models.CharField("Код роли", max_length=64)
    role_name_snapshot = models.CharField("Наименование роли", max_length=255)
    employee = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        related_name="operational_document_participations",
        verbose_name="Сотрудник",
    )
    employee_full_name_snapshot = models.CharField("Ф.И.О.", max_length=500)
    employee_position_snapshot = models.CharField("Должность", max_length=500)
    employee_division_snapshot = models.CharField("Подразделение", max_length=500)
    employee_workplace_snapshot = models.CharField("Рабочее место", max_length=500, blank=True)
    created_at = models.DateTimeField("Создан", auto_now_add=True)

    class Meta:
        ordering = ("role_name_snapshot", "employee_full_name_snapshot")
        constraints = [
            models.UniqueConstraint(
                fields=("record", "role_code", "employee"),
                name="uniq_opdoc_participant_role_employee",
            )
        ]
        verbose_name = "участник оперативной записи"
        verbose_name_plural = "участники оперативной записи"

    def __str__(self) -> str:
        return f"{self.role_name_snapshot}: {self.employee_full_name_snapshot}"

    def clean(self) -> None:
        super().clean()
        if (
            self.record_id
            and self.employee_id
            and self.record.organization_id != self.employee.organization_id
        ):
            raise ValidationError({"employee": "Сотрудник относится к другой организации."})


class OperationalDocumentEquipmentLink(models.Model):
    record = models.ForeignKey(
        OperationalDocumentRecord,
        on_delete=models.PROTECT,
        related_name="equipment_links",
        verbose_name="Запись",
    )
    equipment = models.ForeignKey(
        EquipmentAsset,
        on_delete=models.PROTECT,
        related_name="operational_document_links",
        verbose_name="Оборудование",
    )
    equipment_code_snapshot = models.CharField("Код оборудования", max_length=96)
    dispatcher_name_snapshot = models.CharField("Диспетчерское наименование", max_length=500)
    site_name_snapshot = models.CharField("Энергообъект", max_length=500)
    equipment_type_snapshot = models.CharField("Вид оборудования", max_length=255)
    created_at = models.DateTimeField("Создана", auto_now_add=True)

    class Meta:
        ordering = ("dispatcher_name_snapshot", "equipment_code_snapshot")
        constraints = [
            models.UniqueConstraint(
                fields=("record", "equipment"),
                name="uniq_opdoc_record_equipment",
            )
        ]
        verbose_name = "связь оперативной записи с оборудованием"
        verbose_name_plural = "связи оперативных записей с оборудованием"

    def __str__(self) -> str:
        return f"{self.record.registration_number}: {self.dispatcher_name_snapshot}"

    def clean(self) -> None:
        super().clean()
        if (
            self.record_id
            and self.equipment_id
            and self.record.organization_id != self.equipment.organization_id
        ):
            raise ValidationError({"equipment": "Оборудование относится к другой организации."})


class OperationalDocumentExternalDocumentLink(models.Model):
    record = models.ForeignKey(
        OperationalDocumentRecord,
        on_delete=models.PROTECT,
        related_name="document_links",
        verbose_name="Запись",
    )
    document = models.ForeignKey(
        Document,
        on_delete=models.PROTECT,
        related_name="operational_document_links",
        verbose_name="Документ",
    )
    link_type = models.CharField(
        "Вид связи",
        max_length=16,
        choices=DocumentLinkType.choices,
        default=DocumentLinkType.BASIS,
    )
    registration_number_snapshot = models.CharField("Номер документа", max_length=128, blank=True)
    title_snapshot = models.CharField("Заголовок документа", max_length=500)
    created_at = models.DateTimeField("Создана", auto_now_add=True)

    class Meta:
        ordering = ("link_type", "registration_number_snapshot", "title_snapshot")
        constraints = [
            models.UniqueConstraint(
                fields=("record", "document", "link_type"),
                name="uniq_opdoc_record_document_link",
            )
        ]
        verbose_name = "связь оперативной записи с документом"
        verbose_name_plural = "связи оперативных записей с документами"

    def __str__(self) -> str:
        return f"{self.record.registration_number}: {self.title_snapshot}"

    def clean(self) -> None:
        super().clean()
        if (
            self.record_id
            and self.document_id
            and self.record.organization_id != self.document.organization_id
        ):
            raise ValidationError({"document": "Документ относится к другой организации."})


class OperationalDocumentRelation(models.Model):
    source_record = models.ForeignKey(
        OperationalDocumentRecord,
        on_delete=models.PROTECT,
        related_name="outgoing_relations",
        verbose_name="Исходная запись",
    )
    target_record = models.ForeignKey(
        OperationalDocumentRecord,
        on_delete=models.PROTECT,
        related_name="incoming_relations",
        verbose_name="Связанная запись",
    )
    relation_type = models.CharField(
        "Вид связи",
        max_length=16,
        choices=RecordRelationType.choices,
        default=RecordRelationType.RELATED,
    )
    relation_name_snapshot = models.CharField("Наименование связи", max_length=255)
    created_by = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        related_name="created_operational_document_relations",
        verbose_name="Создал связь",
    )
    created_at = models.DateTimeField("Создана", auto_now_add=True)

    class Meta:
        ordering = ("relation_type", "target_record__event_at")
        constraints = [
            models.UniqueConstraint(
                fields=("source_record", "target_record", "relation_type"),
                name="uniq_opdoc_record_relation",
            ),
            models.CheckConstraint(
                condition=~Q(source_record=F("target_record")),
                name="opdoc_relation_not_self",
            ),
        ]
        verbose_name = "связь оперативных записей"
        verbose_name_plural = "связи оперативных записей"

    def __str__(self) -> str:
        return (
            f"{self.source_record.registration_number} → "
            f"{self.target_record.registration_number}"
        )

    def clean(self) -> None:
        super().clean()
        errors: dict[str, str] = {}
        if self.source_record_id and self.target_record_id:
            if self.source_record_id == self.target_record_id:
                errors["target_record"] = "Запись нельзя связать саму с собой."
            elif self.source_record.organization_id != self.target_record.organization_id:
                errors["target_record"] = "Связываемые записи относятся к разным организациям."
        if self.source_record_id and self.created_by_id:
            if self.source_record.organization_id != self.created_by.organization_id:
                errors["created_by"] = "Создатель связи относится к другой организации."
        if errors:
            raise ValidationError(errors)


class OperationalDocumentRecordRevision(models.Model):
    record = models.ForeignKey(
        OperationalDocumentRecord,
        on_delete=models.PROTECT,
        related_name="revisions",
        verbose_name="Запись",
    )
    revision_number = models.PositiveBigIntegerField("Номер редакции")
    action = models.CharField("Действие", max_length=16, choices=RecordRevisionAction.choices)
    status_code_snapshot = models.CharField("Код состояния", max_length=64)
    status_name_snapshot = models.CharField("Наименование состояния", max_length=255)
    snapshot = models.JSONField("Канонический снимок")
    sha256 = models.CharField("SHA-256", max_length=64)
    actor = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        related_name="operational_document_record_revisions",
        verbose_name="Автор редакции",
    )
    comment = models.TextField("Комментарий", blank=True)
    created_at = models.DateTimeField("Создана", auto_now_add=True)

    objects = ProtectedManager()

    class Meta:
        ordering = ("-revision_number", "-pk")
        constraints = [
            models.UniqueConstraint(
                fields=("record", "revision_number"),
                name="uniq_opdoc_record_revision_number",
            )
        ]
        verbose_name = "редакция оперативной записи"
        verbose_name_plural = "редакции оперативных записей"

    def __str__(self) -> str:
        return f"{self.record.registration_number} · редакция {self.revision_number}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.pk:
            raise ValidationError("Редакция оперативной записи неизменяема.")
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any):
        raise ValidationError("Физическое удаление редакции запрещено.")

    def clean(self) -> None:
        super().clean()
        if self.record_id and self.actor_id and self.record.organization_id != self.actor.organization_id:
            raise ValidationError({"actor": "Автор редакции относится к другой организации."})


class OperationalDocumentAuditEvent(models.Model):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="operational_document_audit_events",
        verbose_name="Организация",
    )
    document_type = models.ForeignKey(
        OperationalDocumentType,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="audit_events",
        verbose_name="Тип документа",
    )
    record = models.ForeignKey(
        OperationalDocumentRecord,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="audit_events",
        verbose_name="Запись",
    )
    event_type = models.CharField("Событие", max_length=64, db_index=True)
    actor = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        related_name="operational_document_audit_events",
        verbose_name="Инициатор",
    )
    entity_type = models.CharField("Тип сущности", max_length=64)
    entity_id = models.CharField("Идентификатор сущности", max_length=128)
    payload = models.JSONField("Данные события", default=dict, blank=True)
    occurred_at = models.DateTimeField("Время", auto_now_add=True, db_index=True)

    objects = ProtectedManager()

    class Meta:
        ordering = ("-occurred_at", "-pk")
        indexes = [
            models.Index(
                fields=("organization", "event_type", "occurred_at"),
                name="opdoc_audit_lookup_idx",
            )
        ]
        verbose_name = "событие аудита оперативной документации"
        verbose_name_plural = "события аудита оперативной документации"

    def __str__(self) -> str:
        return f"{self.event_type} · {self.entity_type}:{self.entity_id}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.pk:
            raise ValidationError("Событие аудита неизменяемо.")
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any):
        raise ValidationError("Физическое удаление аудита запрещено.")

    def clean(self) -> None:
        super().clean()
        errors: dict[str, str] = {}
        if self.actor_id and self.actor.organization_id != self.organization_id:
            errors["actor"] = "Инициатор относится к другой организации."
        if self.document_type_id and self.document_type.organization_id != self.organization_id:
            errors["document_type"] = "Тип документа относится к другой организации."
        if self.record_id and self.record.organization_id != self.organization_id:
            errors["record"] = "Запись относится к другой организации."
        if errors:
            raise ValidationError(errors)
