from __future__ import annotations

from datetime import UTC, datetime

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from apps.organizations.authority import (
    AuthorityActorFact,
    AuthorityBasisStatus,
    AuthorityDecision,
    AuthorityEvaluationResult,
    AuthorityGrantFact,
    AuthorityQualificationFact,
    AuthorityReason,
    AuthorityRequest,
    AuthorityScope,
    AuthorityScopeKind,
    AuthoritySubstitutionFact,
    ExternalPersonnelEngagementFact,
    PersonnelRelationKind,
    evaluate_authority,
)

MOMENT = datetime(2026, 8, 2, 8, 30, tzinfo=UTC)
START = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
END = datetime(2026, 12, 31, 23, 59, tzinfo=UTC)
SITE_SCOPE = AuthorityScope(
    kind=AuthorityScopeKind.ENERGY_SITE,
    reference="site-17",
    label="Кочубеевская ВЭС",
)


def actor(
    *,
    employee_id: int = 7,
    organization_id: int = 1,
    relation_kind: PersonnelRelationKind = PersonnelRelationKind.EMPLOYEE,
    is_active: bool = True,
    employment_until: datetime | None = END,
    application_roles: tuple[str, ...] = (),
) -> AuthorityActorFact:
    return AuthorityActorFact(
        employee_id=employee_id,
        organization_id=organization_id,
        relation_kind=relation_kind,
        full_name="Иванов Иван Иванович",
        position="Начальник смены",
        division="Оперативная служба",
        workplace="ЩУ КВЭС",
        employment_from=START,
        employment_until=employment_until,
        is_active=is_active,
        application_roles=application_roles,
    )


def request(
    *,
    actor_employee_id: int = 7,
    organization_id: int = 1,
    scope: AuthorityScope = SITE_SCOPE,
    required_qualification_codes: tuple[str, ...] = (),
) -> AuthorityRequest:
    return AuthorityRequest(
        organization_id=organization_id,
        actor_employee_id=actor_employee_id,
        action_code="switching.execute",
        occurred_at=MOMENT,
        scope=scope,
        subject_type="switching_document",
        subject_id="SW-2026-17",
        required_qualification_codes=required_qualification_codes,
    )


def grant(
    *,
    grant_id: str = "grant-17",
    employee_id: int = 7,
    organization_id: int = 1,
    scope: AuthorityScope = SITE_SCOPE,
    basis_status: AuthorityBasisStatus = AuthorityBasisStatus.CONFIRMED,
    valid_from: datetime = START,
    valid_until: datetime | None = END,
    is_active: bool = True,
    allow_substitution: bool = False,
) -> AuthorityGrantFact:
    return AuthorityGrantFact(
        grant_id=grant_id,
        employee_id=employee_id,
        organization_id=organization_id,
        action_code="switching.execute",
        scope=scope,
        valid_from=valid_from,
        valid_until=valid_until,
        basis_status=basis_status,
        basis_reference="ORDER-17/2026-R1",
        source_ids=("REF-OD-051", "SRC-DEC-STAGE2"),
        is_active=is_active,
        allow_substitution=allow_substitution,
    )


class AuthorityContractTests(SimpleTestCase):
    def test_explicit_confirmed_grant_allows_action(self) -> None:
        result = evaluate_authority(
            actor=actor(),
            request=request(),
            grants=(grant(),),
        )

        self.assertEqual(result.decision, AuthorityDecision.ALLOW)
        self.assertEqual(result.reasons, (AuthorityReason.EXPLICIT_GRANT,))
        self.assertEqual(result.matched_grant_id, "grant-17")
        self.assertEqual(len(result.digest), 64)

    def test_application_role_and_position_never_replace_operational_grant(self) -> None:
        result = evaluate_authority(
            actor=actor(application_roles=("registry_admin", "operator")),
            request=request(),
            grants=(),
        )

        self.assertEqual(result.decision, AuthorityDecision.DENY)
        self.assertIn(AuthorityReason.NO_MATCHING_GRANT, result.reasons)
        self.assertEqual(result.snapshot["actor"]["position"], "Начальник смены")
        self.assertEqual(
            result.snapshot["actor"]["application_roles"],
            ("OPERATOR", "REGISTRY_ADMIN"),
        )

    def test_unconfirmed_basis_returns_verify_not_allow(self) -> None:
        result = evaluate_authority(
            actor=actor(),
            request=request(),
            grants=(grant(basis_status=AuthorityBasisStatus.VERIFY),),
        )

        self.assertEqual(result.decision, AuthorityDecision.VERIFY)
        self.assertIn(AuthorityReason.BASIS_VERIFY, result.reasons)
        self.assertEqual(result.matched_grant_id, "grant-17")

    def test_expired_grant_and_scope_mismatch_are_denied(self) -> None:
        other_scope = AuthorityScope(
            kind=AuthorityScopeKind.ENERGY_SITE,
            reference="site-99",
        )
        result = evaluate_authority(
            actor=actor(),
            request=request(),
            grants=(
                grant(
                    scope=other_scope,
                    valid_until=datetime(2026, 7, 31, 23, 59, tzinfo=UTC),
                ),
            ),
        )

        self.assertEqual(result.decision, AuthorityDecision.DENY)
        self.assertIn(AuthorityReason.GRANT_NOT_EFFECTIVE, result.reasons)
        self.assertIn(AuthorityReason.SCOPE_MISMATCH, result.reasons)

    def test_required_qualification_is_checked_for_actor_at_action_time(self) -> None:
        denied = evaluate_authority(
            actor=actor(),
            request=request(required_qualification_codes=("ES_GROUP_IV",)),
            grants=(grant(),),
        )
        allowed = evaluate_authority(
            actor=actor(),
            request=request(required_qualification_codes=("ES_GROUP_IV",)),
            grants=(grant(),),
            qualifications=(
                AuthorityQualificationFact(
                    employee_id=7,
                    code="ES_GROUP_IV",
                    valid_from=START,
                    valid_until=END,
                ),
            ),
        )

        self.assertEqual(denied.decision, AuthorityDecision.DENY)
        self.assertIn(AuthorityReason.QUALIFICATION_MISSING, denied.reasons)
        self.assertEqual(allowed.decision, AuthorityDecision.ALLOW)

    def test_substitution_requires_explicit_grant_flag_action_scope_and_period(self) -> None:
        source_grant = grant(
            employee_id=8,
            grant_id="grant-source-8",
            allow_substitution=True,
        )
        substitution = AuthoritySubstitutionFact(
            substitution_id="sub-8-7",
            replaced_employee_id=8,
            substitute_employee_id=7,
            organization_id=1,
            action_codes=("SWITCHING.EXECUTE",),
            scope=SITE_SCOPE,
            valid_from=START,
            valid_until=END,
            basis_status=AuthorityBasisStatus.CONFIRMED,
            basis_reference="ORDER-SUB-8-7",
        )

        allowed = evaluate_authority(
            actor=actor(),
            request=request(),
            grants=(source_grant,),
            substitutions=(substitution,),
        )
        denied = evaluate_authority(
            actor=actor(),
            request=request(),
            grants=(grant(employee_id=8, allow_substitution=False),),
            substitutions=(substitution,),
        )

        self.assertEqual(allowed.decision, AuthorityDecision.ALLOW)
        self.assertEqual(
            allowed.snapshot["substitution"]["substitution_id"],
            "sub-8-7",
        )
        self.assertEqual(denied.decision, AuthorityDecision.DENY)
        self.assertIn(AuthorityReason.SUBSTITUTION_NOT_ALLOWED, denied.reasons)

    def test_external_personnel_requires_effective_host_engagement(self) -> None:
        external_actor = actor(
            organization_id=2,
            relation_kind=PersonnelRelationKind.CONTRACTOR,
        )
        no_engagement = evaluate_authority(
            actor=external_actor,
            request=request(),
            grants=(grant(),),
        )
        engagement = ExternalPersonnelEngagementFact(
            engagement_id="external-7-1",
            employee_id=7,
            home_organization_id=2,
            host_organization_id=1,
            relation_kind=PersonnelRelationKind.CONTRACTOR,
            scope=SITE_SCOPE,
            valid_from=START,
            valid_until=END,
            basis_status=AuthorityBasisStatus.CONFIRMED,
            basis_reference="CONTRACTOR-ADMISSION-17",
        )
        allowed = evaluate_authority(
            actor=external_actor,
            request=request(),
            grants=(grant(),),
            external_engagements=(engagement,),
        )

        self.assertEqual(no_engagement.decision, AuthorityDecision.DENY)
        self.assertIn(
            AuthorityReason.EXTERNAL_ENGAGEMENT_REQUIRED,
            no_engagement.reasons,
        )
        self.assertEqual(allowed.decision, AuthorityDecision.ALLOW)

    def test_inactive_or_expired_employment_is_denied_before_grant(self) -> None:
        inactive = evaluate_authority(
            actor=actor(is_active=False),
            request=request(),
            grants=(grant(),),
        )
        expired = evaluate_authority(
            actor=actor(
                employment_until=datetime(2026, 7, 31, 23, 59, tzinfo=UTC)
            ),
            request=request(),
            grants=(grant(),),
        )

        self.assertEqual(inactive.decision, AuthorityDecision.DENY)
        self.assertIn(AuthorityReason.EMPLOYEE_INACTIVE, inactive.reasons)
        self.assertEqual(expired.decision, AuthorityDecision.DENY)
        self.assertIn(AuthorityReason.EMPLOYMENT_NOT_EFFECTIVE, expired.reasons)

    def test_snapshot_is_deterministic_and_deeply_immutable(self) -> None:
        first = evaluate_authority(
            actor=actor(application_roles=("operator", "registry_admin")),
            request=request(),
            grants=(grant(),),
        )
        second = evaluate_authority(
            actor=actor(application_roles=("registry_admin", "operator")),
            request=request(),
            grants=(grant(),),
        )

        self.assertEqual(first.digest, second.digest)
        with self.assertRaises(TypeError):
            first.snapshot["actor"]["full_name"] = "Другой сотрудник"  # type: ignore[index]
        with self.assertRaises(TypeError):
            first.snapshot["grant"]["scope"]["reference"] = "site-99"  # type: ignore[index]

    def test_secret_like_snapshot_fields_are_rejected(self) -> None:
        with self.assertRaises(ValidationError) as context:
            AuthorityEvaluationResult(
                decision=AuthorityDecision.DENY,
                reasons=(AuthorityReason.NO_MATCHING_GRANT,),
                snapshot={
                    "actor": {"employee_id": 7},
                    "authentication": {"api_token": "must-not-be-persisted"},
                },
            )

        self.assertIn("Секретное поле запрещено", str(context.exception))

    def test_naive_action_time_is_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            AuthorityRequest(
                organization_id=1,
                actor_employee_id=7,
                action_code="switching.execute",
                occurred_at=datetime(2026, 8, 2, 8, 30),
                scope=SITE_SCOPE,
                subject_type="switching_document",
                subject_id="SW-2026-17",
            )
