from __future__ import annotations

from typing import Any

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q
from django.utils import timezone

from apps.normatives.models import NormativeDocument
from apps.organizations.models import Employee, Organization, Workplace


class ProtectedQuerySet(models.QuerySet):
    def update(self, **kwargs: Any) -> int:
        raise ValidationError("Массовое изменение перечней документации запрещено.")

    def delete(self) -> tuple[int, dict[str, int]]:
        raise ValidationError("Физическое удаление перечней документации запрещено.")


ProtectedManager = models.Manager.from_queryset(ProtectedQuerySet)


class RevisionStatus(models.TextChoices):
    DRAFT = "DRAFT", "Черновик"
    APPROVED = "APPROVED", "Утверждена"


class SourceKind(models.TextChoices):
    TYPICAL = "TYPICAL", "Типовая позиция"
    LOCAL = "LOCAL", "Локальная позиция"


class RequirementKind(models.TextChoices):
    MANDATORY = "MANDATORY", "Обязательная"
    CONDITIONAL = "CONDITIONAL", "Обязательная при применимости"
    REFERENCE = "REFERENCE", "Справочная"


class StorageForm(models.TextChoices):
    UNKNOWN = "UNKNOWN", "Не определена"
    PAPER = "PAPER", "Бумажная"
    ELECTRONIC = "ELECTRONIC", "Электронная"
    MIXED = "MIXED", "Смешанная"


class ElectronicStorageInterpretation(models.TextChoices):
    INDICATED = "INDICATED", "Электронная форма указана"
    NOT_INDICATED = "NOT_INDICATED", "Электронная форма не указана"
    UNKNOWN = "UNKNOWN", "Не удалось определить"


class WorkplaceDocumentList(models.Model):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="workplace_document_lists",
        verbose_name="Организация",
    )
    workplace = models.ForeignKey(
        Workplace,
        on_delete=models.PROTECT,
        related_name="document_lists",
        verbose_name="Рабочее место",
    )
    code = models.SlugField("Код перечня", max_length=96)
    title = models.CharField("Наименование перечня", max_length=500)
    is_active = models.BooleanField("Используется", default=True)
    created_at = models.DateTimeField("Создан", auto_now_add=True)

    objects = ProtectedManager()

    class Meta:
        ordering = ("organization__name", "workplace__name", "title")
        constraints = [
            models.UniqueConstraint(
                fields=("organization", "code"),
                name="uniq_workplace_document_list_code",
            )
        ]
        verbose_name = "перечень документации рабочего места"
        verbose_name_plural = "перечни документации рабочих мест"

    def __str__(self) -> str:
        return f"{self.workplace.name}: {self.title}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.code = self.code.strip().lower()
        if self.pk and self.revisions.filter(status=RevisionStatus.APPROVED).exists():
            original = type(self).objects.get(pk=self.pk)
            protected = ("organization_id", "workplace_id", "code", "title")
            if any(getattr(original, field) != getattr(self, field) for field in protected):
                raise ValidationError("Реквизиты перечня с утверждённой редакцией неизменяемы.")
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        raise ValidationError("Физическое удаление перечня документации запрещено.")

    def clean(self) -> None:
        super().clean()
        if self.workplace_id and self.workplace.organization_id != self.organization_id:
            raise ValidationError({"workplace": "Рабочее место относится к другой организации."})


class WorkplaceDocumentRevision(models.Model):
    document_list = models.ForeignKey(
        WorkplaceDocumentList,
        on_delete=models.PROTECT,
        related_name="revisions",
        verbose_name="Перечень",
    )
    revision_number = models.PositiveIntegerField("Номер редакции")
    status = models.CharField(
        "Статус",
        max_length=16,
        choices=RevisionStatus.choices,
        default=RevisionStatus.DRAFT,
        db_index=True,
    )
    effective_from = models.DateField("Действует с")
    effective_until = models.DateField("Действует по", null=True, blank=True)
    review_period_months = models.PositiveSmallIntegerField(
        "Периодичность пересмотра, месяцев",
        default=12,
    )
    next_review_date = models.DateField(
        "Следующий пересмотр",
        null=True,
        blank=True,
        editable=False,
        db_index=True,
    )
    change_summary = models.TextField("Описание редакции", blank=True)
    approved_by = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="approved_workplace_document_revisions",
        verbose_name="Утвердил",
    )
    approved_at = models.DateTimeField("Утверждена", null=True, blank=True, editable=False)
    digest = models.CharField("SHA-256 редакции", max_length=64, blank=True, editable=False)
    created_at = models.DateTimeField("Создана", auto_now_add=True)

    objects = ProtectedManager()

    class Meta:
        ordering = ("document_list", "-revision_number")
        constraints = [
            models.UniqueConstraint(
                fields=("document_list", "revision_number"),
                name="uniq_workplace_document_revision_number",
            ),
            models.CheckConstraint(
                condition=Q(effective_until__isnull=True) | Q(effective_until__gte=F("effective_from")),
                name="workplace_document_revision_valid_window",
            ),
            models.CheckConstraint(
                condition=(
                    Q(
                        status="DRAFT",
                        approved_at__isnull=True,
                        approved_by__isnull=True,
                        next_review_date__isnull=True,
                        digest="",
                    )
                    | (
                        Q(
                            status="APPROVED",
                            approved_at__isnull=False,
                            approved_by__isnull=False,
                            next_review_date__isnull=False,
                        )
                        & ~Q(digest="")
                    )
                ),
                name="workplace_document_revision_approval_consistent",
            ),
        ]
        verbose_name = "редакция перечня документации"
        verbose_name_plural = "редакции перечней документации"

    def __str__(self) -> str:
        return f"{self.document_list} · редакция № {self.revision_number}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.pk:
            original = type(self).objects.get(pk=self.pk)
            if original.status == RevisionStatus.APPROVED:
                raise ValidationError("Утверждённая редакция перечня неизменяема.")
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        raise ValidationError("Физическое удаление редакции перечня запрещено.")

    def clean(self) -> None:
        super().clean()
        if self.effective_until and self.effective_until < self.effective_from:
            raise ValidationError({"effective_until": "Дата окончания раньше даты начала."})
        if not 1 <= self.review_period_months <= 60:
            raise ValidationError(
                {"review_period_months": "Период пересмотра должен быть от 1 до 60 месяцев."}
            )
        if self.approved_by_id:
            organization_id = self.document_list.organization_id
            if self.approved_by.organization_id != organization_id:
                raise ValidationError({"approved_by": "Утверждающий относится к другой организации."})
        if self.status == RevisionStatus.APPROVED:
            errors: dict[str, str] = {}
            if not self.approved_at:
                errors["approved_at"] = "Требуется серверное время утверждения."
            if not self.approved_by_id:
                errors["approved_by"] = "Требуется утверждающий сотрудник."
            if not self.next_review_date:
                errors["next_review_date"] = "Требуется дата следующего пересмотра."
            if len(self.digest) != 64:
                errors["digest"] = "Требуется SHA-256 утверждённой редакции."
            if errors:
                raise ValidationError(errors)


class WorkplaceDocumentEntry(models.Model):
    revision = models.ForeignKey(
        WorkplaceDocumentRevision,
        on_delete=models.PROTECT,
        related_name="entries",
        verbose_name="Редакция перечня",
    )
    code = models.CharField("Код позиции", max_length=96)
    title = models.CharField("Наименование документации", max_length=500)
    source_kind = models.CharField(
        "Происхождение",
        max_length=16,
        choices=SourceKind.choices,
    )
    requirement_kind = models.CharField(
        "Обязательность",
        max_length=16,
        choices=RequirementKind.choices,
        default=RequirementKind.MANDATORY,
    )
    applicability_text = models.TextField("Применимость", blank=True)
    storage_form = models.CharField(
        "Форма хранения",
        max_length=16,
        choices=StorageForm.choices,
    )
    normative_document = models.ForeignKey(
        NormativeDocument,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="workplace_document_entries",
        verbose_name="Нормативный документ",
    )
    normative_clause = models.CharField("Пункт нормативного документа", max_length=128, blank=True)
    basis_text = models.CharField("Основание", max_length=1000, blank=True)
    notes = models.TextField("Примечание", blank=True)
    source_register_entry_no = models.PositiveIntegerField(
        "Сквозной номер позиции источника",
        null=True,
        blank=True,
    )
    section_no = models.CharField("Номер раздела источника", max_length=32, blank=True)
    section_name = models.CharField("Наименование раздела", max_length=255, blank=True)
    subsection_no = models.CharField("Номер подраздела источника", max_length=32, blank=True)
    subsection_name = models.CharField("Наименование подраздела", max_length=255, blank=True)
    source_document_no = models.CharField("Номер документа в разделе", max_length=64, blank=True)
    document_type_label = models.CharField("Тип документа из источника", max_length=255, blank=True)
    electronic_storage_mark = models.CharField(
        "Отметка электронной формы из источника",
        max_length=16,
        blank=True,
    )
    electronic_storage_interpretation = models.CharField(
        "Интерпретация электронной формы",
        max_length=24,
        choices=ElectronicStorageInterpretation.choices,
        default=ElectronicStorageInterpretation.UNKNOWN,
    )
    review_period_raw = models.CharField("Периодичность из источника", max_length=255, blank=True)
    review_interval_months = models.PositiveSmallIntegerField(
        "Нормализованный период пересмотра, месяцев",
        null=True,
        blank=True,
    )
    approval_date = models.DateField("Дата утверждения позиции", null=True, blank=True)
    approving_role = models.CharField("Должность утвердившего", max_length=255, blank=True)
    approver_name = models.CharField("Утвердивший по источнику", max_length=255, blank=True)
    source_pdf_page = models.PositiveSmallIntegerField("Страница источника", null=True, blank=True)
    display_order = models.PositiveIntegerField("Порядок отображения", default=0)

    objects = ProtectedManager()

    class Meta:
        ordering = ("revision", "display_order", "code")
        constraints = [
            models.UniqueConstraint(
                fields=("revision", "code"),
                name="uniq_workplace_document_entry_code",
            )
        ]
        verbose_name = "позиция перечня документации"
        verbose_name_plural = "позиции перечня документации"

    def __str__(self) -> str:
        return f"{self.code}: {self.title}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.revision.status == RevisionStatus.APPROVED:
            raise ValidationError("Позиции утверждённой редакции неизменяемы.")
        self.code = self.code.strip().upper()
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        raise ValidationError("Физическое удаление позиции перечня запрещено.")

    def clean(self) -> None:
        super().clean()
        if not self.normative_document_id and not self.basis_text.strip():
            raise ValidationError({"basis_text": "Укажите нормативный документ или текстовое основание."})
        if self.normative_document_id:
            document = self.normative_document
            organization_id = self.revision.document_list.organization_id
            if (
                document.scope == NormativeDocument.Scope.LOCAL
                and document.organization_id != organization_id
            ):
                raise ValidationError(
                    {"normative_document": "Локальный документ относится к другой организации."}
                )


class WorkplaceDocumentAuditEvent(models.Model):
    class EventType(models.TextChoices):
        REVISION_APPROVED = "REVISION_APPROVED", "Редакция утверждена"

    document_list = models.ForeignKey(
        WorkplaceDocumentList,
        on_delete=models.PROTECT,
        related_name="audit_events",
        verbose_name="Перечень",
    )
    revision = models.ForeignKey(
        WorkplaceDocumentRevision,
        on_delete=models.PROTECT,
        related_name="audit_events",
        verbose_name="Редакция",
    )
    event_type = models.CharField("Событие", max_length=32, choices=EventType.choices)
    actor = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        related_name="workplace_document_audit_events",
        verbose_name="Сотрудник",
    )
    event_at = models.DateTimeField("Время", default=timezone.now, editable=False)
    snapshot = models.JSONField("Снимок", default=dict, editable=False)
    digest = models.CharField("SHA-256 события", max_length=64, editable=False)

    objects = ProtectedManager()

    class Meta:
        ordering = ("-event_at", "-pk")
        constraints = [
            models.UniqueConstraint(
                fields=("revision", "event_type"),
                name="uniq_workplace_document_revision_event",
            )
        ]
        verbose_name = "событие перечня документации"
        verbose_name_plural = "события перечней документации"

    def __str__(self) -> str:
        return f"{self.get_event_type_display()} · {self.revision}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.pk:
            raise ValidationError("Событие аудита неизменяемо; создайте новое событие.")
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        raise ValidationError("Физическое удаление события аудита запрещено.")

    def clean(self) -> None:
        super().clean()
        organization_id = self.document_list.organization_id
        if self.revision.document_list_id != self.document_list_id:
            raise ValidationError({"revision": "Редакция относится к другому перечню."})
        if self.actor.organization_id != organization_id:
            raise ValidationError({"actor": "Сотрудник относится к другой организации."})
        if len(self.digest) != 64:
            raise ValidationError({"digest": "Для события требуется SHA-256."})
