from __future__ import annotations

from datetime import date

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from apps.dispatching.models import ManagementRevision, SupervisionRevision
from apps.equipment.models import EnergySite, EquipmentAlias, EquipmentAsset
from apps.imports.models import (
    DataProfile,
    PowerSystemAssetOccurrence,
    PowerSystemSourceRevision,
)
from apps.imports.power_system import (
    build_power_system_publication_preview,
    decide_power_system_duplicate_group,
    decide_power_system_occurrence,
    publish_power_system_revision,
    reanalyze_power_system_revision,
    stage_power_system_package,
)
from apps.organizations.models import (
    Division,
    Employee,
    Organization,
    Position,
    Role,
    RoleAssignment,
)

from .power_system_package import synthetic_power_system_package


class PowerSystemAssetImporterTests(TestCase):
    password = "Power-System-2026!"

    def setUp(self):
        self.organization = Organization.objects.create(
            code="PS-ORG",
            name="Синтетическая организация",
        )
        division = Division.objects.create(
            organization=self.organization,
            code="PS-DIV",
            name="Оперативная служба",
        )
        position = Position.objects.create(
            organization=self.organization,
            code="PS-POS",
            name="Администратор справочников",
        )
        self.user = get_user_model().objects.create_user(
            username="power-system-publisher",
            password=self.password,
        )
        self.employee = Employee.objects.create(
            organization=self.organization,
            division=division,
            position=position,
            user=self.user,
            personnel_number="PS-001",
            last_name="Тестов",
            first_name="Импорт",
            employment_start=date(2026, 1, 1),
        )
        role, _created = Role.objects.get_or_create(
            code="organization_admin",
            defaults={
                "name": "Администратор справочников",
                "description": "Контролируемая публикация справочников.",
                "is_system": True,
            },
        )
        RoleAssignment.objects.create(
            employee=self.employee,
            role=role,
            valid_from=date(2026, 1, 1),
        )
        self.profile = DataProfile.default_for_organization(self.organization)

    def stage(self):
        return stage_power_system_package(
            uploaded_file=synthetic_power_system_package(),
            employee=self.employee,
            data_profile=self.profile,
            source_reference="Синтетический перечень объектов диспетчеризации",
            source_approval_status=PowerSystemSourceRevision.SourceApprovalStatus.DRAFT,
        )

    def test_stage_is_idempotent_and_keeps_conflict_in_row_quarantine(self):
        revision, created = self.stage()
        self.assertTrue(created)
        self.assertEqual(revision.total_occurrences, 9)
        self.assertEqual(revision.ready_count, 8)
        self.assertEqual(revision.blocked_count, 1)
        blocked = revision.asset_occurrences.get(occurrence_id="SYN-BLOCKED")
        self.assertEqual(blocked.review_status, PowerSystemAssetOccurrence.ReviewStatus.BLOCKED)
        self.assertEqual(EquipmentAsset.objects.count(), 0)

        duplicate, duplicate_created = self.stage()
        self.assertFalse(duplicate_created)
        self.assertEqual(duplicate.pk, revision.pk)
        self.assertEqual(PowerSystemSourceRevision.objects.count(), 1)

    def test_hierarchy_is_recovered_from_semantic_context_not_broken_source_path(self):
        revision, _created = self.stage()
        rows = {
            row.occurrence_id: row
            for row in revision.asset_occurrences.filter(
                occurrence_id__in=(
                    "SYN-SITE",
                    "SYN-35KV",
                    "SYN-KTP-1",
                    "SYN-OPU",
                    "SYN-WTG-GROUP",
                    "SYN-WTG-1",
                    "SYN-LINE-35",
                )
            )
        }
        self.assertEqual(rows["SYN-KTP-1"].parent_external_key, rows["SYN-35KV"].external_key)
        self.assertEqual(rows["SYN-OPU"].parent_external_key, rows["SYN-SITE"].external_key)
        self.assertEqual(rows["SYN-LINE-35"].parent_external_key, rows["SYN-35KV"].external_key)
        self.assertEqual(
            rows["SYN-WTG-1"].parent_external_key,
            rows["SYN-WTG-GROUP"].external_key,
        )

    def test_reanalysis_repairs_existing_staging_without_changing_source_values(self):
        revision, _created = self.stage()
        site = revision.asset_occurrences.get(occurrence_id="SYN-SITE")
        ktp = revision.asset_occurrences.get(occurrence_id="SYN-KTP-1")
        original_parent_raw = ktp.parent_raw
        original_path_raw = ktp.hierarchy_path_raw
        PowerSystemAssetOccurrence.objects.filter(pk=ktp.pk).update(
            parent_external_key=site.external_key,
            logical_key="LOGICAL:incorrect-before-repair",
        )

        result = reanalyze_power_system_revision(revision)
        ktp.refresh_from_db()
        voltage = revision.asset_occurrences.get(occurrence_id="SYN-35KV")
        self.assertGreaterEqual(result["parent_changed"], 1)
        self.assertGreaterEqual(result["logical_key_changed"], 1)
        self.assertEqual(ktp.parent_external_key, voltage.external_key)
        self.assertNotEqual(ktp.logical_key, "LOGICAL:incorrect-before-repair")
        self.assertEqual(ktp.parent_raw, original_parent_raw)
        self.assertEqual(ktp.hierarchy_path_raw, original_path_raw)

    def test_manual_decision_is_audited_and_resettable(self):
        revision, _created = self.stage()
        blocked = revision.asset_occurrences.get(occurrence_id="SYN-BLOCKED")
        accepted = decide_power_system_occurrence(
            occurrence=blocked,
            employee=self.employee,
            action="ACCEPT_AS_NEW",
            note="Проверено на синтетическом источнике.",
        )
        self.assertEqual(accepted.review_status, PowerSystemAssetOccurrence.ReviewStatus.READY)
        self.assertEqual(accepted.reviewed_by, self.employee)
        self.assertIsNotNone(accepted.reviewed_at)
        reset = decide_power_system_occurrence(
            occurrence=accepted,
            employee=self.employee,
            action="RESET",
        )
        self.assertEqual(reset.review_status, PowerSystemAssetOccurrence.ReviewStatus.BLOCKED)
        self.assertIsNone(reset.reviewed_by)

    def test_publication_rebuilds_hierarchy_and_separates_management_from_conduct(self):
        revision, _created = self.stage()
        preview = build_power_system_publication_preview(
            revision=revision,
            effective_from=date(2026, 7, 22),
        )
        with self.assertRaises(ValidationError):
            publish_power_system_revision(
                revision=revision,
                actor=self.employee,
                user=self.user,
                password="wrong-password",
                effective_from=date(2026, 7, 22),
                expected_digest=preview.digest,
            )
        publication = publish_power_system_revision(
            revision=revision,
            actor=self.employee,
            user=self.user,
            password=self.password,
            effective_from=date(2026, 7, 22),
            expected_digest=preview.digest,
        )
        revision.refresh_from_db()
        self.assertEqual(revision.status, PowerSystemSourceRevision.Status.PARTIALLY_PUBLISHED)
        self.assertEqual(revision.published_count, 8)
        self.assertEqual(revision.blocked_count, 1)
        self.assertEqual(EnergySite.objects.filter(organization=self.organization).count(), 1)

        voltage = EquipmentAsset.objects.get(
            organization=self.organization,
            technical_name="35 кВ",
        )
        ktp = EquipmentAsset.objects.get(
            organization=self.organization,
            technical_name="КТП-1",
        )
        control_building = EquipmentAsset.objects.get(
            organization=self.organization,
            technical_name="ОПУ ВЭС",
        )
        turbine_group = EquipmentAsset.objects.get(
            organization=self.organization,
            technical_name="ВЭУ",
        )
        turbine = EquipmentAsset.objects.get(
            organization=self.organization,
            technical_name="ВЭУ-1",
        )
        line = EquipmentAsset.objects.get(
            organization=self.organization,
            technical_name="КЛ 35 кВ КТП-1 – КТП-2",
        )
        breaker = EquipmentAsset.objects.get(
            organization=self.organization,
            technical_name="В-35 КТП-1",
        )
        self.assertIsNone(voltage.parent)
        self.assertEqual(ktp.parent, voltage)
        self.assertIsNone(control_building.parent)
        self.assertEqual(control_building.site.name, "Синтетическая ВЭС")
        self.assertEqual(line.parent, voltage)
        self.assertEqual(turbine.parent, turbine_group)
        self.assertEqual(breaker.parent, ktp)
        self.assertEqual(breaker.attributes["source_occurrence_ids"], ["SYN-Q-1"])
        self.assertEqual(EquipmentAlias.objects.get().scope_parent, ktp)
        self.assertEqual(ManagementRevision.objects.count(), 1)
        supervision = SupervisionRevision.objects.get()
        self.assertEqual(supervision.conduct_mode, SupervisionRevision.ConductMode.OPERATIONAL)
        self.assertFalse(supervision.is_information_only)
        self.assertEqual(len(publication.digest), 64)

    def test_detail_defaults_to_attention_and_hides_manual_action_for_ready_rows(self):
        revision, _created = self.stage()
        self.client.force_login(self.user)

        attention = self.client.get(
            reverse("imports:power_system_detail", args=[revision.public_id])
        )
        self.assertContains(attention, "Показаны только строки, требующие решения")
        self.assertContains(attention, "SYN-BLOCKED")
        self.assertNotContains(attention, "SYN-Q-1")
        self.assertContains(attention, "Принять решение")

        ready = self.client.get(
            reverse("imports:power_system_detail", args=[revision.public_id]),
            {"status": PowerSystemAssetOccurrence.ReviewStatus.READY},
        )
        self.assertContains(ready, "SYN-Q-1")
        self.assertContains(ready, "Ручное действие не требуется")
        self.assertNotContains(ready, "Принять решение")

    def test_issue_descriptions_are_localized_for_user_interface(self):
        revision, _created = self.stage()
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("imports:power_system_detail", args=[revision.public_id])
        )
        self.assertContains(response, "Повторное представление КЛ 35 кВ")
        self.assertContains(response, "Кандидат на объединение")
        self.assertContains(response, "после ручной проверки")
        self.assertNotContains(response, "source-occurrence")
        self.assertNotContains(response, "Merge candidate")
        self.assertNotContains(response, "staging external authority references")

    def test_repair6_normalizes_shot_and_separates_root_from_orphan(self):
        revision, created = stage_power_system_package(
            uploaded_file=synthetic_power_system_package(
                filename="synthetic-repair6.zip",
                include_repair6_cases=True,
            ),
            employee=self.employee,
            data_profile=self.profile,
            source_reference="Синтетический пакет Repair 6",
            source_approval_status=PowerSystemSourceRevision.SourceApprovalStatus.DRAFT,
        )
        self.assertTrue(created)
        shot = revision.asset_occurrences.get(occurrence_id="SYN-SHOT-1")
        site = revision.asset_occurrences.get(occurrence_id="SYN-SITE")
        ktp = revision.asset_occurrences.get(occurrence_id="SYN-KTP-1")
        self.assertEqual(shot.asset_type_code, "dc_distribution_board")
        self.assertEqual(shot.asset_type_name, "Щит или шкаф оперативного постоянного тока")
        self.assertEqual(shot.classification_confidence, "HIGH")
        self.assertEqual(shot.review_status, PowerSystemAssetOccurrence.ReviewStatus.READY)
        self.assertEqual(
            shot.source_flags["controlled_type_normalization"],
            "SHOT_EXACT_UNDER_KTP",
        )
        self.assertEqual(
            shot.source_flags["source_asset_type_proposed"],
            "other_equipment",
        )
        self.assertEqual(shot.parent_external_key, ktp.external_key)
        shpt = revision.asset_occurrences.get(occurrence_id="SYN-SHPT-1")
        self.assertEqual(shpt.asset_type_code, shot.asset_type_code)
        self.assertEqual(shpt.asset_type_name, shot.asset_type_name)
        self.assertEqual(shpt.source_flags["dc_equipment_designation"], "ЩПТ")
        self.assertEqual(shot.source_flags["dc_equipment_designation"], "ШОТ")
        self.assertEqual(site.parent_external_key, "")

        result = reanalyze_power_system_revision(revision)
        self.assertEqual(result["root_without_parent"], 1)
        self.assertEqual(result.get("orphan_parent", 0), 0)

    def test_duplicate_group_decision_merges_to_selected_primary(self):
        revision, _created = stage_power_system_package(
            uploaded_file=synthetic_power_system_package(
                filename="synthetic-groups.zip",
                include_repair6_cases=True,
            ),
            employee=self.employee,
            data_profile=self.profile,
            source_reference="Синтетические группы",
            source_approval_status=PowerSystemSourceRevision.SourceApprovalStatus.DRAFT,
        )
        rows = decide_power_system_duplicate_group(
            revision=revision,
            employee=self.employee,
            duplicate_group="SYN_DUP_1",
            action="MERGE",
            primary_occurrence_id="SYN-DUP-A",
            note="Синтетическое объединение пары.",
        )
        primary = next(row for row in rows if row.occurrence_id == "SYN-DUP-A")
        secondary = next(row for row in rows if row.occurrence_id == "SYN-DUP-B")
        self.assertEqual(
            primary.review_decision,
            PowerSystemAssetOccurrence.ReviewDecision.ACCEPT_AS_NEW,
        )
        self.assertEqual(
            secondary.review_decision,
            PowerSystemAssetOccurrence.ReviewDecision.MERGE_WITH,
        )
        self.assertEqual(secondary.merge_target_id, primary.pk)
        self.assertEqual(primary.effective_logical_key, primary.logical_key)
        self.assertEqual(primary.effective_logical_key, secondary.effective_logical_key)
        self.assertEqual(
            primary.review_status,
            PowerSystemAssetOccurrence.ReviewStatus.READY,
        )
        self.assertEqual(
            secondary.review_status,
            PowerSystemAssetOccurrence.ReviewStatus.READY,
        )

        preview = build_power_system_publication_preview(
            revision=revision,
            effective_from=date(2026, 7, 22),
        )
        self.assertEqual(preview.summary["orphan_rows"], 0)
        self.assertEqual(preview.summary["dc_control_equipment_rows"], 2)
        self.assertEqual(preview.summary["shot_rows"], 1)
        self.assertEqual(preview.summary["shpt_rows"], 1)
        self.assertIn("\n  ", preview.canonical_json_pretty)
        self.assertEqual(preview.summary["duplicate_groups_pending"], 0)

        publish_power_system_revision(
            revision=revision,
            actor=self.employee,
            user=self.user,
            password=self.password,
            effective_from=date(2026, 7, 22),
            expected_digest=preview.digest,
        )
        merged = EquipmentAsset.objects.get(
            organization=self.organization,
            technical_name="КЛ 35 кВ Синтетическая 1 цепь",
        )
        self.assertEqual(
            merged.attributes["source_occurrence_ids"],
            ["SYN-DUP-A", "SYN-DUP-B"],
        )
        shot_asset = EquipmentAsset.objects.get(
            organization=self.organization,
            technical_name="ШОТ",
        )
        self.assertEqual(shot_asset.equipment_type.code, "dc_distribution_board")
        self.assertEqual(
            shot_asset.equipment_type.name,
            "Щит или шкаф оперативного постоянного тока",
        )
        self.assertEqual(shot_asset.attributes["dc_equipment_designation"], "ШОТ")
        shpt_asset = EquipmentAsset.objects.get(
            organization=self.organization,
            technical_name="ЩПТ-1",
        )
        self.assertEqual(shpt_asset.equipment_type_id, shot_asset.equipment_type_id)
        self.assertEqual(shpt_asset.attributes["dc_equipment_designation"], "ЩПТ")

    def test_grouped_review_view_uses_detected_candidates_instead_of_free_text(self):
        revision, _created = stage_power_system_package(
            uploaded_file=synthetic_power_system_package(
                filename="synthetic-group-ui.zip",
                include_repair6_cases=True,
            ),
            employee=self.employee,
            data_profile=self.profile,
            source_reference="Синтетический интерфейс групп",
            source_approval_status=PowerSystemSourceRevision.SourceApprovalStatus.DRAFT,
        )
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("imports:power_system_detail", args=[revision.public_id])
        )
        self.assertContains(response, "СГРУППИРОВАННАЯ ПРОВЕРКА")
        self.assertContains(response, "SYN-DUP-A")
        self.assertContains(response, "SYN-DUP-B")
        self.assertContains(response, 'name="primary_occurrence_id"')
        self.assertContains(response, "Оборудование оперативного постоянного тока")
        self.assertContains(response, "Обозначение ШОТ")
        self.assertContains(response, "Обозначение ЩПТ")
        self.assertContains(response, "Отдельные строки вне групп")
        self.assertContains(response, "SYN-BLOCKED")
        self.assertNotContains(
            response,
            "Все спорные строки распределены по группам",
        )
        revision.asset_occurrences.filter(occurrence_id="SYN-BLOCKED").update(
            review_status=PowerSystemAssetOccurrence.ReviewStatus.EXCLUDED,
        )
        grouped_only_response = self.client.get(
            reverse("imports:power_system_detail", args=[revision.public_id])
        )
        self.assertContains(
            grouped_only_response,
            "Все спорные строки распределены по группам",
        )
        self.assertContains(response, "Потерянные родители")
        self.assertNotContains(response, "Идентификатор исходной строки")
        self.assertNotContains(response, 'placeholder="Идентификатор')

        publication = self.client.get(
            reverse("imports:power_system_publication", args=[revision.public_id])
        )
        self.assertContains(publication, "Оборудование ОПТ")
        self.assertContains(publication, "ШОТ")
        self.assertContains(publication, "ЩПТ")
        self.assertContains(publication, "Неизменяемый технический состав публикации")
        self.assertContains(publication, 'class="technical-only ps-canonical-snapshot"')
        self.assertContains(publication, "Скачать канонический JSON")
        self.assertNotContains(publication, "\n  &quot;effective_from&quot;")
        self.assertNotContains(publication, "preview.canonical_json_pretty")
        snapshot_download = self.client.get(
            reverse(
                "imports:power_system_snapshot_download",
                args=[revision.public_id],
            )
        )
        self.assertEqual(snapshot_download.status_code, 200)
        snapshot_post = self.client.post(
            reverse(
                "imports:power_system_snapshot_download",
                args=[revision.public_id],
            )
        )
        self.assertEqual(snapshot_post.status_code, 405)
        self.assertEqual(
            snapshot_download["Content-Type"],
            "application/json; charset=utf-8",
        )
        self.assertIn("attachment;", snapshot_download["Content-Disposition"])
        self.assertEqual(snapshot_download["Cache-Control"], "no-store")
        self.assertEqual(snapshot_download["X-Content-Type-Options"], "nosniff")
        self.assertEqual(
            snapshot_download["X-Content-SHA256"],
            __import__("hashlib").sha256(snapshot_download.content).hexdigest(),
        )
        self.assertContains(publication, snapshot_download["X-Content-SHA256"])


    def test_views_expose_staging_without_publishing(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("imports:power_system_upload"),
            {
                "data_profile": self.profile.pk,
                "source_reference": "Синтетический перечень",
                "source_approval_status": PowerSystemSourceRevision.SourceApprovalStatus.DRAFT,
                "source_file": synthetic_power_system_package(),
            },
        )
        self.assertEqual(response.status_code, 302)
        revision = PowerSystemSourceRevision.objects.get()
        self.assertEqual(EquipmentAsset.objects.count(), 0)
        detail = self.client.get(
            reverse("imports:power_system_detail", args=[revision.public_id])
        )
        self.assertContains(detail, "Требуют решения")
        self.assertContains(detail, "SYN-BLOCKED")
        self.assertContains(detail, "Заблокирована")
