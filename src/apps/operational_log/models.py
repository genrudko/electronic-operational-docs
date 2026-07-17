from __future__ import annotations

from typing import Any

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q
from django.utils import timezone

from apps.documents.models import Document
from apps.equipment.models import EquipmentAsset
from apps.organizations.models import Employee, Organization, Workplace


class ImmutableQuerySet(models.QuerySet):
    def update(self, **kwargs: Any) -> int:
        raise ValidationError(
            "Массовое изменение записей оперативного журнала запрещено."
        )

    def delete(self) -> tuple[int, dict[str, int]]:
        raise ValidationError(
            "Физическое удаление записей оперативного журнала запрещено."
        )


ImmutableManager = models.Manager.from_queryset(ImmutableQuerySet)


class EntryForm(models.TextChoices):
    FREE_TEXT = "FREE_TEXT", "Свободная запись"
    TYPED = "TYPED", "Типизированная запись"


class OperationalJournal(models.Model):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="operational_journals",
        verbose_name="Организация",
    )
    workplace = models.ForeignKey(
        Workplace,
        on_delete=models.PROTECT,
        related_name="operational_journals",
        verbose_name="Рабочее место",
    )
    code = models.SlugField("Код журнала", max_length=96)
    title = models.CharField("Наименование журнала", max_length=500)
    is_active = models.BooleanField("Действующий", default=True)
    created_at = models.DateTimeField("Создан", auto_now_add=True)

    objects = ImmutableManager()

    class Meta:
        ordering = ("organization__name", "workplace__name", "title")
        constraints = [
            models.UniqueConstraint(
                fields=("organization", "code"),
                name="uniq_operational_journal_code",
            )
        ]
        verbose_name = "оперативный журнал"
        verbose_name_plural = "оперативные журналы"

    def __str__(self) -> str:
        return f"{self.workplace.name}: {self.title}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.code = self.code.strip().lower()
        if self.pk and self.entries.exists():
            original = type(self).objects.get(pk=self.pk)
            protected = ("organization_id", "workplace_id", "code", "title")
            if any(
                getattr(original, field) != getattr(self, field) for field in protected
            ):
                raise ValidationError(
                    "Реквизиты журнала с зарегистрированными записями неизменяемы."
                )
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        raise ValidationError("Физическое удаление оперативного журнала запрещено.")

    def clean(self) -> None:
        super().clean()
        if self.workplace_id and self.workplace.organization_id != self.organization_id:
            raise ValidationError(
                {"workplace": "Рабочее место относится к другой организации."}
            )


class OperationalJournalSequence(models.Model):
    journal = models.OneToOneField(
        OperationalJournal,
        on_delete=models.PROTECT,
        related_name="number_sequence",
        verbose_name="Оперативный журнал",
    )
    last_value = models.PositiveBigIntegerField("Последний номер", default=0)
    updated_at = models.DateTimeField("Изменён", auto_now=True)

    class Meta:
        verbose_name = "нумератор оперативного журнала"
        verbose_name_plural = "нумераторы оперативных журналов"

    def __str__(self) -> str:
        return f"{self.journal}: {self.last_value}"


class OperationalLogEntry(models.Model):
    journal = models.ForeignKey(
        OperationalJournal,
        on_delete=models.PROTECT,
        related_name="entries",
        verbose_name="Оперативный журнал",
    )
    sequence_number = models.PositiveBigIntegerField("Номер записи")
    event_at = models.DateTimeField("Время события", db_index=True)
    registered_at = models.DateTimeField(
        "Время регистрации", default=timezone.now, editable=False
    )
    entry_form = models.CharField(
        "Форма записи",
        max_length=16,
        choices=EntryForm.choices,
        db_index=True,
    )
    type_code = models.SlugField("Код типа", max_length=96, blank=True)
    type_title = models.CharField("Наименование типа", max_length=255, blank=True)
    content = models.TextField("Содержание")
    typed_payload = models.JSONField("Типизированные данные", default=dict, blank=True)
    author = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        related_name="operational_log_entries",
        verbose_name="Автор",
    )
    author_full_name_snapshot = models.CharField(
        "Ф.И.О. автора", max_length=500, editable=False
    )
    author_position_snapshot = models.CharField(
        "Должность автора", max_length=500, editable=False
    )
    author_workplace_snapshot = models.CharField(
        "Рабочее место автора", max_length=500, editable=False
    )
    digest = models.CharField("SHA-256 записи", max_length=64, editable=False)

    objects = ImmutableManager()

    class Meta:
        ordering = ("-sequence_number", "-pk")
        constraints = [
            models.UniqueConstraint(
                fields=("journal", "sequence_number"),
                name="uniq_operational_log_sequence_number",
            ),
            models.CheckConstraint(
                condition=Q(sequence_number__gte=1),
                name="operational_log_sequence_positive",
            ),
            models.CheckConstraint(
                condition=Q(event_at__lte=F("registered_at")),
                name="operational_log_event_not_after_registration",
            ),
        ]
        indexes = [
            models.Index(fields=("journal", "-sequence_number")),
            models.Index(fields=("journal", "event_at")),
        ]
        verbose_name = "запись оперативного журнала"
        verbose_name_plural = "записи оперативного журнала"

    def __str__(self) -> str:
        return f"{self.journal} · запись № {self.sequence_number}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.pk:
            raise ValidationError(
                "Зарегистрированная запись оперативного журнала неизменяема."
            )
        self.type_code = self.type_code.strip().lower()
        self.type_title = self.type_title.strip()
        self.content = self.content.strip()
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        raise ValidationError(
            "Физическое удаление записи оперативного журнала запрещено."
        )

    def clean(self) -> None:
        super().clean()
        errors: dict[str, str] = {}
        if (
            self.author_id
            and self.author.organization_id != self.journal.organization_id
        ):
            errors["author"] = "Автор относится к другой организации."
        if self.event_at and self.registered_at and self.event_at > self.registered_at:
            errors["event_at"] = (
                "Время события не может быть позже времени регистрации."
            )
        if not self.content.strip():
            errors["content"] = "Содержание записи обязательно."
        if not isinstance(self.typed_payload, dict):
            errors["typed_payload"] = "Типизированные данные должны быть JSON-объектом."
        if len(self.digest) != 64:
            errors["digest"] = "Требуется SHA-256 зарегистрированной записи."
        if self.entry_form == EntryForm.FREE_TEXT:
            if self.type_code or self.type_title or self.typed_payload:
                errors["entry_form"] = (
                    "Свободная запись не должна содержать типизированные реквизиты."
                )
        elif self.entry_form == EntryForm.TYPED:
            if not self.type_code:
                errors["type_code"] = "Для типизированной записи требуется код типа."
            if not self.type_title:
                errors["type_title"] = (
                    "Для типизированной записи требуется наименование типа."
                )
        if errors:
            raise ValidationError(errors)


class OperationalLogEquipmentLink(models.Model):
    entry = models.ForeignKey(
        OperationalLogEntry,
        on_delete=models.PROTECT,
        related_name="equipment_links",
        verbose_name="Запись журнала",
    )
    equipment = models.ForeignKey(
        EquipmentAsset,
        on_delete=models.PROTECT,
        related_name="operational_log_links",
        verbose_name="Оборудование",
    )
    equipment_code_snapshot = models.CharField(
        "Код оборудования", max_length=96, editable=False
    )
    dispatcher_name_snapshot = models.CharField(
        "Диспетчерское наименование",
        max_length=1000,
        editable=False,
    )
    site_name_snapshot = models.CharField(
        "Энергообъект", max_length=500, editable=False
    )

    objects = ImmutableManager()

    class Meta:
        ordering = ("entry", "dispatcher_name_snapshot", "equipment_code_snapshot")
        constraints = [
            models.UniqueConstraint(
                fields=("entry", "equipment"),
                name="uniq_operational_log_entry_equipment",
            )
        ]
        verbose_name = "связь записи журнала с оборудованием"
        verbose_name_plural = "связи записей журнала с оборудованием"

    def __str__(self) -> str:
        return f"{self.entry} → {self.dispatcher_name_snapshot}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.pk:
            raise ValidationError("Снимок связи с оборудованием неизменяем.")
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        raise ValidationError("Физическое удаление связи с оборудованием запрещено.")

    def clean(self) -> None:
        super().clean()
        if (
            self.equipment_id
            and self.equipment.organization_id != self.entry.journal.organization_id
        ):
            raise ValidationError(
                {"equipment": "Оборудование относится к другой организации."}
            )


class OperationalLogDocumentLink(models.Model):
    entry = models.ForeignKey(
        OperationalLogEntry,
        on_delete=models.PROTECT,
        related_name="document_links",
        verbose_name="Запись журнала",
    )
    document = models.ForeignKey(
        Document,
        on_delete=models.PROTECT,
        related_name="operational_log_links",
        verbose_name="Документ",
    )
    registration_number_snapshot = models.CharField(
        "Регистрационный номер",
        max_length=96,
        editable=False,
    )
    title_snapshot = models.CharField(
        "Заголовок документа", max_length=500, editable=False
    )

    objects = ImmutableManager()

    class Meta:
        ordering = ("entry", "registration_number_snapshot")
        constraints = [
            models.UniqueConstraint(
                fields=("entry", "document"),
                name="uniq_operational_log_entry_document",
            )
        ]
        verbose_name = "связь записи журнала с документом"
        verbose_name_plural = "связи записей журнала с документами"

    def __str__(self) -> str:
        return f"{self.entry} → {self.registration_number_snapshot}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.pk:
            raise ValidationError("Снимок связи с документом неизменяем.")
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        raise ValidationError("Физическое удаление связи с документом запрещено.")

    def clean(self) -> None:
        super().clean()
        errors: dict[str, str] = {}
        if self.document_id:
            if self.document.organization_id != self.entry.journal.organization_id:
                errors["document"] = "Документ относится к другой организации."
            elif self.document.status != Document.Status.REGISTERED:
                errors["document"] = (
                    "В журнале можно ссылаться только на зарегистрированный документ."
                )
        if errors:
            raise ValidationError(errors)


class OperationalLogAuditEvent(models.Model):
    class EventType(models.TextChoices):
        ENTRY_REGISTERED = "ENTRY_REGISTERED", "Запись зарегистрирована"

    entry = models.ForeignKey(
        OperationalLogEntry,
        on_delete=models.PROTECT,
        related_name="audit_events",
        verbose_name="Запись журнала",
    )
    event_type = models.CharField("Событие", max_length=32, choices=EventType.choices)
    actor = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        related_name="operational_log_audit_events",
        verbose_name="Сотрудник",
    )
    event_at = models.DateTimeField(
        "Время события", default=timezone.now, editable=False
    )
    snapshot = models.JSONField("Снимок записи", default=dict, editable=False)
    digest = models.CharField("SHA-256 события", max_length=64, editable=False)

    objects = ImmutableManager()

    class Meta:
        ordering = ("-event_at", "-pk")
        constraints = [
            models.UniqueConstraint(
                fields=("entry", "event_type"),
                name="uniq_operational_log_entry_event",
            )
        ]
        verbose_name = "событие оперативного журнала"
        verbose_name_plural = "события оперативного журнала"

    def __str__(self) -> str:
        return f"{self.get_event_type_display()}: {self.entry}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.pk:
            raise ValidationError("Событие аудита оперативного журнала неизменяемо.")
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        raise ValidationError("Физическое удаление события аудита запрещено.")

    def clean(self) -> None:
        super().clean()
        errors: dict[str, str] = {}
        if (
            self.actor_id
            and self.actor.organization_id != self.entry.journal.organization_id
        ):
            errors["actor"] = "Сотрудник относится к другой организации."
        if not isinstance(self.snapshot, dict):
            errors["snapshot"] = "Снимок должен быть JSON-объектом."
        if len(self.digest) != 64:
            errors["digest"] = "Требуется SHA-256 события аудита."
        if errors:
            raise ValidationError(errors)
