from datetime import date

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from ..models import (
    EnergySite,
    EquipmentAsset,
    EquipmentNameRevision,
    EquipmentType,
)
from ..services import (
    build_site_tree,
    dispatcher_name_on,
    hierarchy_path,
    name_history_rows,
    publish_equipment_name_revision,
    resolve_equipment_alias,
    search_equipment,
)
from .helpers import EquipmentDemoMixin


class EquipmentRegistryServiceTests(EquipmentDemoMixin, TestCase):
    def test_historical_dispatcher_name_is_resolved_by_date(self):
        self.assertEqual(
            dispatcher_name_on(self.ktp, date(2025, 6, 1)),
            "КТП-1 Демо-ВЭС",
        )
        self.assertEqual(
            dispatcher_name_on(self.ktp, date(2026, 6, 1)),
            "КТП-01 Демо-ВЭС",
        )

    def test_alias_resolves_equipment(self):
        resolved = resolve_equipment_alias(
            self.employee.organization,
            "  КТП   1 ",
        )
        self.assertEqual(resolved, self.ktp)

    def test_hierarchy_path_contains_ancestors(self):
        path = hierarchy_path(
            EquipmentAsset.objects.get(code="DEMO-RZA-01")
        )
        self.assertIn("РУ 35 кВ", path)
        self.assertIn("ячейка 1", path)
        self.assertIn("РЗА", path)

    def test_name_history_derives_previous_end_date(self):
        rows = name_history_rows(self.ktp)
        old = next(
            row
            for row in rows
            if row["revision"].revision_number == 1
        )
        self.assertEqual(old["effective_until"], date(2025, 12, 31))

    def test_publish_name_revision_creates_sha256(self):
        site = EnergySite.objects.get(code="demo-wpp")
        equipment = EquipmentAsset.objects.create(
            organization=self.employee.organization,
            site=site,
            equipment_type=EquipmentType.objects.get(code="ktp"),
            code="PUBLISH-NAME",
            technical_name="Оборудование для публикации",
        )
        revision = EquipmentNameRevision.objects.create(
            equipment=equipment,
            revision_number=1,
            dispatcher_name="Демонстрационное имя",
            effective_from=timezone.localdate(),
        )
        published = publish_equipment_name_revision(
            revision=revision,
            actor=self.employee,
        )
        self.assertEqual(published.status, "PUBLISHED")
        self.assertEqual(len(published.digest), 64)
        self.assertIsNotNone(published.published_at)

    def test_second_publication_is_rejected(self):
        revision = EquipmentNameRevision.objects.filter(
            equipment=self.ktp
        ).order_by("-revision_number").first()
        with self.assertRaises(ValidationError):
            publish_equipment_name_revision(
                revision=revision,
                actor=self.employee,
            )

    def test_search_finds_historical_alias(self):
        queryset = search_equipment(
            organization=self.employee.organization,
            query="Блочная КТП №1",
        )
        self.assertEqual(list(queryset), [self.ktp])

    def test_site_tree_preserves_parent_before_child(self):
        rows = build_site_tree(EnergySite.objects.get(code="demo-wpp"))
        codes = [row["equipment"].code for row in rows]
        self.assertLess(codes.index("DEMO-RU35"), codes.index("DEMO-RU35-S1"))
        self.assertLess(codes.index("DEMO-RU35-S1"), codes.index("DEMO-CELL-01"))
