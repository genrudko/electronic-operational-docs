from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass

from django.contrib.auth import get_user_model
from django.db import transaction

DEMO_ACCESS_ENV = "EOD_DEMO_USER_PASSWORD"
DEMO_USERNAMES = ("operator.demo", "supervisor.demo")
MINIMUM_DEMO_PASSWORD_LENGTH = 16

# Contract marker: COMPROMISED_DEMO_PASSWORD_SHA256.
# Hashes identify revoked historical values without republishing them.
COMPROMISED_DEMO_CREDENTIAL_SHA256 = frozenset(
    {
        "b79083c70227d52d9367e736c031374fe5848582a3e63c90a0ac7171ba4f05d7",
    }
)


class DemoAccessPolicyError(ValueError):
    pass


@dataclass(frozen=True)
class DemoAccessResult:
    status: str
    accounts: int
    changed: int


@dataclass(frozen=True)
class DemoAccessPresentation:
    usernames: tuple[str, ...]
    password: str


def injected_demo_password() -> str:
    return os.environ.get(DEMO_ACCESS_ENV, "")


def validate_demo_password(password: str) -> None:
    if not password:
        raise DemoAccessPolicyError(
            f"{DEMO_ACCESS_ENV} is required to enable demo account access."
        )
    if len(password) < MINIMUM_DEMO_PASSWORD_LENGTH:
        raise DemoAccessPolicyError(
            f"{DEMO_ACCESS_ENV} must contain at least "
            f"{MINIMUM_DEMO_PASSWORD_LENGTH} characters."
        )
    classes = (
        any(character.islower() for character in password),
        any(character.isupper() for character in password),
        any(character.isdigit() for character in password),
        any(not character.isalnum() for character in password),
    )
    if sum(classes) < 3:
        raise DemoAccessPolicyError(
            f"{DEMO_ACCESS_ENV} must use at least three character classes."
        )
    password_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
    if password_hash in COMPROMISED_DEMO_CREDENTIAL_SHA256:
        raise DemoAccessPolicyError(
            f"{DEMO_ACCESS_ENV} contains a revoked historical credential."
        )


def development_demo_access_presentation(
    *,
    deployment_mode: str,
) -> DemoAccessPresentation | None:
    """Return the Development-only credential that the login page may publish.

    The source never contains the credential.  A value is exposed only when the
    live process is explicitly in the Development deployment mode and the same
    injected secret passes the demo-access security policy used for authentication.
    """

    if deployment_mode.strip().lower() != "development":
        return None
    candidate = injected_demo_password()
    try:
        validate_demo_password(candidate)
    except DemoAccessPolicyError:
        return None
    return DemoAccessPresentation(usernames=DEMO_USERNAMES, password=candidate)


@transaction.atomic
def reconcile_demo_access(
    *,
    password: str | None = None,
    require_injection: bool = False,
) -> DemoAccessResult:
    user_model = get_user_model()
    users = list(
        user_model.objects.filter(username__in=DEMO_USERNAMES).order_by("username")
    )
    if not users:
        return DemoAccessResult(status="ABSENT", accounts=0, changed=0)

    candidate = injected_demo_password() if password is None else password
    if not candidate:
        if require_injection:
            raise DemoAccessPolicyError(
                f"{DEMO_ACCESS_ENV} is required; demo credentials were not created."
            )
        changed = 0
        for user in users:
            update_fields: list[str] = []
            if user.has_usable_password():
                user.set_unusable_password()
                update_fields.append("password")
            if user.is_active:
                user.is_active = False
                update_fields.append("is_active")
            if update_fields:
                user.save(update_fields=update_fields)
                changed += 1
        return DemoAccessResult(
            status="DISABLED_MISSING_INJECTION",
            accounts=len(users),
            changed=changed,
        )

    validate_demo_password(candidate)
    changed = 0
    for user in users:
        update_fields = []
        if not user.check_password(candidate):
            user.set_password(candidate)
            update_fields.append("password")
        if not user.is_active:
            user.is_active = True
            update_fields.append("is_active")
        if update_fields:
            user.save(update_fields=update_fields)
            changed += 1
    return DemoAccessResult(
        status="ENABLED_LOCAL_INJECTION",
        accounts=len(users),
        changed=changed,
    )
