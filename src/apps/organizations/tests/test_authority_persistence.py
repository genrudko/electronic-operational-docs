from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from apps.organizations.authority import PersonnelRelationKind
from apps.organizations.authority_models import (
    AuthorityBasisStatus,
    AuthorityDecision,
    AuthorityEvaluationRecord,
    AuthorityScopeKind,
    ExternalPersonnelEngagement,
    ExternalPersonnelRelationKind,
    OperationalAuthorityGrant,
    OperationalAuthoritySubstitution,
)
from apps.organizations.authority_services import evaluate_and_record_authority
from apps.organizations.models import (
    Division,
    Employee,
    EmployeeOperationalRight,
    EmployeeQualification,
    OperationalRightDefinition,
    Organization,
    Position,
    Role,
    RoleAssignment,
    Substitution,
    Workplace,
)

MOMENT = datetime(2026, 8, 2, 8, 30, tzinfo=UTC)
START = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
END = datetime(2026, 12, 31, 23, 59, tzinfo=UTC)
SOURCE_SHA = "a" * 64


class AuthorityPersistenceTests(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.organization = Organization.objects.create(
            code="HOST",
            name="Принимающая организация",
            short_name="HOST",
        )
        cls.external_organization = Organization.objects.create(
            code="HOME",
            name="Направляющая организация",
            short_name="HOME",
        )
        cls.division = Division.objects.create(
            organization=cls.organization,
            code="OPS",
            name="Оперативная служба",
        )
        cls.external_division = Division.objects.create(
            organization=cls.external_organization,
            code="EXT",
            name="Подрядное подразделение",
        )
        cls.position = Position.objects.create(
            organization=cls.organization,
            code="SHIFT",
            name="Начальник смены",
            is_operational=True,
        )
        cls.external_position = Position.objects.create(
            organization=cls.external_organization,
            code="CONTRACTOR",
            name="Специалист подрядчика",
            is_operational=True,
        )
        cls.workplace = Workplace.objects.create(
            organization=cls.organization,
            division=cls.division,
            code="CTRL",
            name="Щит управления",
        )
        cls.external_workplace = Workplace.objects.create(
            organization=cls.external_organization,
            division=cls.external_division,
            code="EXT-WP",
            name="Рабочее место подрядчика",
        )
        cls.employee = Employee.objects.create(
            organization=cls.organization,
            division=cls.division,
            position=cls.position,
            workplace=cls.workplace,
            personnel_number="HOST-001",
            last_name="Иванов",
            first_name="Иван",
            middle_name="Иванович",
            employment_start=date(2025, 1, 1),
        )
        cls.replaced_employee = Employee.objects.create(
            organization=cls.organization,
            division=cls.division,
            position=cls.position,
            workplace=cls.workplace,
            personnel_number="HOST-002",
            last_name="Петров",
            first_name="Пётр",
            middle_name="Петрович",
            employment_start=date(2025, 1, 1),
        )
        cls.external_employee = Employee.objects.create(
            organization=cls.external_organization,
            division=cls.external_division,
            position=cls.external_position,
            workplace=cls.external_workplace,
            personnel_number="HOME-001",
            last_name="Сидоров",
            first_name="Сидор",
            middle_name="Сидорович",
            employment_start=date(2025, 1, 1),
        )
        cls.right_definition = OperationalRightDefinition.objects.get(
            code="switching_operation"
        )

    def create_grant(
        self,
        *,
        employee: Employee | None = None,
        basis_status: str = AuthorityBasisStatus.CONFIRMED,
        allow_substitution: bool = False,
        source_operational_right: EmployeeOperationalRight | None = None,
    ) -> OperationalAuthorityGrant:
        return OperationalAuthorityGrant.objects.create(
            organization=self.organization,
            employee=employee or self.employee,
            right_definition=self.right_definition,
            action_code="switching.execute",
            scope_kind=AuthorityScopeKind.ENERGY_SITE,
            scope_reference="site-17",
            scope_label="Кочубеевская ВЭС",
            granting_organization=self.organization,
            basis_status=basis_status,
            basis_reference="ORDER-17/2026-R1",
            source_ids=["REF-OD-051", "SRC-DEC-STAGE2"],
            source_operational_right=source_operational_right,
            valid_from=START,
            valid_until=END,
            allow_substitution=allow_substitution,
            created_by=self.employee,
        )

    def evaluate(
        self,
        *,
        employee: Employee | None = None,
        occurred_at: datetime = MOMENT,
        required_qualification_codes: tuple[str, ...] = (),
        external_relation_kind: PersonnelRelationKind | None = None,
        previous_evaluation: AuthorityEvaluationRecord | None = None,
    ) -> AuthorityEvaluationRecord:
        return evaluate_and_record_authority(
            employee=employee or self.employee,
            organization=self.organization,
            action_code="switching.execute",
            occurred_at=occurred_at,
            scope_kind=AuthorityScopeKind.ENERGY_SITE,
            scope_reference="site-17",
            scope_label="Кочубеевская ВЭС",
            subject_type="switching_document",
            subject_id="SW-2026-17",
            required_qualification_codes=required_qualification_codes,
            external_relation_kind=external_relation_kind,
            recorded_by=self.employee,
            previous_evaluation=previous_evaluation,
        )

    def test_confirmed_structured_grant_creates_allow_snapshot(self) -> None:
        grant = self.create_grant()

        record = self.evaluate()

        self.assertEqual(record.decision, AuthorityDecision.ALLOW)
        self.assertEqual(record.matched_grant, grant)
        self.assertEqual(record.reasons, ["EXPLICIT_GRANT"])
        self.assertEqual(len(record.digest), 64)
        self.assertEqual(record.snapshot["grant"]["grant_id"], str(grant.public_id))
        self.assertEqual(record.snapshot["request"]["subject_id"], "SW-2026-17")

    def test_position_and_application_role_without_grant_are_denied(self) -> None:
        role = Role.objects.create(code="registry_admin", name="Администратор справочников")
        RoleAssignment.objects.create(
            employee=self.employee,
            role=role,
            valid_from=date(2026, 1, 1),
        )

        record = self.evaluate()

        self.assertEqual(record.decision, AuthorityDecision.DENY)
        self.assertIn("NO_MATCHING_GRANT", record.reasons)
        self.assertEqual(record.snapshot["actor"]["position"], "Начальник смены")
        self.assertEqual(record.snapshot["actor"]["application_roles"], ["REGISTRY_ADMIN"])

    def test_verify_basis_never_becomes_allow(self) -> None:
        self.create_grant(basis_status=AuthorityBasisStatus.VERIFY)

        record = self.evaluate()

        self.assertEqual(record.decision, AuthorityDecision.VERIFY)
        self.assertIn("BASIS_VERIFY", record.reasons)
        self.assertIsNotNone(record.matched_grant)

    def test_imported_positive_marker_requires_separate_structured_grant(self) -> None:
        imported = EmployeeOperationalRight.objects.create(
            employee=self.employee,
            right_definition=self.right_definition,
            qualifier="до 110 кВ",
            scope_text="Кочубеевская ВЭС",
            source_marker="+",
            source_reference="Исходная матрица",
            source_file_sha256=SOURCE_SHA,
            source_row_number=17,
            valid_from=date(2026, 1, 1),
        )

        without_grant = self.evaluate()
        self.create_grant(
            basis_status=AuthorityBasisStatus.VERIFY,
            source_operational_right=imported,
        )
        with_unconfirmed_grant = self.evaluate(occurred_at=MOMENT + timedelta(seconds=1))

        self.assertEqual(without_grant.decision, AuthorityDecision.DENY)
        self.assertEqual(with_unconfirmed_grant.decision, AuthorityDecision.VERIFY)

    def test_required_qualification_is_checked_on_actual_actor(self) -> None:
        self.create_grant()
        EmployeeQualification.objects.create(
            employee=self.employee,
            personnel_category="оперативный персонал",
            electrical_safety_group="IV",
            voltage_scope="до и выше 1000 В",
            valid_from=date(2026, 1, 1),
            source_reference="SYNTHETIC-QUALIFICATION",
            source_file_sha256=SOURCE_SHA,
            source_row_number=18,
        )

        allowed = self.evaluate(
            required_qualification_codes=("ELECTRICAL_SAFETY_GROUP:IV",)
        )
        denied = self.evaluate(
            occurred_at=MOMENT + timedelta(seconds=1),
            required_qualification_codes=("ELECTRICAL_SAFETY_GROUP:V",),
        )

        self.assertEqual(allowed.decision, AuthorityDecision.ALLOW)
        self.assertEqual(denied.decision, AuthorityDecision.DENY)
        self.assertIn("QUALIFICATION_MISSING", denied.reasons)

    def test_external_personnel_requires_host_engagement(self) -> None:
        self.create_grant(employee=self.external_employee)

        denied = self.evaluate(
            employee=self.external_employee,
            external_relation_kind=PersonnelRelationKind.CONTRACTOR,
        )
        ExternalPersonnelEngagement.objects.create(
            employee=self.external_employee,
            home_organization=self.external_organization,
            host_organization=self.organization,
            relation_kind=ExternalPersonnelRelationKind.CONTRACTOR,
            scope_kind=AuthorityScopeKind.ENERGY_SITE,
            scope_reference="site-17",
            scope_label="Кочубеевская ВЭС",
            valid_from=START,
            valid_until=END,
            basis_status=AuthorityBasisStatus.CONFIRMED,
            basis_reference="CONTRACTOR-ADMISSION-17",
            source_ids=["REF-OD-052"],
            created_by=self.employee,
        )
        allowed = self.evaluate(
            employee=self.external_employee,
            occurred_at=MOMENT + timedelta(seconds=1),
        )

        self.assertEqual(denied.decision, AuthorityDecision.DENY)
        self.assertIn("EXTERNAL_ENGAGEMENT_REQUIRED", denied.reasons)
        self.assertEqual(allowed.decision, AuthorityDecision.ALLOW)

    def test_substitution_transfers_only_explicit_action_and_scope(self) -> None:
        self.create_grant(
            employee=self.replaced_employee,
            allow_substitution=True,
        )
        base = Substitution.objects.create(
            replaced_employee=self.replaced_employee,
            substitute_employee=self.employee,
            valid_from=date(2026, 8, 1),
            valid_until=date(2026, 8, 3),
            reason="SYNTHETIC-SUBSTITUTION",
        )
        OperationalAuthoritySubstitution.objects.create(
            substitution=base,
            organization=self.organization,
            action_codes=["switching.execute"],
            scope_kind=AuthorityScopeKind.ENERGY_SITE,
            scope_reference="site-17",
            scope_label="Кочубеевская ВЭС",
            basis_status=AuthorityBasisStatus.CONFIRMED,
            basis_reference="ORDER-SUB-17",
            source_ids=["REF-OD-051"],
            created_by=self.employee,
        )

        record = self.evaluate()

        self.assertEqual(record.decision, AuthorityDecision.ALLOW)
        self.assertIsNotNone(record.snapshot["substitution"])
        self.assertEqual(
            record.snapshot["substitution"]["substitute_employee_id"],
            self.employee.id,
        )

    def test_evaluation_record_is_append_only(self) -> None:
        self.create_grant()
        record = self.evaluate()

        record.subject_id = "CHANGED"
        with self.assertRaises(ValidationError):
            record.save()
        with self.assertRaises(ValidationError):
            record.delete()
        with self.assertRaises(ValidationError):
            AuthorityEvaluationRecord.objects.filter(pk=record.pk).update(
                decision=AuthorityDecision.DENY
            )
        with self.assertRaises(ValidationError):
            AuthorityEvaluationRecord.objects.filter(pk=record.pk).delete()

    def test_correction_requires_same_subject_and_new_fact(self) -> None:
        self.create_grant(basis_status=AuthorityBasisStatus.VERIFY)
        first = self.evaluate()
        OperationalAuthorityGrant.objects.filter(pk=first.matched_grant_id).update(
            basis_status=AuthorityBasisStatus.CONFIRMED
        )
        second = self.evaluate(
            occurred_at=MOMENT + timedelta(seconds=1),
            previous_evaluation=first,
        )

        self.assertEqual(first.decision, AuthorityDecision.VERIFY)
        self.assertEqual(second.decision, AuthorityDecision.ALLOW)
        self.assertEqual(second.previous_evaluation, first)
        self.assertNotEqual(first.digest, second.digest)

    def test_cross_tenant_grant_and_external_same_org_are_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            ExternalPersonnelEngagement.objects.create(
                employee=self.employee,
                home_organization=self.organization,
                host_organization=self.organization,
                relation_kind=ExternalPersonnelRelationKind.CONTRACTOR,
                scope_kind=AuthorityScopeKind.ORGANIZATION,
                scope_reference=str(self.organization.id),
                valid_from=START,
                basis_status=AuthorityBasisStatus.CONFIRMED,
                basis_reference="INVALID",
                source_ids=["REF-OD-052"],
            )

        grant = OperationalAuthorityGrant(
            organization=self.organization,
            employee=self.employee,
            right_definition=self.right_definition,
            action_code="switching.execute",
            scope_kind=AuthorityScopeKind.ORGANIZATION,
            scope_reference=str(self.external_organization.id),
            granting_organization=self.organization,
            basis_status=AuthorityBasisStatus.CONFIRMED,
            basis_reference="INVALID-SCOPE",
            source_ids=["REF-OD-051"],
            valid_from=START,
        )
        with self.assertRaises(ValidationError):
            grant.save()

    def test_database_constraints_reject_invalid_window(self) -> None:
        with self.assertRaises((ValidationError, IntegrityError)):
            OperationalAuthorityGrant.objects.create(
                organization=self.organization,
                employee=self.employee,
                right_definition=self.right_definition,
                action_code="switching.execute",
                scope_kind=AuthorityScopeKind.ENERGY_SITE,
                scope_reference="site-17",
                granting_organization=self.organization,
                basis_status=AuthorityBasisStatus.CONFIRMED,
                basis_reference="INVALID-WINDOW",
                source_ids=["REF-OD-051"],
                valid_from=END,
                valid_until=START,
            )
