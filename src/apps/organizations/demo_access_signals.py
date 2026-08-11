from __future__ import annotations

import logging

from django.conf import settings
from django.db.models.signals import post_migrate
from django.dispatch import receiver

from .demo_access import (
    DemoAccessPolicyError,
    ensure_development_demo_accounts,
    injected_demo_password,
    reconcile_demo_access,
)

logger = logging.getLogger(__name__)


@receiver(
    post_migrate,
    dispatch_uid="organizations.enforce_demo_access_policy",
)
def enforce_demo_access_policy(sender, **kwargs) -> None:
    if sender.label != "organizations":
        return
    # Django emits post_migrate while constructing and flushing its isolated
    # test database. Automatic Development demo bootstrap there would pollute
    # test fixtures, consume auth_user identities, and make account-creation
    # tests order-dependent. Tests that exercise demo access call the bootstrap
    # functions explicitly; real Development migrations keep automatic policy
    # enforcement enabled.
    if settings.TESTING:
        logger.info("Demo access automatic policy skipped for isolated test database.")
        return
    try:
        created = 0
        if settings.EOD_DEPLOYMENT_MODE == "development":
            demo_password = injected_demo_password()
            if not demo_password:
                # Trusted deployment maintenance commands intentionally run
                # without the Development demo credential. They may migrate or
                # inspect the persistent database, but they must neither disable
                # existing demo principals nor fail merely because the secret is
                # outside that maintenance process. The real Development app
                # receives the credential and its health/login smoke verifies the
                # resulting authentication state before deployment acceptance.
                logger.info(
                    "Demo access automatic policy deferred for Development "
                    "maintenance process without local injection."
                )
                return
            created = ensure_development_demo_accounts()
            result = reconcile_demo_access(
                password=demo_password,
                require_injection=True,
            )
        else:
            # Outside Development any persistent demo accounts fail closed when
            # there is no explicit local injection.
            result = reconcile_demo_access(require_injection=False)
    except DemoAccessPolicyError as exc:
        raise RuntimeError(
            "Demo access policy rejected the configured local injection."
        ) from exc
    logger.info(
        "Demo access policy applied: status=%s accounts=%s created=%s changed=%s",
        result.status,
        result.accounts,
        created,
        result.changed,
    )
