# Generated manually for DEFECT-001.

import uuid

import django.db.models.deletion
from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("operational_documents", "0001_initial"),
        ("operational_log", "0001_initial"),
        ("organizations", "0007_personnel_qualifications_and_operational_rights"),
    ]

    operations = [
        migrations.CreateModel(
            name="EquipmentDefectVolume",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "public_id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        unique=True,
                        verbose_name="Публичный идентификатор",
                    ),
                ),
                ("sequence_number", models.PositiveIntegerField(verbose_name="Номер тома")),
                (
                    "organization_name_snapshot",
                    models.CharField(
                        editable=False,
                        max_length=500,
                        verbose_name="Наименование организации",
                    ),
                ),
                (
                    "workplace_name_snapshot",
                    models.CharField(
                        editable=False,
                        max_length=500,
                        verbose_name="Наименование ВЭС / ПС",
                    ),
                ),
                (
                    "division_name_snapshot",
                    models.CharField(
                        blank=True,
                        editable=False,
                        max_length=500,
                        verbose_name="Наименование ЦОТУиЭ ВЭС",
                    ),
                ),
                ("started_on", models.DateField(verbose_name="Дата начала")),
                (
                    "closed_on",
                    models.DateField(
                        blank=True,
                        null=True,
                        verbose_name="Дата окончания",
                    ),
                ),
                (
                    "accepts_new_records",
                    models.BooleanField(
                        default=True,
                        verbose_name="Принимает новые записи",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создан")),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="created_equipment_defect_volumes",
                        to="organizations.employee",
                        verbose_name="Создал том",
                    ),
                ),
                (
                    "organization",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="equipment_defect_volumes",
                        to="organizations.organization",
                        verbose_name="Организация",
                    ),
                ),
                (
                    "workplace",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="equipment_defect_volumes",
                        to="organizations.workplace",
                        verbose_name="Рабочее место",
                    ),
                ),
            ],
            options={
                "verbose_name": "том журнала дефектов",
                "verbose_name_plural": "тома журнала дефектов",
                "ordering": ("organization", "workplace", "-sequence_number"),
            },
        ),
        migrations.CreateModel(
            name="EquipmentDefectContext",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "presentation_key",
                    models.CharField(
                        blank=True,
                        editable=False,
                        max_length=96,
                        null=True,
                        unique=True,
                        verbose_name="Ключ презентационных данных",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создан")),
                (
                    "record",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="equipment_defect_context",
                        to="operational_documents.operationaldocumentrecord",
                        verbose_name="Запись журнала дефектов",
                    ),
                ),
                (
                    "volume",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="defect_contexts",
                        to="equipment_defects.equipmentdefectvolume",
                        verbose_name="Исходный том",
                    ),
                ),
            ],
            options={
                "verbose_name": "предметный контекст дефекта",
                "verbose_name_plural": "предметные контексты дефектов",
                "ordering": ("record__sequence_year", "record__sequence_value"),
            },
        ),
        migrations.CreateModel(
            name="EquipmentDefectActionEvidence",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "public_id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        unique=True,
                        verbose_name="Публичный идентификатор",
                    ),
                ),
                (
                    "action_code",
                    models.CharField(
                        choices=[
                            ("REGISTERED", "Дефект зарегистрирован"),
                            ("DEADLINE_CONFIRMED", "Срок подтверждён"),
                            ("DEADLINE_EXTENDED", "Срок устранения продлен"),
                            ("RESOLUTION_CONFIRMED", "Устранение подтверждено"),
                            ("ACKNOWLEDGED", "Оперативный персонал ознакомлен"),
                            ("CLOSED", "Дефект закрыт"),
                        ],
                        db_index=True,
                        max_length=32,
                        verbose_name="Действие",
                    ),
                ),
                (
                    "actor_full_name_snapshot",
                    models.CharField(
                        editable=False,
                        max_length=500,
                        verbose_name="Ф.И.О.",
                    ),
                ),
                (
                    "actor_position_snapshot",
                    models.CharField(
                        editable=False,
                        max_length=500,
                        verbose_name="Должность",
                    ),
                ),
                (
                    "actor_division_snapshot",
                    models.CharField(
                        editable=False,
                        max_length=500,
                        verbose_name="Подразделение",
                    ),
                ),
                (
                    "occurred_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        db_index=True,
                        verbose_name="Время действия",
                    ),
                ),
                ("record_version", models.PositiveBigIntegerField(verbose_name="Версия записи")),
                (
                    "previous_deadline",
                    models.DateTimeField(
                        blank=True,
                        null=True,
                        verbose_name="Прежний срок",
                    ),
                ),
                (
                    "new_deadline",
                    models.DateTimeField(
                        blank=True,
                        null=True,
                        verbose_name="Новый срок",
                    ),
                ),
                (
                    "result",
                    models.CharField(
                        default="CONFIRMED",
                        max_length=64,
                        verbose_name="Результат",
                    ),
                ),
                ("comment", models.TextField(blank=True, verbose_name="Причина или комментарий")),
                ("canonical_snapshot", models.JSONField(verbose_name="Канонический снимок")),
                (
                    "sha256",
                    models.CharField(
                        editable=False,
                        max_length=64,
                        verbose_name="SHA-256",
                    ),
                ),
                (
                    "actor",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="equipment_defect_actions",
                        to="organizations.employee",
                        verbose_name="Сотрудник",
                    ),
                ),
                (
                    "record",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="equipment_defect_actions",
                        to="operational_documents.operationaldocumentrecord",
                        verbose_name="Запись журнала дефектов",
                    ),
                ),
                (
                    "record_revision",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="equipment_defect_actions",
                        to="operational_documents.operationaldocumentrecordrevision",
                        verbose_name="Редакция записи",
                    ),
                ),
            ],
            options={
                "verbose_name": "подтверждение действия по дефекту",
                "verbose_name_plural": "подтверждения действий по дефектам",
                "ordering": ("occurred_at", "pk"),
            },
        ),
        migrations.CreateModel(
            name="EquipmentDefectOperationalLogLink",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "entry_sequence_snapshot",
                    models.PositiveBigIntegerField(verbose_name="Номер исходной записи"),
                ),
                (
                    "entry_event_at_snapshot",
                    models.DateTimeField(verbose_name="Время исходного события"),
                ),
                (
                    "entry_content_snapshot",
                    models.TextField(verbose_name="Краткое содержание исходной записи"),
                ),
                (
                    "entry_digest_snapshot",
                    models.CharField(
                        max_length=64,
                        verbose_name="SHA-256 исходной записи",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создана")),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="created_equipment_defect_operational_log_links",
                        to="organizations.employee",
                        verbose_name="Создал связь",
                    ),
                ),
                (
                    "operational_log_entry",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="equipment_defect_links",
                        to="operational_log.operationallogentry",
                        verbose_name="Запись оперативного журнала",
                    ),
                ),
                (
                    "record",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="equipment_defect_operational_log_link",
                        to="operational_documents.operationaldocumentrecord",
                        verbose_name="Дефект",
                    ),
                ),
            ],
            options={
                "verbose_name": "связь дефекта с оперативным журналом",
                "verbose_name_plural": "связи дефектов с оперативным журналом",
                "ordering": ("operational_log_entry__journal", "entry_sequence_snapshot"),
            },
        ),
        migrations.AddConstraint(
            model_name="equipmentdefectvolume",
            constraint=models.UniqueConstraint(
                fields=("organization", "workplace", "sequence_number"),
                name="uniq_defect_volume_number",
            ),
        ),
        migrations.AddConstraint(
            model_name="equipmentdefectvolume",
            constraint=models.UniqueConstraint(
                condition=Q(accepts_new_records=True),
                fields=("organization", "workplace"),
                name="uniq_open_defect_volume",
            ),
        ),
        migrations.AddConstraint(
            model_name="equipmentdefectvolume",
            constraint=models.CheckConstraint(
                condition=Q(sequence_number__gte=1),
                name="defect_volume_number_positive",
            ),
        ),
        migrations.AddConstraint(
            model_name="equipmentdefectvolume",
            constraint=models.CheckConstraint(
                condition=Q(closed_on__isnull=True)
                | Q(closed_on__gte=models.F("started_on")),
                name="defect_volume_dates_valid",
            ),
        ),
        migrations.AddIndex(
            model_name="equipmentdefectactionevidence",
            index=models.Index(
                fields=["record", "action_code", "occurred_at"],
                name="defect_action_lookup_idx",
            ),
        ),
        migrations.AddConstraint(
            model_name="equipmentdefectactionevidence",
            constraint=models.CheckConstraint(
                condition=Q(record_version__gte=1),
                name="defect_action_version_positive",
            ),
        ),
    ]
