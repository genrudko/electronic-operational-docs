from datetime import date

from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.organizations.models import Organization

from ..models import (
    EnergySite,
    EquipmentAlias,
    EquipmentAsset,
    EquipmentNameRevision,
    EquipmentRelation,
    EquipmentType,
)
from .helpers import EquipmentDemoMixin


class EquipmentRegistryModelTests(EquipmentDemoMixin, TestCase):
    def test_asset_rejects_site_from_other_organization(self):
        other = Organization.objects.create(code="OTHER", name="Другая организация")
        site = EnergySite.objects.create(
            organization=other,
            code="other-site",
            name="Другой объект",
            site_type=EnergySite.SiteType.OTHER,
        )
        asset = EquipmentAsset(
            organization=self.employee.organization,
            site=site,
            equipment_type=EquipmentType.objects.first(),
            code="CROSS-ORG",
            technical_name="Ошибочное оборудование",
        )
        with self.assertRaises(ValidationError):
            asset.full_clean()

    def test_asset_rejects_parent_from_other_site(self):
        parent = EquipmentAsset.objects.get(code="DEMO-GRID-BAY-01")
        asset = EquipmentAsset(
            organization=self.employee.organization,
            site=EnergySite.objects.get(code="demo-wpp"),
            equipment_type=EquipmentType.objects.first(),
            parent=parent,
            code="WRONG-PARENT",
            technical_name="Ошибочный дочерний объект",
        )
        self.assertNotEqual(parent.site_id, asset.site_id)
        with self.assertRaises(ValidationError):
            asset.full_clean()

    def test_asset_rejects_hierarchy_cycle(self):
        site = EnergySite.objects.get(code="demo-wpp")
        equipment_type = EquipmentType.objects.get(code="switchgear")
        first = EquipmentAsset.objects.create(
            organization=self.employee.organization,
            site=site,
            equipment_type=equipment_type,
            code="CYCLE-A",
            technical_name="Цикл А",
        )
        second = EquipmentAsset.objects.create(
            organization=self.employee.organization,
            site=site,
            equipment_type=equipment_type,
            parent=first,
            code="CYCLE-B",
            technical_name="Цикл Б",
        )
        first.parent = second
        with self.assertRaises(ValidationError):
            first.full_clean()

    def test_published_dispatcher_name_is_immutable(self):
        revision = EquipmentNameRevision.objects.filter(
            equipment=self.ktp
        ).order_by("-revision_number").first()
        revision.dispatcher_name = "Недопустимое изменение"
        with self.assertRaises(ValidationError):
            revision.save()

    def test_asset_structure_is_immutable_after_name_publication(self):
        self.ktp.technical_name = "Недопустимое изменение"
        with self.assertRaises(ValidationError):
            self.ktp.save()

    def test_alias_is_append_only(self):
        alias = EquipmentAlias.objects.filter(equipment=self.ktp).first()
        alias.alias = "Недопустимое изменение"
        with self.assertRaises(ValidationError):
            alias.save()

    def test_relation_rejects_self_reference(self):
        relation = EquipmentRelation(
            source_equipment=self.ktp,
            target_equipment=self.ktp,
            relation_type=EquipmentRelation.RelationType.RELATED,
            valid_from=date(2026, 1, 1),
            created_by=self.employee,
        )
        with self.assertRaises(ValidationError):
            relation.full_clean()

    def test_alias_is_normalized_for_search(self):
        alias = EquipmentAlias.objects.get(alias="КТП 1")
        self.assertEqual(alias.normalized_alias, "ктп 1")
