import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("imports", "0006_personnel_operational_authority_importer"),
        ("organizations", "0007_personnel_qualifications_and_operational_rights"),
        ("workplace_docs", "0002_workplace_document_entry_source_metadata"),
    ]

    operations = [
        migrations.CreateModel(
            name="WorkplaceDocumentSourceRevision",
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
                    "source_reference",
                    models.CharField(max_length=1000, verbose_name="Источник или основание"),
                ),
                ("effective_from", models.DateField(verbose_name="Действует с")),
                (
                    "list_review_period_months",
                    models.PositiveSmallIntegerField(
                        default=12,
                        verbose_name="Период пересмотра перечня, месяцев",
                    ),
                ),
                ("original_filename", models.CharField(max_length=255, verbose_name="Имя CSV")),
                ("file_size", models.PositiveBigIntegerField(verbose_name="Размер CSV, байт")),
                ("file_sha256", models.CharField(max_length=64, verbose_name="SHA-256 CSV")),
                ("header_signature", models.CharField(max_length=64, verbose_name="SHA-256 заголовка")),
                (
                    "source_encoding",
                    models.CharField(
                        default="utf-8-sig",
                        max_length=32,
                        verbose_name="Кодировка",
                    ),
                ),
                (
                    "workplace_scope_raw",
                    models.CharField(
                        blank=True,
                        max_length=500,
                        verbose_name="Рабочее место из источника",
                    ),
                ),
                ("manifest", models.JSONField(default=dict, verbose_name="Манифест разбора")),
                ("total_rows", models.PositiveIntegerField(default=0, verbose_name="Позиций")),
                ("section_count", models.PositiveIntegerField(default=0, verbose_name="Разделов")),
                ("ready_rows", models.PositiveIntegerField(default=0, verbose_name="Готовых строк")),
                ("review_rows", models.PositiveIntegerField(default=0, verbose_name="Строк на проверке")),
                (
                    "blocked_rows",
                    models.PositiveIntegerField(
                        default=0,
                        verbose_name="Заблокированных строк",
                    ),
                ),
                ("excluded_rows", models.PositiveIntegerField(default=0, verbose_name="Исключённых строк")),
                (
                    "electronic_indicated_rows",
                    models.PositiveIntegerField(
                        default=0,
                        verbose_name="Строк с указанной электронной формой",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("STAGED", "Подготовлена к проверке"),
                            ("PUBLISHED", "Опубликована"),
                            ("DISCARDED", "Убрана из рабочего списка"),
                        ],
                        db_index=True,
                        default="STAGED",
                        max_length=16,
                        verbose_name="Состояние",
                    ),
                ),
                (
                    "publication_digest",
                    models.CharField(
                        blank=True,
                        editable=False,
                        max_length=64,
                        verbose_name="SHA-256 публикации",
                    ),
                ),
                ("published_at", models.DateTimeField(blank=True, null=True, verbose_name="Опубликовано")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создано")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Изменено")),
                (
                    "discarded_at",
                    models.DateTimeField(
                        blank=True,
                        null=True,
                        verbose_name="Убрано из рабочего списка",
                    ),
                ),
                (
                    "data_profile",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="workplace_document_source_revisions",
                        to="imports.dataprofile",
                        verbose_name="Профиль данных",
                    ),
                ),
                (
                    "matched_workplace",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="matched_workplace_document_source_revisions",
                        to="organizations.workplace",
                        verbose_name="Сопоставленное рабочее место",
                    ),
                ),
                (
                    "organization",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="workplace_document_source_revisions",
                        to="organizations.organization",
                        verbose_name="Организация",
                    ),
                ),
                (
                    "published_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="published_workplace_document_imports",
                        to="organizations.employee",
                        verbose_name="Опубликовал",
                    ),
                ),
                (
                    "target_document_list",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="source_import_revisions",
                        to="workplace_docs.workplacedocumentlist",
                        verbose_name="Созданный перечень",
                    ),
                ),
                (
                    "target_revision",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="source_import_revisions",
                        to="workplace_docs.workplacedocumentrevision",
                        verbose_name="Созданная редакция",
                    ),
                ),
                (
                    "uploaded_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="uploaded_workplace_document_revisions",
                        to="organizations.employee",
                        verbose_name="Загрузил",
                    ),
                ),
            ],
            options={
                "verbose_name": "редакция источника документации рабочего места",
                "verbose_name_plural": "редакции источников документации рабочих мест",
                "ordering": ("-created_at", "-id"),
            },
        ),
        migrations.CreateModel(
            name="WorkplaceDocumentSourceRow",
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
                ("source_row_number", models.PositiveIntegerField(verbose_name="Строка CSV")),
                ("source_index", models.PositiveIntegerField(verbose_name="Технический индекс источника")),
                ("register_entry_no", models.PositiveIntegerField(verbose_name="Сквозной номер позиции")),
                ("section_no", models.CharField(max_length=32, verbose_name="Номер раздела")),
                ("section_name", models.CharField(max_length=255, verbose_name="Наименование раздела")),
                (
                    "subsection_no",
                    models.CharField(
                        blank=True,
                        max_length=32,
                        verbose_name="Номер подраздела",
                    ),
                ),
                (
                    "subsection_name",
                    models.CharField(
                        blank=True,
                        max_length=255,
                        verbose_name="Наименование подраздела",
                    ),
                ),
                (
                    "source_document_no",
                    models.CharField(
                        blank=True,
                        max_length=64,
                        verbose_name="Номер документа в разделе",
                    ),
                ),
                (
                    "document_title_raw",
                    models.CharField(
                        max_length=1000,
                        verbose_name="Наименование документа",
                    ),
                ),
                (
                    "document_type_proposed",
                    models.CharField(
                        blank=True,
                        max_length=255,
                        verbose_name="Предложенный тип",
                    ),
                ),
                (
                    "electronic_storage_mark",
                    models.CharField(
                        max_length=16,
                        verbose_name="Исходная отметка электронной формы",
                    ),
                ),
                (
                    "electronic_storage_interpretation",
                    models.CharField(
                        max_length=24,
                        verbose_name="Интерпретация электронной формы",
                    ),
                ),
                (
                    "review_period_raw",
                    models.CharField(
                        blank=True,
                        max_length=255,
                        verbose_name="Исходная периодичность",
                    ),
                ),
                (
                    "review_interval_years_raw",
                    models.CharField(
                        blank=True,
                        max_length=64,
                        verbose_name="Предложенный период в годах",
                    ),
                ),
                (
                    "review_interval_months",
                    models.PositiveSmallIntegerField(
                        blank=True,
                        null=True,
                        verbose_name="Нормализованный период, месяцев",
                    ),
                ),
                ("approval_date", models.DateField(blank=True, null=True, verbose_name="Дата утверждения")),
                (
                    "approval_date_raw",
                    models.CharField(
                        blank=True,
                        max_length=64,
                        verbose_name="Исходная дата утверждения",
                    ),
                ),
                (
                    "approving_role",
                    models.CharField(
                        blank=True,
                        max_length=255,
                        verbose_name="Должность утвердившего",
                    ),
                ),
                ("approver_name", models.CharField(blank=True, max_length=255, verbose_name="Утвердивший")),
                ("workplace_scope", models.CharField(max_length=500, verbose_name="Рабочее место")),
                (
                    "source_pdf_page",
                    models.PositiveSmallIntegerField(
                        blank=True,
                        null=True,
                        verbose_name="Страница PDF",
                    ),
                ),
                ("source_notes", models.TextField(blank=True, verbose_name="Примечания источника")),
                (
                    "initial_review_status",
                    models.CharField(
                        choices=[
                            ("READY", "Готова"),
                            ("REVIEW_REQUIRED", "Требует проверки"),
                            ("BLOCKED", "Заблокирована"),
                            ("PUBLISHED", "Опубликована"),
                            ("EXCLUDED", "Исключена"),
                        ],
                        max_length=24,
                        verbose_name="Исходное состояние проверки",
                    ),
                ),
                (
                    "review_status",
                    models.CharField(
                        choices=[
                            ("READY", "Готова"),
                            ("REVIEW_REQUIRED", "Требует проверки"),
                            ("BLOCKED", "Заблокирована"),
                            ("PUBLISHED", "Опубликована"),
                            ("EXCLUDED", "Исключена"),
                        ],
                        db_index=True,
                        max_length=24,
                        verbose_name="Состояние проверки",
                    ),
                ),
                (
                    "review_decision",
                    models.CharField(
                        choices=[
                            ("NONE", "Решение не принято"),
                            ("ACCEPT_AS_IS", "Принять исходное значение"),
                            ("EXCLUDE", "Исключить из публикации"),
                        ],
                        default="NONE",
                        max_length=24,
                        verbose_name="Решение",
                    ),
                ),
                ("decision_note", models.TextField(blank=True, verbose_name="Обоснование решения")),
                ("reviewed_at", models.DateTimeField(blank=True, null=True, verbose_name="Проверено")),
                ("issues", models.JSONField(blank=True, default=list, verbose_name="Проблемы строки")),
                ("fingerprint", models.CharField(max_length=64, verbose_name="SHA-256 строки")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создано")),
                (
                    "reviewed_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="reviewed_workplace_document_source_rows",
                        to="organizations.employee",
                        verbose_name="Проверил",
                    ),
                ),
                (
                    "source_revision",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="source_rows",
                        to="imports.workplacedocumentsourcerevision",
                        verbose_name="Редакция источника",
                    ),
                ),
                (
                    "target_entry",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="source_import_rows",
                        to="workplace_docs.workplacedocumententry",
                        verbose_name="Опубликованная позиция",
                    ),
                ),
            ],
            options={
                "verbose_name": "строка источника документации рабочего места",
                "verbose_name_plural": "строки источника документации рабочего места",
                "ordering": ("source_revision", "register_entry_no", "source_index"),
            },
        ),
        migrations.CreateModel(
            name="WorkplaceDocumentPublication",
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
                    "schema_version",
                    models.CharField(
                        default="eod.workplace-document-import.publication.v1",
                        max_length=64,
                        verbose_name="Версия схемы",
                    ),
                ),
                ("canonical_json", models.TextField(verbose_name="Канонический снимок публикации")),
                ("digest", models.CharField(max_length=64, unique=True, verbose_name="SHA-256 публикации")),
                ("result_summary", models.JSONField(default=dict, verbose_name="Итоги публикации")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Опубликовано")),
                (
                    "actor",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="workplace_document_import_publications",
                        to="organizations.employee",
                        verbose_name="Опубликовал",
                    ),
                ),
                (
                    "source_revision",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="publication",
                        to="imports.workplacedocumentsourcerevision",
                        verbose_name="Редакция источника",
                    ),
                ),
            ],
            options={
                "verbose_name": "публикация реестра документации рабочего места",
                "verbose_name_plural": "публикации реестров документации рабочих мест",
                "ordering": ("-created_at", "-id"),
            },
        ),
        migrations.AddConstraint(
            model_name="workplacedocumentsourcerevision",
            constraint=models.UniqueConstraint(
                fields=(
                    "organization",
                    "file_sha256",
                    "source_reference",
                    "effective_from",
                    "list_review_period_months",
                ),
                name="uniq_workdoc_source_context",
            ),
        ),
        migrations.AddIndex(
            model_name="workplacedocumentsourcerevision",
            index=models.Index(
                fields=["organization", "status", "-created_at"],
                name="workdoc_src_status_idx",
            ),
        ),
        migrations.AddConstraint(
            model_name="workplacedocumentsourcerow",
            constraint=models.UniqueConstraint(
                fields=("source_revision", "source_row_number"),
                name="uniq_workdoc_source_row",
            ),
        ),
        migrations.AddIndex(
            model_name="workplacedocumentsourcerow",
            index=models.Index(
                fields=["source_revision", "review_status", "register_entry_no"],
                name="workdoc_row_review_idx",
            ),
        ),
    ]
