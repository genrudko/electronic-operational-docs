from __future__ import annotations

import inspect
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eod_config.settings")
os.environ.setdefault("DB_ENGINE", "sqlite")
os.environ.setdefault("PYTHONUTF8", "1")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

import django  # noqa: E402
from django.core.exceptions import ValidationError  # noqa: E402
from django.db import connection  # noqa: E402

django.setup()

from apps.documents import services  # noqa: E402
from apps.documents.models import (  # noqa: E402
    AuditEvent,
    Document,
    DocumentLink,
    DocumentNumberSequence,
    DocumentVersion,
)

documents = Document.objects.all()
registered = list(documents.filter(status=Document.Status.REGISTERED))
drafts = list(documents.filter(status=Document.Status.DRAFT))
numbers = [item.registration_number for item in registered]

if len(registered) < 2:
    raise SystemExit("Expected at least two registered demo documents.")
if len(drafts) < 1:
    raise SystemExit("Expected at least one demo draft.")
if len(numbers) != len(set(numbers)):
    raise SystemExit("Registered document numbers are not unique.")
if not DocumentLink.objects.exists():
    raise SystemExit("Typed document link is missing.")
if not AuditEvent.objects.filter(
    event_type=AuditEvent.EventType.DOCUMENT_REGISTERED
).exists():
    raise SystemExit("Registration audit event is missing.")

sequence = DocumentNumberSequence.objects.get(
    organization=registered[0].organization,
    document_type=registered[0].document_type,
    year=registered[0].registration_year,
)
if sequence.last_value < max(item.sequence_number for item in registered):
    raise SystemExit("Server number sequence is behind registered documents.")

immutable_document = registered[0]
original_title = immutable_document.title
immutable_document.title = "Недопустимое изменение"
try:
    immutable_document.save()
except ValidationError:
    pass
else:
    raise SystemExit("Registered document mutation was not blocked.")
immutable_document.refresh_from_db()
if immutable_document.title != original_title:
    raise SystemExit("Registered document content changed after rejected save.")

version = DocumentVersion.objects.get(pk=immutable_document.current_version_id)
try:
    version.delete()
except ValidationError:
    pass
else:
    raise SystemExit("Registered document version deletion was not blocked.")

try:
    Document.objects.filter(pk=immutable_document.pk).delete()
except ValidationError:
    pass
else:
    raise SystemExit("Document queryset deletion was not blocked.")

try:
    AuditEvent.objects.filter(document=immutable_document).update(payload={"tampered": True})
except ValidationError:
    pass
else:
    raise SystemExit("Audit event bulk mutation was not blocked.")

service_source = inspect.getsource(services.register_document)
if "transaction.atomic" not in service_source:
    raise SystemExit("Registration service is not transactional.")
if "select_for_update" not in service_source:
    raise SystemExit("Registration service does not lock rows.")

print(f"DATABASE_VENDOR={connection.vendor}")
print(f"DOCUMENT_COUNT={documents.count()}")
print(f"REGISTERED_COUNT={len(registered)}")
print(f"DRAFT_COUNT={len(drafts)}")
print(f"AUDIT_EVENT_COUNT={AuditEvent.objects.count()}")
print(f"DOCUMENT_LINK_COUNT={DocumentLink.objects.count()}")
print(f"SEQUENCE_LAST_VALUE={sequence.last_value}")
if connection.vendor == "postgresql":
    print("CONCURRENCY_GATE=POSTGRESQL_TRANSACTION_TEST_ENABLED")
else:
    print("CONCURRENCY_GATE=DEFERRED_TO_POSTGRESQL")
print("PATCH_003_DOCUMENT_CORE_GATE_PASSED")
