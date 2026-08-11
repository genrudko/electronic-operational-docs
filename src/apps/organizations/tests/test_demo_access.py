from __future__ import annotations

import hashlib
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.organizations import demo_access
from apps.organizations.demo_access import (
    DEMO_ACCESS_ENV,
    DemoAccessPolicyError,
    reconcile_demo_access,
)


def strong_candidate(prefix: str) -> str:
    return f"{prefix}{'A' * 16}1!"


class DemoAccessPolicyTests(TestCase):
    def setUp(self) -> None:
        user_model = get_user_model()
        initial = strong_candidate("Initial")
        self.operator, _ = user_model.objects.get_or_create(username="operator.demo")
        self.operator.is_active = True
        self.operator.set_password(initial)
        self.operator.save(update_fields=["is_active", "password"])
        self.supervisor, _ = user_model.objects.get_or_create(username="supervisor.demo")
        self.supervisor.is_active = True
        self.supervisor.set_password(initial)
        self.supervisor.save(update_fields=["is_active", "password"])

    @mock.patch.dict("os.environ", {}, clear=True)
    def test_missing_injection_disables_existing_demo_access(self) -> None:
        result = reconcile_demo_access(require_injection=False)
        self.operator.refresh_from_db()
        self.supervisor.refresh_from_db()
        self.assertEqual(result.status, "DISABLED_MISSING_INJECTION")
        self.assertEqual(result.changed, 2)
        self.assertFalse(self.operator.has_usable_password())
        self.assertFalse(self.supervisor.has_usable_password())

    @mock.patch.dict("os.environ", {}, clear=True)
    def test_mandatory_injection_fails_without_changing_accounts(self) -> None:
        with self.assertRaisesMessage(DemoAccessPolicyError, DEMO_ACCESS_ENV):
            reconcile_demo_access(require_injection=True)
        self.operator.refresh_from_db()
        self.supervisor.refresh_from_db()
        self.assertTrue(self.operator.has_usable_password())
        self.assertTrue(self.supervisor.has_usable_password())

    def test_local_injection_enables_both_accounts(self) -> None:
        candidate = strong_candidate("Local")
        with mock.patch.dict("os.environ", {DEMO_ACCESS_ENV: candidate}, clear=True):
            result = reconcile_demo_access(require_injection=True)
        self.operator.refresh_from_db()
        self.supervisor.refresh_from_db()
        self.assertEqual(result.status, "ENABLED_LOCAL_INJECTION")
        self.assertTrue(self.operator.check_password(candidate))
        self.assertTrue(self.supervisor.check_password(candidate))

    def test_revoked_hash_is_rejected(self) -> None:
        candidate = strong_candidate("Revoked")
        candidate_hash = hashlib.sha256(candidate.encode("utf-8")).hexdigest()
        with mock.patch.object(
            demo_access,
            "COMPROMISED_DEMO_CREDENTIAL_SHA256",
            frozenset({candidate_hash}),
        ):
            with self.assertRaisesMessage(
                DemoAccessPolicyError,
                "revoked historical credential",
            ):
                reconcile_demo_access(password=candidate, require_injection=True)
