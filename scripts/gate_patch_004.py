from __future__ import annotations

import inspect
import os
import sys
from pathlib import Path
from uuid import UUID

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eod_config.settings")
os.environ.setdefault("DB_ENGINE", "sqlite")
os.environ.setdefault("PYTHONUTF8", "1")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

import django  # noqa: E402
from django.core.exceptions import ValidationError  # noqa: E402
from django.db import connection, transaction  # noqa: E402

django.setup()

from apps.documents.models import (  # noqa: E402
    AuditEvent,
    Document,
    DocumentNumberSequence,
    DocumentSignature,
    SignedSnapshot,
)
from apps.documents.services import (  # noqa: E402
    IntegrityStatus,
    create_document_draft,
    register_document_with_password,
    verify_document_integrity,
)
from apps.organizations.demo_access import (  # noqa: E402
    DemoAccessPolicyError,
    injected_demo_password,
    validate_demo_password,
)
from apps.organizations.models import Employee  # noqa: E402

DEMO_ACCESS_VALUE = injected_demo_password()
try:
    validate_demo_password(DEMO_ACCESS_VALUE)
except DemoAccessPolicyError as exc:
    raise SystemExit(
        "EOD_DEMO_USER_PASSWORD must be injected to run Patch 004 gate."
    ) from exc

GATE_ID = UUID("00000000-0000-4000-8000-000000000304")

actor = Employee.objects.select_related(
    "user", "organization", "position", "division", "workplace"
).get(user__username="operator.demo")
document_type = actor.organization.document_types.get(code="general")

legacy_signatures = DocumentSignature.objects.filter(
    confirmation_method=DocumentSignature.ConfirmationMethod.LEGACY_MIGRATION
)
demo_signatures = DocumentSignature.objects.filter(
    confirmation_method=DocumentSignature.ConfirmationMethod.DEMO_SEED
)
if legacy_signatures.count() + demo_signatures.count() < 2:
    raise SystemExit(
        "Expected at least two non-password baseline confirmations from migration or demo seed."
    )
for item in legacy_signatures.select_related("snapshot__document"):
    if verify_document_integrity(item.snapshot.document).status != IntegrityStatus.LEGACY:
        raise SystemExit("Legacy document is not reported as LEGACY.")
for item in demo_signatures.select_related("snapshot__document"):
    if verify_document_integrity(item.snapshot.document).status != IntegrityStatus.VALID:
        raise SystemExit("Demo-seeded document is not reported as VALID.")

migration_source = (
    ROOT / "src/apps/documents/migrations/0003_legacy_signature_backfill.py"
).read_text(encoding="utf-8")
for marker in ("LEGACY_MIGRATION", "migrations.RunPython", "def forwards"):
    if marker not in migration_source:
        raise SystemExit(f"Legacy migration marker is missing: {marker}")

wrong = Document.objects.filter(public_id=GATE_ID).first()
if wrong is None:
    wrong = create_document_draft(
        document_type=document_type,
        actor=actor,
        title="Контрольная запись Patch 004",
        content={"subject": "Gate", "body": "Проверка повторной аутентификации и SHA-256."},
        public_id=GATE_ID,
    )

if wrong.status == Document.Status.DRAFT:
    sequence = DocumentNumberSequence.objects.filter(
        organization=actor.organization,
        document_type=document_type,
    ).first()
    before = sequence.last_value if sequence else 0
    try:
        register_document_with_password(
            document=wrong,
            actor=actor,
            user=actor.user,
            password="wrong-password",
        )
    except ValidationError:
        pass
    else:
        raise SystemExit("Wrong password unexpectedly registered the document.")
    wrong.refresh_from_db()
    sequence = DocumentNumberSequence.objects.filter(
        organization=actor.organization,
        document_type=document_type,
    ).first()
    after = sequence.last_value if sequence else 0
    if wrong.status != Document.Status.DRAFT or after != before:
        raise SystemExit("Wrong password changed document state or number sequence.")
    result = register_document_with_password(
        document=wrong,
        actor=actor,
        user=actor.user,
        password=DEMO_ACCESS_VALUE,
    )
    wrong = result.document

wrong.refresh_from_db()
integrity = verify_document_integrity(wrong)
if integrity.status != IntegrityStatus.VALID:
    raise SystemExit(f"Password-confirmed document integrity is {integrity.status}.")
if integrity.signature is None or integrity.snapshot is None:
    raise SystemExit("Snapshot or signature is missing.")
if integrity.signature.confirmation_method != DocumentSignature.ConfirmationMethod.PASSWORD_REAUTH:
    raise SystemExit("Password-confirmed document has the wrong confirmation method.")

snapshot = integrity.snapshot
with transaction.atomic():
    with connection.cursor() as cursor:
        cursor.execute(
            f'UPDATE "{SignedSnapshot._meta.db_table}" SET canonical_json = %s WHERE id = %s',
            [snapshot.canonical_json + " ", snapshot.pk],
        )
    wrong.refresh_from_db()
    if verify_document_integrity(wrong).status != IntegrityStatus.INVALID:
        raise SystemExit("Tampered snapshot was not reported as INVALID.")
    transaction.set_rollback(True)

credential_corpus = "\n".join(
    [
        snapshot.canonical_json,
        integrity.signature.checksum,
        *[
            str(item.payload)
            for item in AuditEvent.objects.filter(document=wrong)
        ],
    ]
)
if DEMO_ACCESS_VALUE in credential_corpus:
    raise SystemExit("Authentication credential leaked into snapshot, signature or audit payload.")

for model, instance in (
    (SignedSnapshot, snapshot),
    (DocumentSignature, integrity.signature),
):
    try:
        model.objects.filter(pk=instance.pk).update(pk=instance.pk)
    except ValidationError:
        pass
    else:
        raise SystemExit(f"Bulk update is not blocked for {model.__name__}.")

source = inspect.getsource(register_document_with_password)
if "check_password" not in source:
    raise SystemExit("Password re-authentication is missing from the registration service.")
if "password" in snapshot.canonical_json.lower():
    raise SystemExit("Snapshot schema contains a password field.")

print(f"DATABASE_VENDOR={connection.vendor}")
print(f"LEGACY_SIGNATURE_COUNT={legacy_signatures.count()}")
print(f"DEMO_SIGNATURE_COUNT={demo_signatures.count()}")
print(f"SNAPSHOT_COUNT={SignedSnapshot.objects.count()}")
print(f"SIGNATURE_COUNT={DocumentSignature.objects.count()}")
print(f"PASSWORD_DOCUMENT_STATUS={integrity.status.value}")
print("WRONG_PASSWORD_NO_NUMBER=PASSED")
print("PASSWORD_NOT_PERSISTED=PASSED")
print("TAMPER_DETECTION=PASSED")
print("PATCH_004_SYSTEM_SIGNATURE_INTEGRITY_GATE_PASSED")
