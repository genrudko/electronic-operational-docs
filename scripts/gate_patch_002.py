from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("DB_ENGINE", "sqlite")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eod_config.settings")

import django  # noqa: E402
from django.contrib.auth import get_user_model  # noqa: E402
from django.db import connection  # noqa: E402
from django.utils import timezone  # noqa: E402

django.setup()

from apps.organizations.models import (  # noqa: E402
    AuthenticationEvent,
    Employee,
    Organization,
    Role,
    Substitution,
)
from apps.organizations.services import get_effective_roles  # noqa: E402

organization = Organization.objects.get(code="DEMO")
users = get_user_model().objects.filter(username__endswith=".demo", is_active=True)
employees = Employee.objects.filter(organization=organization, user__in=users, is_active=True)

if users.count() != 2 or employees.count() != 2:
    raise SystemExit("Expected exactly two personal demo users linked to two employees.")
if employees.values("user_id").distinct().count() != employees.count():
    raise SystemExit("A personal account is linked to more than one employee.")
if Role.objects.filter(is_system=True, is_active=True).count() < 3:
    raise SystemExit("System roles were not seeded.")

operator = Employee.objects.get(user__username="operator.demo")
role_codes = {item.assignment.role.code for item in get_effective_roles(operator)}
if "operator" not in role_codes or "shift_supervisor" not in role_codes:
    raise SystemExit("Effective roles do not include direct and substituted permissions.")

active_substitutions = Substitution.objects.filter(
    substitute_employee=operator,
    is_active=True,
    valid_from__lte=timezone.localdate(),
    valid_until__gte=timezone.localdate(),
)
if not active_substitutions.exists():
    raise SystemExit("Active temporary substitution is missing.")

with connection.cursor() as cursor:
    tables = set(connection.introspection.table_names(cursor))
if AuthenticationEvent._meta.db_table not in tables:
    raise SystemExit("Authentication audit table is missing.")

print("ORGANIZATION_COUNT=1")
print(f"PERSONAL_ACCOUNT_COUNT={users.count()}")
print(f"EMPLOYEE_COUNT={employees.count()}")
print(f"EFFECTIVE_ROLE_CODES={','.join(sorted(role_codes))}")
print("PATCH_002_ORGANIZATIONAL_CORE_GATE_PASSED")
