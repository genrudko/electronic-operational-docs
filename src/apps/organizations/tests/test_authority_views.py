from __future__ import annotations

from datetime import UTC, date, datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.organizations.authority_models import (
    AuthorityBasisStatus,
    AuthorityScopeKind,
    OperationalAuthorityGrant,
)
from apps.organizations.authority_services import evaluate_and_record_authority
from apps.organizations.models import (
    Division,
    Employee,
    EmployeeOperationalRight,
    OperationalRightDefinition,
    Organization,
    Position,
    Workplace,
)

MOMENT = datetime(2026, 8, 2, 8, 30, tzinfo=UTC)
START = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
END = datetime(2026, 12, 31, 23, 59, tzinfo=UTC)


class AuthorityReadOnlyViewTests(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        user_model = get_user_model()
        cls.user = user_model.objects.create_user(
            username="authority-reviewer",
            password="synthetic-password",
        )
        cls.organization = Organization.objects.create(
            code="AUTH-VIEW",
            name="Синтетическая организация",
            short_name="AUTH-VIEW",
        )
        cls.division = Division.objects.create(
            organization=cls.organization,
            code="OPS",
            name="Оперативная служба",
        )
        cls.position = Position.objects.create(
            organization=cls.organization,
            code="SHIFT",
            name="Начальник смены",
            is_operational=True,
        )
        cls.workplace = Workplace.objects.create(
            organization=cls.organization,
            division=cls.division,
            code="CTRL",
            name="Щит управления",
        )
        cls.employee = Employee.objects.create(
            organization=cls.organization,
            division=cls.division,
            position=cls.position,
            workplace=cls.workplace,
            user=cls.user,
            personnel_number="SYNTHETIC-001",
            last_name="Тестов",
            first_name="Тест",
            middle_name="Тестович",
            employment_start=date(2025, 1, 1),
        )
        cls.right_definition = OperationalRightDefinition.objects.get(
            code="switching_operation"
        )
        cls.source_right = EmployeeOperationalRight.objects.create(
            employee=cls.employee,
            right_definition=cls.right_definition,
            scope_text="Синтетический энергообъект",
            source_marker="+",
            source_reference="SYNTHETIC-SOURCE",
            source_file_sha256="b" * 64,
            source_row_number=1,
            valid_from=date(2026, 1, 1),
        )
        cls.grant = OperationalAuthorityGrant.objects.create(
            organization=cls.organization,
            employee=cls.employee,
            right_definition=cls.right_definition,
            action_code="switching.execute",
            scope_kind=AuthorityScopeKind.ENERGY_SITE,
            scope_reference="synthetic-site",
            scope_label="Синтетический энергообъект",
            granting_organization=cls.organization,
            basis_status=AuthorityBasisStatus.CONFIRMED,
            basis_reference="SYNTHETIC-ORDER-R1",
            source_ids=["REF-OD-051"],
            source_operational_right=cls.source_right,
            valid_from=START,
            valid_until=END,
            created_by=cls.employee,
        )

    def setUp(self) -> None:
        self.client.force_login(self.user)

    def create_evaluation(self):
        return evaluate_and_record_authority(
            employee=self.employee,
            organization=self.organization,
            action_code="switching.execute",
            occurred_at=MOMENT,
            scope_kind=AuthorityScopeKind.ENERGY_SITE,
            scope_reference="synthetic-site",
            scope_label="Синтетический энергообъект",
            subject_type="switching_document",
            subject_id="SYNTHETIC-SW-001",
            recorded_by=self.employee,
        )

    def test_authority_registry_is_authenticated_and_read_only(self) -> None:
        response = self.client.get(reverse("organizations:authority_registry"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Реестр оперативных полномочий")
        self.assertContains(response, "SYNTHETIC-ORDER-R1")
        self.assertContains(response, "Подтверждено")
        self.assertNotContains(response, "<form", html=False)

    def test_employee_card_separates_source_fact_from_structured_grant(self) -> None:
        response = self.client.get(
            reverse(
                "organizations:employee_detail",
                kwargs={"public_id": self.employee.public_id},
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Предоставленные оперативные полномочия")
        self.assertContains(response, "Импортированные положительные отметки")
        self.assertContains(
            response,
            "не разрешают контролируемое действие без отдельного структурированного grant",
        )
        self.assertContains(response, "SYNTHETIC-ORDER-R1")

    def test_evaluation_detail_exposes_result_digest_and_snapshot(self) -> None:
        evaluation = self.create_evaluation()

        response = self.client.get(
            reverse(
                "organizations:authority_evaluation_detail",
                kwargs={"public_id": evaluation.public_id},
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Проверка полномочия на момент действия")
        self.assertContains(response, "Разрешено")
        self.assertContains(response, evaluation.digest)
        self.assertContains(response, "SYNTHETIC-SW-001")
        self.assertContains(response, "EXPLICIT_GRANT")

    def test_anonymous_access_redirects_to_login(self) -> None:
        self.client.logout()

        registry = self.client.get(reverse("organizations:authority_registry"))
        detail = self.client.get(
            reverse(
                "organizations:employee_detail",
                kwargs={"public_id": self.employee.public_id},
            )
        )

        self.assertEqual(registry.status_code, 302)
        self.assertEqual(detail.status_code, 302)
