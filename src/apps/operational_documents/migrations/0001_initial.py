# Generated manually for Patch 011.7 — Operational Documentation Core.

import uuid

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("documents", "0004_normative_registry"),
        ("equipment", "0002_patch_011_5_power_system_asset_importer"),
        ("organizations", "0007_personnel_qualifications_and_operational_rights"),
    ]

    operations = [
        migrations.CreateModel(
            name="OperationalDocumentType",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name="Публичный идентификатор")),
                ("code", models.SlugField(max_length=64, verbose_name="Код")),
                ("name", models.CharField(max_length=255, verbose_name="Наименование")),
                ("short_name", models.CharField(blank=True, max_length=120, verbose_name="Краткое наименование")),
                ("description", models.TextField(blank=True, verbose_name="Описание")),
                ("is_active", models.BooleanField(default=True, verbose_name="Действующий")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создан")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Изменён")),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="created_operational_document_types", to="organizations.employee", verbose_name="Создал")),
                ("organization", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="operational_document_types", to="organizations.organization", verbose_name="Организация")),
            ],
            options={
                "verbose_name": "тип оперативного документа",
                "verbose_name_plural": "типы оперативных документов",
                "ordering": ("name", "code"),
            },
        ),
        migrations.CreateModel(
            name="OperationalDocumentTypeRevision",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name="Публичный идентификатор")),
                ("revision_number", models.PositiveIntegerField(verbose_name="Номер редакции")),
                ("status", models.CharField(choices=[("DRAFT", "Черновик"), ("PUBLISHED", "Опубликована"), ("RETIRED", "Выведена из действия")], db_index=True, default="DRAFT", max_length=16, verbose_name="Состояние")),
                ("number_prefix", models.CharField(max_length=24, verbose_name="Префикс номера")),
                ("number_width", models.PositiveSmallIntegerField(default=4, verbose_name="Разрядность номера")),
                ("requires_workplace", models.BooleanField(default=True, verbose_name="Требуется рабочее место")),
                ("field_definitions", models.JSONField(default=list, verbose_name="Поля")),
                ("status_definitions", models.JSONField(default=list, verbose_name="Статусы")),
                ("transition_definitions", models.JSONField(default=list, verbose_name="Переходы")),
                ("participant_role_definitions", models.JSONField(default=list, verbose_name="Роли участников")),
                ("canonical_snapshot", models.JSONField(blank=True, default=dict, verbose_name="Канонический снимок")),
                ("sha256", models.CharField(blank=True, editable=False, max_length=64, verbose_name="SHA-256")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создана")),
                ("published_at", models.DateTimeField(blank=True, null=True, verbose_name="Опубликована")),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="created_operational_document_type_revisions", to="organizations.employee", verbose_name="Создал редакцию")),
                ("document_type", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="revisions", to="operational_documents.operationaldocumenttype", verbose_name="Тип документа")),
                ("published_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="published_operational_document_type_revisions", to="organizations.employee", verbose_name="Опубликовал")),
            ],
            options={
                "verbose_name": "редакция типа оперативного документа",
                "verbose_name_plural": "редакции типов оперативных документов",
                "ordering": ("document_type__name", "-revision_number"),
            },
        ),
        migrations.CreateModel(
            name="OperationalDocumentNumberSequence",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("year", models.PositiveSmallIntegerField(verbose_name="Год")),
                ("last_value", models.PositiveBigIntegerField(default=0, verbose_name="Последнее значение")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Изменён")),
                ("document_type", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="number_sequences", to="operational_documents.operationaldocumenttype", verbose_name="Тип документа")),
            ],
            options={
                "verbose_name": "нумератор оперативных документов",
                "verbose_name_plural": "нумераторы оперативных документов",
            },
        ),
        migrations.CreateModel(
            name="OperationalDocumentRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name="Публичный идентификатор")),
                ("sequence_year", models.PositiveSmallIntegerField(verbose_name="Год нумерации")),
                ("sequence_value", models.PositiveBigIntegerField(verbose_name="Порядковый номер")),
                ("registration_number", models.CharField(max_length=128, verbose_name="Регистрационный номер")),
                ("title", models.CharField(max_length=500, verbose_name="Заголовок")),
                ("summary", models.TextField(blank=True, verbose_name="Краткое содержание")),
                ("workplace_name_snapshot", models.CharField(blank=True, editable=False, max_length=500, verbose_name="Снимок рабочего места")),
                ("event_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now, verbose_name="Время события")),
                ("status_code", models.CharField(db_index=True, max_length=64, verbose_name="Код состояния")),
                ("status_name_snapshot", models.CharField(max_length=255, verbose_name="Наименование состояния")),
                ("status_is_terminal", models.BooleanField(db_index=True, default=False, verbose_name="Конечное состояние")),
                ("field_values", models.JSONField(default=dict, verbose_name="Значения полей")),
                ("search_text", models.TextField(blank=True, editable=False, verbose_name="Поисковый текст")),
                ("created_by_full_name_snapshot", models.CharField(editable=False, max_length=500, verbose_name="Ф.И.О. создателя")),
                ("created_by_position_snapshot", models.CharField(editable=False, max_length=500, verbose_name="Должность создателя")),
                ("created_by_division_snapshot", models.CharField(editable=False, max_length=500, verbose_name="Подразделение создателя")),
                ("version", models.PositiveBigIntegerField(default=1, verbose_name="Версия")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создана")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Изменена")),
                ("closed_at", models.DateTimeField(blank=True, null=True, verbose_name="Закрыта")),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="created_operational_document_records", to="organizations.employee", verbose_name="Создал")),
                ("document_type", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="records", to="operational_documents.operationaldocumenttype", verbose_name="Тип документа")),
                ("organization", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="operational_document_records", to="organizations.organization", verbose_name="Организация")),
                ("schema_revision", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="records", to="operational_documents.operationaldocumenttyperevision", verbose_name="Редакция структуры")),
                ("updated_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="updated_operational_document_records", to="organizations.employee", verbose_name="Последним изменил")),
                ("workplace", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="operational_document_records", to="organizations.workplace", verbose_name="Рабочее место")),
            ],
            options={
                "verbose_name": "запись оперативной документации",
                "verbose_name_plural": "записи оперативной документации",
                "ordering": ("-event_at", "-pk"),
            },
        ),
        migrations.CreateModel(
            name="OperationalDocumentParticipant",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("role_code", models.CharField(max_length=64, verbose_name="Код роли")),
                ("role_name_snapshot", models.CharField(max_length=255, verbose_name="Наименование роли")),
                ("employee_full_name_snapshot", models.CharField(max_length=500, verbose_name="Ф.И.О.")),
                ("employee_position_snapshot", models.CharField(max_length=500, verbose_name="Должность")),
                ("employee_division_snapshot", models.CharField(max_length=500, verbose_name="Подразделение")),
                ("employee_workplace_snapshot", models.CharField(blank=True, max_length=500, verbose_name="Рабочее место")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создан")),
                ("employee", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="operational_document_participations", to="organizations.employee", verbose_name="Сотрудник")),
                ("record", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="participants", to="operational_documents.operationaldocumentrecord", verbose_name="Запись")),
            ],
            options={
                "verbose_name": "участник оперативной записи",
                "verbose_name_plural": "участники оперативной записи",
                "ordering": ("role_name_snapshot", "employee_full_name_snapshot"),
            },
        ),
        migrations.CreateModel(
            name="OperationalDocumentEquipmentLink",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("equipment_code_snapshot", models.CharField(max_length=96, verbose_name="Код оборудования")),
                ("dispatcher_name_snapshot", models.CharField(max_length=500, verbose_name="Диспетчерское наименование")),
                ("site_name_snapshot", models.CharField(max_length=500, verbose_name="Энергообъект")),
                ("equipment_type_snapshot", models.CharField(max_length=255, verbose_name="Вид оборудования")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создана")),
                ("equipment", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="operational_document_links", to="equipment.equipmentasset", verbose_name="Оборудование")),
                ("record", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="equipment_links", to="operational_documents.operationaldocumentrecord", verbose_name="Запись")),
            ],
            options={
                "verbose_name": "связь оперативной записи с оборудованием",
                "verbose_name_plural": "связи оперативных записей с оборудованием",
                "ordering": ("dispatcher_name_snapshot", "equipment_code_snapshot"),
            },
        ),
        migrations.CreateModel(
            name="OperationalDocumentExternalDocumentLink",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("link_type", models.CharField(choices=[("BASIS", "Документ-основание"), ("ATTACHMENT", "Связанный документ"), ("RESULT", "Результирующий документ")], default="BASIS", max_length=16, verbose_name="Вид связи")),
                ("registration_number_snapshot", models.CharField(blank=True, max_length=128, verbose_name="Номер документа")),
                ("title_snapshot", models.CharField(max_length=500, verbose_name="Заголовок документа")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создана")),
                ("document", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="operational_document_links", to="documents.document", verbose_name="Документ")),
                ("record", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="document_links", to="operational_documents.operationaldocumentrecord", verbose_name="Запись")),
            ],
            options={
                "verbose_name": "связь оперативной записи с документом",
                "verbose_name_plural": "связи оперативных записей с документами",
                "ordering": ("link_type", "registration_number_snapshot", "title_snapshot"),
            },
        ),
        migrations.CreateModel(
            name="OperationalDocumentRelation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("relation_type", models.CharField(choices=[("BASIS", "Основание"), ("RESULT", "Результат"), ("RELATED", "Связано"), ("CONTINUES", "Продолжает"), ("SUPERSEDES", "Заменяет")], default="RELATED", max_length=16, verbose_name="Вид связи")),
                ("relation_name_snapshot", models.CharField(max_length=255, verbose_name="Наименование связи")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создана")),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="created_operational_document_relations", to="organizations.employee", verbose_name="Создал связь")),
                ("source_record", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="outgoing_relations", to="operational_documents.operationaldocumentrecord", verbose_name="Исходная запись")),
                ("target_record", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="incoming_relations", to="operational_documents.operationaldocumentrecord", verbose_name="Связанная запись")),
            ],
            options={
                "verbose_name": "связь оперативных записей",
                "verbose_name_plural": "связи оперативных записей",
                "ordering": ("relation_type", "target_record__event_at"),
            },
        ),
        migrations.CreateModel(
            name="OperationalDocumentRecordRevision",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("revision_number", models.PositiveBigIntegerField(verbose_name="Номер редакции")),
                ("action", models.CharField(choices=[("CREATED", "Создание"), ("UPDATED", "Изменение"), ("TRANSITION", "Переход состояния")], max_length=16, verbose_name="Действие")),
                ("status_code_snapshot", models.CharField(max_length=64, verbose_name="Код состояния")),
                ("status_name_snapshot", models.CharField(max_length=255, verbose_name="Наименование состояния")),
                ("snapshot", models.JSONField(verbose_name="Канонический снимок")),
                ("sha256", models.CharField(max_length=64, verbose_name="SHA-256")),
                ("comment", models.TextField(blank=True, verbose_name="Комментарий")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создана")),
                ("actor", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="operational_document_record_revisions", to="organizations.employee", verbose_name="Автор редакции")),
                ("record", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="revisions", to="operational_documents.operationaldocumentrecord", verbose_name="Запись")),
            ],
            options={
                "verbose_name": "редакция оперативной записи",
                "verbose_name_plural": "редакции оперативных записей",
                "ordering": ("-revision_number", "-pk"),
            },
        ),
        migrations.CreateModel(
            name="OperationalDocumentAuditEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("event_type", models.CharField(db_index=True, max_length=64, verbose_name="Событие")),
                ("entity_type", models.CharField(max_length=64, verbose_name="Тип сущности")),
                ("entity_id", models.CharField(max_length=128, verbose_name="Идентификатор сущности")),
                ("payload", models.JSONField(blank=True, default=dict, verbose_name="Данные события")),
                ("occurred_at", models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="Время")),
                ("actor", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="operational_document_audit_events", to="organizations.employee", verbose_name="Инициатор")),
                ("document_type", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="audit_events", to="operational_documents.operationaldocumenttype", verbose_name="Тип документа")),
                ("organization", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="operational_document_audit_events", to="organizations.organization", verbose_name="Организация")),
                ("record", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="audit_events", to="operational_documents.operationaldocumentrecord", verbose_name="Запись")),
            ],
            options={
                "verbose_name": "событие аудита оперативной документации",
                "verbose_name_plural": "события аудита оперативной документации",
                "ordering": ("-occurred_at", "-pk"),
            },
        ),
        migrations.AddConstraint(
            model_name="operationaldocumenttype",
            constraint=models.UniqueConstraint(fields=("organization", "code"), name="uniq_opdoc_type_code_per_org"),
        ),
        migrations.AddConstraint(
            model_name="operationaldocumenttyperevision",
            constraint=models.UniqueConstraint(fields=("document_type", "revision_number"), name="uniq_opdoc_type_revision_number"),
        ),
        migrations.AddConstraint(
            model_name="operationaldocumenttyperevision",
            constraint=models.CheckConstraint(condition=models.Q(("revision_number__gte", 1)), name="opdoc_type_revision_positive"),
        ),
        migrations.AddConstraint(
            model_name="operationaldocumenttyperevision",
            constraint=models.CheckConstraint(condition=models.Q(("number_width__gte", 1), ("number_width__lte", 12)), name="opdoc_number_width_range"),
        ),
        migrations.AddConstraint(
            model_name="operationaldocumentnumbersequence",
            constraint=models.UniqueConstraint(fields=("document_type", "year"), name="uniq_opdoc_sequence_type_year"),
        ),
        migrations.AddConstraint(
            model_name="operationaldocumentrecord",
            constraint=models.UniqueConstraint(fields=("organization", "registration_number"), name="uniq_opdoc_registration_number_org"),
        ),
        migrations.AddConstraint(
            model_name="operationaldocumentrecord",
            constraint=models.UniqueConstraint(fields=("document_type", "sequence_year", "sequence_value"), name="uniq_opdoc_sequence_components"),
        ),
        migrations.AddConstraint(
            model_name="operationaldocumentrecord",
            constraint=models.CheckConstraint(condition=models.Q(("version__gte", 1)), name="opdoc_record_version_positive"),
        ),
        migrations.AddConstraint(
            model_name="operationaldocumentrecord",
            constraint=models.CheckConstraint(condition=models.Q(models.Q(("closed_at__isnull", False), ("status_is_terminal", True)), models.Q(("closed_at__isnull", True), ("status_is_terminal", False)), _connector="OR"), name="opdoc_terminal_closed_consistent"),
        ),
        migrations.AddConstraint(
            model_name="operationaldocumentparticipant",
            constraint=models.UniqueConstraint(fields=("record", "role_code", "employee"), name="uniq_opdoc_participant_role_employee"),
        ),
        migrations.AddConstraint(
            model_name="operationaldocumentequipmentlink",
            constraint=models.UniqueConstraint(fields=("record", "equipment"), name="uniq_opdoc_record_equipment"),
        ),
        migrations.AddConstraint(
            model_name="operationaldocumentexternaldocumentlink",
            constraint=models.UniqueConstraint(fields=("record", "document", "link_type"), name="uniq_opdoc_record_document_link"),
        ),
        migrations.AddConstraint(
            model_name="operationaldocumentrelation",
            constraint=models.UniqueConstraint(fields=("source_record", "target_record", "relation_type"), name="uniq_opdoc_record_relation"),
        ),
        migrations.AddConstraint(
            model_name="operationaldocumentrelation",
            constraint=models.CheckConstraint(condition=models.Q(("source_record", models.F("target_record")), _negated=True), name="opdoc_relation_not_self"),
        ),
        migrations.AddConstraint(
            model_name="operationaldocumentrecordrevision",
            constraint=models.UniqueConstraint(fields=("record", "revision_number"), name="uniq_opdoc_record_revision_number"),
        ),
        migrations.AddIndex(
            model_name="operationaldocumentrecord",
            index=models.Index(fields=["organization", "document_type", "status_code", "event_at"], name="opdoc_registry_filter_idx"),
        ),
        migrations.AddIndex(
            model_name="operationaldocumentrecord",
            index=models.Index(fields=["organization", "workplace", "event_at"], name="opdoc_workplace_time_idx"),
        ),
        migrations.AddIndex(
            model_name="operationaldocumentauditevent",
            index=models.Index(fields=["organization", "event_type", "occurred_at"], name="opdoc_audit_lookup_idx"),
        ),
    ]
