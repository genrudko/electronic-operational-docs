from __future__ import annotations

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.organizations.demo_access import (
    DEMO_USERNAMES,
    DemoAccessPolicyError,
    ensure_development_demo_accounts,
    reconcile_demo_access,
)


class Command(BaseCommand):
    help = "Create/reconcile the Development-only demo authentication principals."

    def handle(self, *args, **options) -> None:
        if settings.EOD_DEPLOYMENT_MODE != "development":
            raise CommandError(
                "Development demo access bootstrap is forbidden outside Development."
            )

        try:
            ensure_development_demo_accounts()
            result = reconcile_demo_access(require_injection=True)
        except DemoAccessPolicyError as exc:
            raise CommandError(
                "Development demo access bootstrap rejected the local credential policy."
            ) from exc

        if result.status != "ENABLED_LOCAL_INJECTION" or result.accounts != len(DEMO_USERNAMES):
            raise CommandError(
                "Development demo access bootstrap did not establish the expected principals."
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Development demo access bootstrap: PASS accounts={result.accounts}"
            )
        )
