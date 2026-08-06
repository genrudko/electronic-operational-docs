from __future__ import annotations

import logging

from django.db.models.signals import post_migrate
from django.dispatch import receiver

from .demo_access import DemoAccessPolicyError, reconcile_demo_access

logger = logging.getLogger(__name__)


@receiver(
    post_migrate,
    dispatch_uid="organizations.enforce_demo_access_policy",
)
def enforce_demo_access_policy(sender, **kwargs) -> None:
    if sender.label != "organizations":
        return
    try:
        result = reconcile_demo_access(require_injection=False)
    except DemoAccessPolicyError as exc:
        raise RuntimeError(
            "Demo access policy rejected the configured local injection."
        ) from exc
    logger.info(
        "Demo access policy applied: status=%s accounts=%s changed=%s",
        result.status,
        result.accounts,
        result.changed,
    )
