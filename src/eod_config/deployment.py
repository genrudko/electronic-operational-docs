from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping
from urllib.parse import urlsplit

SUPPORTED_DEPLOYMENT_MODES = frozenset({"development", "ci", "preview", "production"})
PRODUCTION_CAPABLE_MODE = "production"
MINIMUM_DATABASE_PASSWORD_LENGTH = 20
MINIMUM_PRODUCTION_SECRET_LENGTH = 50
MINIMUM_HSTS_SECONDS = 3600


class DeploymentConfigurationError(RuntimeError):
    """Raised when a deployment profile is internally unsafe."""


@dataclass(frozen=True)
class DeploymentContract:
    mode: str
    production_capable: bool
    csrf_trusted_origins: tuple[str, ...]
    hsts_seconds: int


def _text(env: Mapping[str, str], name: str, default: str = "") -> str:
    return str(env.get(name, default)).strip()


def _bool(env: Mapping[str, str], name: str, default: bool = False) -> bool:
    return _text(env, name, "1" if default else "0").lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _csv(env: Mapping[str, str], name: str, default: str = "") -> tuple[str, ...]:
    return tuple(value.strip() for value in _text(env, name, default).split(",") if value.strip())


def _valid_https_origin(value: str) -> bool:
    if "*" in value:
        return False
    parsed = urlsplit(value)
    return (
        parsed.scheme == "https"
        and bool(parsed.netloc)
        and parsed.path in {"", "/"}
        and not parsed.query
        and not parsed.fragment
    )


def validate_deployment_environment(env: Mapping[str, str]) -> DeploymentContract:
    """Validate deployment-mode invariants without printing secret values."""

    mode = _text(env, "EOD_DEPLOYMENT_MODE", "development").lower()
    if mode not in SUPPORTED_DEPLOYMENT_MODES:
        allowed = ", ".join(sorted(SUPPORTED_DEPLOYMENT_MODES))
        raise DeploymentConfigurationError(
            f"Неподдерживаемый EOD_DEPLOYMENT_MODE. Допустимы: {allowed}."
        )

    if mode != PRODUCTION_CAPABLE_MODE:
        return DeploymentContract(
            mode=mode,
            production_capable=False,
            csrf_trusted_origins=_csv(env, "DJANGO_CSRF_TRUSTED_ORIGINS"),
            hsts_seconds=0,
        )

    errors: list[str] = []
    secret_key = _text(env, "DJANGO_SECRET_KEY")
    if len(secret_key) < MINIMUM_PRODUCTION_SECRET_LENGTH:
        errors.append(
            "DJANGO_SECRET_KEY должен быть явно задан и иметь длину "
            f"не менее {MINIMUM_PRODUCTION_SECRET_LENGTH} символов"
        )
    if _bool(env, "DJANGO_DEBUG", True):
        errors.append("DJANGO_DEBUG должен быть отключён")

    allowed_hosts = _csv(env, "DJANGO_ALLOWED_HOSTS")
    if not allowed_hosts:
        errors.append("DJANGO_ALLOWED_HOSTS должен содержать явные host values")
    elif any(host == "*" or "*" in host for host in allowed_hosts):
        errors.append("DJANGO_ALLOWED_HOSTS не должен содержать wildcard")

    csrf_origins = _csv(env, "DJANGO_CSRF_TRUSTED_ORIGINS")
    if not csrf_origins:
        errors.append("DJANGO_CSRF_TRUSTED_ORIGINS должен содержать HTTPS origin")
    elif any(not _valid_https_origin(origin) for origin in csrf_origins):
        errors.append(
            "DJANGO_CSRF_TRUSTED_ORIGINS допускает только явные HTTPS origins без wildcard"
        )

    db_engine = _text(env, "DB_ENGINE").lower()
    if db_engine not in {"postgres", "postgresql"}:
        errors.append("production допускает только PostgreSQL; SQLite fallback запрещён")
    for name in ("POSTGRES_DB", "POSTGRES_USER", "POSTGRES_HOST", "POSTGRES_PORT"):
        if not _text(env, name):
            errors.append(f"{name} должен быть задан явно")
    if len(_text(env, "POSTGRES_PASSWORD")) < MINIMUM_DATABASE_PASSWORD_LENGTH:
        errors.append(
            "POSTGRES_PASSWORD должен быть задан явно и иметь длину "
            f"не менее {MINIMUM_DATABASE_PASSWORD_LENGTH} символов"
        )
    if _bool(env, "EOD_ALLOW_SQLITE_PATH_OVERRIDE", False):
        errors.append("EOD_ALLOW_SQLITE_PATH_OVERRIDE должен быть отключён")

    if _text(env, "EOD_TLS_TERMINATION").lower() != "reverse-proxy":
        errors.append("EOD_TLS_TERMINATION должен быть reverse-proxy")
    if not _bool(env, "EOD_TRUST_PROXY_HEADERS", False):
        errors.append("EOD_TRUST_PROXY_HEADERS=1 обязателен для production reverse proxy")
    if _bool(env, "EOD_TRUST_X_FORWARDED_HOST", False):
        errors.append(
            "EOD_TRUST_X_FORWARDED_HOST должен быть отключён; proxy обязан сохранять canonical Host"
        )

    raw_hsts = _text(env, "DJANGO_SECURE_HSTS_SECONDS")
    try:
        hsts_seconds = int(raw_hsts)
    except ValueError:
        hsts_seconds = 0
    if hsts_seconds < MINIMUM_HSTS_SECONDS:
        errors.append(
            f"DJANGO_SECURE_HSTS_SECONDS должен быть не менее {MINIMUM_HSTS_SECONDS}"
        )

    if errors:
        raise DeploymentConfigurationError(
            "Небезопасная production-конфигурация: " + "; ".join(errors) + "."
        )

    return DeploymentContract(
        mode=mode,
        production_capable=True,
        csrf_trusted_origins=csrf_origins,
        hsts_seconds=hsts_seconds,
    )
