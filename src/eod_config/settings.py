from __future__ import annotations

import os
import sys
from pathlib import Path

from .deployment import validate_deployment_environment

BASE_DIR = Path(__file__).resolve().parents[2]


def load_env_file(path: Path) -> None:
    # Load simple KEY=VALUE entries without overriding process environment.
    if not path.is_file():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            os.environ.setdefault(key, value)


load_env_file(BASE_DIR / ".env")


def env_bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, "1" if default else "0").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


TESTING = "test" in sys.argv or env_bool("EOD_TESTING", False)
DEPLOYMENT_CONTRACT = validate_deployment_environment(os.environ)
EOD_DEPLOYMENT_MODE = DEPLOYMENT_CONTRACT.mode

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "development-only-change-me").strip()
DEBUG = env_bool("DJANGO_DEBUG", True)
ALLOWED_HOSTS = [
    value.strip()
    for value in os.getenv("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")
    if value.strip()
]
CSRF_TRUSTED_ORIGINS = list(DEPLOYMENT_CONTRACT.csrf_trusted_origins)

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "apps.system.apps.SystemConfig",
    "apps.organizations.apps.OrganizationsConfig",
    "apps.documents.apps.DocumentsConfig",
    "apps.normatives.apps.NormativesConfig",
    "apps.equipment.apps.EquipmentConfig",
    "apps.dispatching.apps.DispatchingConfig",
    "apps.imports.apps.ImportsConfig",
    "apps.workplace_docs.apps.WorkplaceDocsConfig",
    "apps.operational_documents.apps.OperationalDocumentsConfig",
    "apps.equipment_defects.apps.EquipmentDefectsConfig",
    "apps.operational_log.apps.OperationalLogConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "apps.equipment_defects.middleware.EquipmentDefectRouteGuardMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "eod_config.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "src" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.organizations.context_processors.interface_preferences",
            ],
        },
    }
]
WSGI_APPLICATION = "eod_config.wsgi.application"
ASGI_APPLICATION = "eod_config.asgi.application"

EOD_ALLOW_SQLITE_PATH_OVERRIDE = env_bool("EOD_ALLOW_SQLITE_PATH_OVERRIDE", False)
EOD_DATABASE_PROFILE = os.getenv("EOD_DATABASE_PROFILE", "presentation").strip().lower() or "presentation"

DB_ENGINE = os.getenv("DB_ENGINE", "sqlite").strip().lower()
if DB_ENGINE == "sqlite":
    requested_sqlite_path = os.getenv("SQLITE_PATH", "").strip()
    entry_point = Path(sys.argv[0]).name.lower()
    if requested_sqlite_path and EOD_ALLOW_SQLITE_PATH_OVERRIDE:
        requested_path = Path(requested_sqlite_path)
        sqlite_path = requested_path if requested_path.is_absolute() else BASE_DIR / requested_path
        EOD_DATABASE_PROFILE = "explicit"
    else:
        default_name = "presentation.sqlite3"
        if EOD_DATABASE_PROFILE == "development":
            default_name = "dev.sqlite3"
        elif EOD_DATABASE_PROFILE == "gate" or entry_point.startswith("gate_"):
            default_name = "gate_runtime.sqlite3"
            EOD_DATABASE_PROFILE = "gate"
        else:
            EOD_DATABASE_PROFILE = "presentation"
        sqlite_path = BASE_DIR / "data" / default_name
    sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": sqlite_path,
        }
    }
elif DB_ENGINE in {"postgres", "postgresql"}:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("POSTGRES_DB", "eod"),
            "USER": os.getenv("POSTGRES_USER", "eod"),
            "PASSWORD": os.getenv("POSTGRES_PASSWORD", "eod_local_password"),
            "HOST": os.getenv("POSTGRES_HOST", "127.0.0.1"),
            "PORT": os.getenv("POSTGRES_PORT", "55432"),
            "CONN_MAX_AGE": 0 if TESTING else 60,
            "OPTIONS": {"connect_timeout": 5},
        }
    }
else:
    raise RuntimeError(
        f"Неподдерживаемый DB_ENGINE={DB_ENGINE!r}. Допустимы sqlite и postgresql."
    )

LANGUAGE_CODE = "ru"
TIME_ZONE = os.getenv("TIME_ZONE", "Europe/Moscow")
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "src" / "static"]
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": (
            "django.contrib.staticfiles.storage.StaticFilesStorage"
            if TESTING
            else "whitenoise.storage.CompressedManifestStaticFilesStorage"
        ),
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Security-sensitive HTTP/session semantics are explicit project decisions rather
# than implicit Django defaults, so framework upgrades cannot silently weaken them.
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = "Lax"

# Django admin is a privileged mutation surface. It remains available to the
# development/CI profiles, but the production-capable SAFE baseline does not
# route it at all. No environment opt-in exists here: any exceptional future
# production exposure requires an explicit, separately assured design.
EOD_DJANGO_ADMIN_ENABLED = not DEPLOYMENT_CONTRACT.production_capable

if DEPLOYMENT_CONTRACT.production_capable:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = DEPLOYMENT_CONTRACT.hsts_seconds
    SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS", False)
    SECURE_HSTS_PRELOAD = env_bool("DJANGO_SECURE_HSTS_PRELOAD", False)
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    USE_X_FORWARDED_HOST = False
else:
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    SECURE_HSTS_SECONDS = 0
    SECURE_HSTS_INCLUDE_SUBDOMAINS = False
    SECURE_HSTS_PRELOAD = False
    SECURE_PROXY_SSL_HEADER = None
    USE_X_FORWARDED_HOST = False

LOGIN_URL = "organizations:login"
LOGIN_REDIRECT_URL = "system:home"
LOGOUT_REDIRECT_URL = "system:home"
