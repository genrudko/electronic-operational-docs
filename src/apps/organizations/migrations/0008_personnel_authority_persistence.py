import uuid

import django.db.models.deletion
from django.db import migrations, models
from django.db.models import F, Q


class Migration(migrations.Migration):
    dependencies = [
        ("organizations", "0007_personnel_qualifications_and_operational_rights"),
    ]

    operations = [
        migrations.CreateModel(
            name="ExternalPersonnelEngagement",
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
                    "relation_kind",
                    models.CharField(
                        choices=[
                            ("SECONDED", "Командированный персонал"),
                            ("CONTRACTOR", "Подрядный персонал"),
                            ("SYSTEM_OPERATOR", "Персонал системного оператора"),
                        ],
                        max_length=24,
                        verbose_name="Вид внешнего персонала",
                    ),
                ),
                (
                    "scope_kind",
                    models.CharField(
                        choices=[
                            ("ORGANIZATION", "Организация"),
                            ("DIVISION", "Подразделение"),
                            ("WORKPLACE", "Рабочее место"),
                            ("OPERATIONAL_AREA", "Оперативная область"),
                            ("ENERGY_SITE", "Энергообъект"),
                            ("EQUIPMENT", "Оборудование"),
                        ],
                        max_length=24,
                        verbose_name="Вид области допуска",
                    ),
                ),
                (
                    "scope_reference",
                    models.CharField(max_length=255, verbose_name="Идентификатор области допуска"),
                ),
                (
                    "scope_label",
                    models.CharField(
                        blank=True,
                        max_length=500,
                        verbose_name="Наименование области допуска",
                    ),
                ),
                ("valid_from", models.DateTimeField(verbose_name="Допущен с")),
                (
                    "valid_until",
                    models.DateTimeField(blank=True, null=True, verbose_name="Допущен по"),
                ),
                (
                    "basis_status",
                    models.CharField(
                        choices=[
                            ("CONFIRMED", "Основание подтверждено"),
                            ("VERIFY", "Основание требует проверки"),
                            ("REJECTED", "Основание отклонено"),
                        ],
                        default="VERIFY",
                        max_length=16,
                        verbose_name="Статус основания",
                    ),
                ),
                (
                    "basis_reference",
                    models.CharField(max_length=1000, verbose_name="Основание внешнего допуска"),
                ),
                (
                    "source_ids",
                    models.JSONField(default=list, verbose_name="Traceable source IDs"),
                ),
                (
                    "is_active",
                    models.BooleanField(default=True, verbose_name="Действующий внешний допуск"),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создан")),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="created_external_engagements",
                        to="organizations.employee",
                        verbose_name="Зафиксировал",
                    ),
                ),
                (
                    "employee",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="external_engagements",
                        to="organizations.employee",
                        verbose_name="Внешний сотрудник",
                    ),
                ),
                (
                    "home_organization",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="outgoing_external_personnel",
                        to="organizations.organization",
                        verbose_name="Направляющая организация",
                    ),
                ),
                (
                    "host_organization",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="incoming_external_personnel",
                        to="organizations.organization",
                        verbose_name="Принимающая организация",
                    ),
                ),
            ],
            options={
                "verbose_name": "допуск внешнего персонала",
                "verbose_name_plural": "допуски внешнего персонала",
                "ordering": (
                    "host_organization__name",
                    "employee__last_name",
                    "valid_from",
                ),
            },
        ),
        migrations.CreateModel(
            name="OperationalAuthorityGrant",
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
                        db_index=True,
                        max_length=128,
                        verbose_name="Код контролируемого действия",
                    ),
                ),
                (
                    "scope_kind",
                    models.CharField(
                        choices=[
                            ("ORGANIZATION", "Организация"),
                            ("DIVISION", "Подразделение"),
                            ("WORKPLACE", "Рабочее место"),
                            ("OPERATIONAL_AREA", "Оперативная область"),
                            ("ENERGY_SITE", "Энергообъект"),
                            ("EQUIPMENT", "Оборудование"),
                        ],
                        max_length=24,
                        verbose_name="Вид области",
                    ),
                ),
                (
                    "scope_reference",
                    models.CharField(max_length=255, verbose_name="Идентификатор области"),
                ),
                (
                    "scope_label",
                    models.CharField(
                        blank=True,
                        max_length=500,
                        verbose_name="Наименование области",
                    ),
                ),
                (
                    "basis_status",
                    models.CharField(
                        choices=[
                            ("CONFIRMED", "Основание подтверждено"),
                            ("VERIFY", "Основание требует проверки"),
                            ("REJECTED", "Основание отклонено"),
                        ],
                        default="VERIFY",
                        max_length=16,
                        verbose_name="Статус основания",
                    ),
                ),
                (
                    "basis_reference",
                    models.CharField(
                        max_length=1000,
                        verbose_name="Документ-основание и редакция",
                    ),
                ),
                (
                    "source_ids",
                    models.JSONField(default=list, verbose_name="Traceable source IDs"),
                ),
                ("valid_from", models.DateTimeField(verbose_name="Действует с")),
                (
                    "valid_until",
                    models.DateTimeField(blank=True, null=True, verbose_name="Действует по"),
                ),
                (
                    "is_active",
                    models.BooleanField(default=True, verbose_name="Действующее предоставление"),
                ),
                (
                    "allow_substitution",
                    models.BooleanField(default=False, verbose_name="Допускает явное замещение"),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создано")),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="created_authority_grants",
                        to="organizations.employee",
                        verbose_name="Зафиксировал",
                    ),
                ),
                (
                    "employee",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="structured_authority_grants",
                        to="organizations.employee",
                        verbose_name="Лицо, которому предоставлено право",
                    ),
                ),
                (
                    "granting_organization",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="granted_operational_authorities",
                        to="organizations.organization",
                        verbose_name="Организация, предоставившая право",
                    ),
                ),
                (
                    "organization",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="authority_grants",
                        to="organizations.organization",
                        verbose_name="Организация действия",
                    ),
                ),
                (
                    "right_definition",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="structured_grants",
                        to="organizations.operationalrightdefinition",
                        verbose_name="Вид оперативного права",
                    ),
                ),
                (
                    "source_operational_right",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="published_structured_grants",
                        to="organizations.employeeoperationalright",
                        verbose_name="Исходный импортированный факт",
                    ),
                ),
            ],
            options={
                "verbose_name": "структурированное оперативное право",
                "verbose_name_plural": "структурированные оперативные права",
                "ordering": (
                    "employee__last_name",
                    "action_code",
                    "scope_kind",
                    "scope_reference",
                ),
            },
        ),
        migrations.CreateModel(
            name="OperationalAuthoritySubstitution",
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
                    "action_codes",
                    models.JSONField(default=list, verbose_name="Явно разрешённые действия"),
                ),
                (
                    "scope_kind",
                    models.CharField(
                        choices=[
                            ("ORGANIZATION", "Организация"),
                            ("DIVISION", "Подразделение"),
                            ("WORKPLACE", "Рабочее место"),
                            ("OPERATIONAL_AREA", "Оперативная область"),
                            ("ENERGY_SITE", "Энергообъект"),
                            ("EQUIPMENT", "Оборудование"),
                        ],
                        max_length=24,
                        verbose_name="Вид области",
                    ),
                ),
                (
                    "scope_reference",
                    models.CharField(max_length=255, verbose_name="Идентификатор области"),
                ),
                (
                    "scope_label",
                    models.CharField(
                        blank=True,
                        max_length=500,
                        verbose_name="Наименование области",
                    ),
                ),
                (
                    "basis_status",
                    models.CharField(
                        choices=[
                            ("CONFIRMED", "Основание подтверждено"),
                            ("VERIFY", "Основание требует проверки"),
                            ("REJECTED", "Основание отклонено"),
                        ],
                        default="VERIFY",
                        max_length=16,
                        verbose_name="Статус основания",
                    ),
                ),
                (
                    "basis_reference",
                    models.CharField(
                        max_length=1000,
                        verbose_name="Документ-основание и редакция",
                    ),
                ),
                (
                    "source_ids",
                    models.JSONField(default=list, verbose_name="Traceable source IDs"),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        default=True,
                        verbose_name="Действующее ограничение замещения",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создано")),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="created_authority_substitutions",
                        to="organizations.employee",
                        verbose_name="Зафиксировал",
                    ),
                ),
                (
                    "organization",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="authority_substitutions",
                        to="organizations.organization",
                        verbose_name="Организация",
                    ),
                ),
                (
                    "substitution",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="authority_scopes",
                        to="organizations.substitution",
                        verbose_name="Базовое замещение",
                    ),
                ),
            ],
            options={
                "verbose_name": "область оперативных прав при замещении",
                "verbose_name_plural": "области оперативных прав при замещении",
                "ordering": (
                    "-substitution__valid_from",
                    "substitution__substitute_employee__last_name",
                ),
            },
        ),
        migrations.CreateModel(
            name="AuthorityEvaluationRecord",
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
                    models.CharField(db_index=True, max_length=128, verbose_name="Код действия"),
                ),
                (
                    "occurred_at",
                    models.DateTimeField(db_index=True, verbose_name="Момент действия"),
                ),
                (
                    "scope_kind",
                    models.CharField(
                        choices=[
                            ("ORGANIZATION", "Организация"),
                            ("DIVISION", "Подразделение"),
                            ("WORKPLACE", "Рабочее место"),
                            ("OPERATIONAL_AREA", "Оперативная область"),
                            ("ENERGY_SITE", "Энергообъект"),
                            ("EQUIPMENT", "Оборудование"),
                        ],
                        max_length=24,
                        verbose_name="Вид области",
                    ),
                ),
                (
                    "scope_reference",
                    models.CharField(max_length=255, verbose_name="Идентификатор области"),
                ),
                (
                    "scope_label",
                    models.CharField(
                        blank=True,
                        max_length=500,
                        verbose_name="Наименование области",
                    ),
                ),
                (
                    "subject_type",
                    models.CharField(max_length=128, verbose_name="Тип предметного объекта"),
                ),
                (
                    "subject_id",
                    models.CharField(max_length=255, verbose_name="Идентификатор предметного объекта"),
                ),
                (
                    "decision",
                    models.CharField(
                        choices=[
                            ("ALLOW", "Разрешено"),
                            ("DENY", "Запрещено"),
                            ("VERIFY", "Требуется проверка"),
                        ],
                        db_index=True,
                        max_length=16,
                        verbose_name="Результат",
                    ),
                ),
                (
                    "reasons",
                    models.JSONField(default=list, verbose_name="Коды причин"),
                ),
                ("snapshot", models.JSONField(verbose_name="Неизменяемый authority snapshot")),
                (
                    "digest",
                    models.CharField(
                        editable=False,
                        max_length=64,
                        unique=True,
                        verbose_name="SHA-256 authority snapshot",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Зафиксировано")),
                (
                    "actor",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="authority_evaluations",
                        to="organizations.employee",
                        verbose_name="Проверяемое лицо",
                    ),
                ),
                (
                    "matched_grant",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="evaluation_records",
                        to="organizations.operationalauthoritygrant",
                        verbose_name="Использованное предоставление права",
                    ),
                ),
                (
                    "organization",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="authority_evaluations",
                        to="organizations.organization",
                        verbose_name="Организация действия",
                    ),
                ),
                (
                    "previous_evaluation",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="corrections",
                        to="organizations.authorityevaluationrecord",
                        verbose_name="Предыдущий результат",
                    ),
                ),
                (
                    "recorded_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="recorded_authority_evaluations",
                        to="organizations.employee",
                        verbose_name="Зафиксировал",
                    ),
                ),
            ],
            options={
                "verbose_name": "результат проверки оперативного полномочия",
                "verbose_name_plural": "результаты проверки оперативных полномочий",
                "ordering": ("-occurred_at", "-id"),
            },
        ),
        migrations.AddConstraint(
            model_name="externalpersonnelengagement",
            constraint=models.CheckConstraint(
                condition=Q(valid_until__isnull=True) | Q(valid_until__gte=F("valid_from")),
                name="external_engagement_valid_window",
            ),
        ),
        migrations.AddConstraint(
            model_name="externalpersonnelengagement",
            constraint=models.CheckConstraint(
                condition=~Q(home_organization=F("host_organization")),
                name="external_engagement_distinct_orgs",
            ),
        ),
        migrations.AddConstraint(
            model_name="externalpersonnelengagement",
            constraint=models.UniqueConstraint(
                fields=(
                    "employee",
                    "host_organization",
                    "scope_kind",
                    "scope_reference",
                    "valid_from",
                ),
                name="uniq_external_engagement_start",
            ),
        ),
        migrations.AddConstraint(
            model_name="operationalauthoritygrant",
            constraint=models.CheckConstraint(
                condition=Q(valid_until__isnull=True) | Q(valid_until__gte=F("valid_from")),
                name="authority_grant_valid_window",
            ),
        ),
        migrations.AddConstraint(
            model_name="operationalauthoritygrant",
            constraint=models.UniqueConstraint(
                fields=(
                    "employee",
                    "action_code",
                    "scope_kind",
                    "scope_reference",
                    "valid_from",
                    "basis_reference",
                ),
                name="uniq_authority_grant_start_basis",
            ),
        ),
        migrations.AddConstraint(
            model_name="operationalauthoritysubstitution",
            constraint=models.UniqueConstraint(
                fields=("substitution", "scope_kind", "scope_reference"),
                name="uniq_authority_substitution_scope",
            ),
        ),
        migrations.AddConstraint(
            model_name="authorityevaluationrecord",
            constraint=models.UniqueConstraint(
                fields=(
                    "organization",
                    "subject_type",
                    "subject_id",
                    "occurred_at",
                    "digest",
                ),
                name="uniq_authority_evaluation_fact",
            ),
        ),
    ]
