from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.normatives.models import NormativeDocument
from apps.organizations.models import (
    Division,
    Employee,
    Organization,
    Position,
    Role,
    RoleAssignment,
    Workplace,
)
from apps.workplace_docs.models import (
    RequirementKind,
    SourceKind,
    StorageForm,
    WorkplaceDocumentEntry,
    WorkplaceDocumentList,
    WorkplaceDocumentRevision,
)
from tests.credential_fixtures import ephemeral_credential


class WorkplaceDocumentTestBase(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.organization = Organization.objects.create(code="ORG", name="Организация")
        cls.division = Division.objects.create(
            organization=cls.organization,
            code="OPS",
            name="Оперативное подразделение",
        )
        cls.workplace = Workplace.objects.create(
            organization=cls.organization,
            division=cls.division,
            code="SHIFT",
            name="Рабочее место смены",
        )
        cls.position = Position.objects.create(
            organization=cls.organization,
            code="SUPERVISOR",
            name="Начальник смены",
            is_operational=True,
        )
        user_model = get_user_model()
        cls.user = user_model.objects.create_user(
            username="approver",
            password=ephemeral_credential("WorkplaceApprover"),
        )
        cls.employee = Employee.objects.create(
            organization=cls.organization,
            division=cls.division,
            position=cls.position,
            workplace=cls.workplace,
            user=cls.user,
            personnel_number="A-001",
            last_name="Орлова",
            first_name="Анна",
            middle_name="Сергеевна",
            employment_start=date(2026, 1, 1),
        )
        cls.role = Role.objects.create(
            code="organization_admin",
            name="Администратор справочников",
            is_system=True,
        )
        cls.assignment = RoleAssignment.objects.create(
            employee=cls.employee,
            role=cls.role,
            valid_from=date(2026, 1, 1),
            is_active=True,
        )
        cls.normative = NormativeDocument.objects.create(
            code="federal-demo",
            title="Федеральный демонстрационный документ",
            short_title="Федеральный документ",
            scope=NormativeDocument.Scope.FEDERAL,
            issuer="Минэнерго России",
        )

        cls.foreign_organization = Organization.objects.create(code="OTHER", name="Другая организация")
        cls.foreign_division = Division.objects.create(
            organization=cls.foreign_organization,
            code="OPS",
            name="Другое подразделение",
        )
        cls.foreign_workplace = Workplace.objects.create(
            organization=cls.foreign_organization,
            division=cls.foreign_division,
            code="SHIFT",
            name="Другое рабочее место",
        )
        cls.foreign_position = Position.objects.create(
            organization=cls.foreign_organization,
            code="SUPERVISOR",
            name="Начальник смены",
        )
        cls.foreign_user = user_model.objects.create_user(
            username="foreign",
            password=ephemeral_credential("ForeignWorkplaceUser"),
        )
        cls.foreign_employee = Employee.objects.create(
            organization=cls.foreign_organization,
            division=cls.foreign_division,
            position=cls.foreign_position,
            workplace=cls.foreign_workplace,
            user=cls.foreign_user,
            personnel_number="F-001",
            last_name="Петров",
            first_name="Пётр",
            middle_name="Петрович",
            employment_start=date(2026, 1, 1),
        )
        cls.foreign_local_normative = NormativeDocument.objects.create(
            organization=cls.foreign_organization,
            code="foreign-local",
            title="Локальный документ другой организации",
            short_title="Чужой локальный документ",
            scope=NormativeDocument.Scope.LOCAL,
            issuer="Другая организация",
        )

    def create_document_list(self, *, code: str = "shift-list") -> WorkplaceDocumentList:
        return WorkplaceDocumentList.objects.create(
            organization=self.organization,
            workplace=self.workplace,
            code=code,
            title="Перечень документации смены",
        )

    def create_revision(
        self,
        *,
        document_list: WorkplaceDocumentList | None = None,
        revision_number: int = 1,
        effective_from: date = date(2026, 1, 1),
        effective_until: date | None = None,
        review_period_months: int = 12,
        with_entry: bool = True,
    ) -> WorkplaceDocumentRevision:
        target_list = document_list or self.create_document_list()
        revision = WorkplaceDocumentRevision.objects.create(
            document_list=target_list,
            revision_number=revision_number,
            effective_from=effective_from,
            effective_until=effective_until,
            review_period_months=review_period_months,
            change_summary="Тестовая редакция",
        )
        if with_entry:
            WorkplaceDocumentEntry.objects.create(
                revision=revision,
                code="OP-JOURNAL",
                title="Оперативный журнал",
                source_kind=SourceKind.LOCAL,
                requirement_kind=RequirementKind.MANDATORY,
                applicability_text="На каждом дежурстве.",
                storage_form=StorageForm.ELECTRONIC,
                basis_text="Локальная инструкция.",
                display_order=10,
            )
        return revision
