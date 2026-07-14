
from __future__ import annotations

import hashlib
import json
from datetime import UTC

from django.db import migrations
from django.utils import timezone

SNAPSHOT_SCHEMA = "eod.document.registration.v1"
SIGNATURE_SCHEMA = "eod.document.signature.v1"


def _iso(value):
    if value is None:
        return None
    if hasattr(value, "astimezone"):
        if timezone.is_naive(value):
            value = timezone.make_aware(value, timezone.get_current_timezone())
        return value.astimezone(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")
    return value


def _safe(value):
    if isinstance(value, dict):
        return {str(key): _safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_safe(item) for item in value]
    converted = _iso(value)
    if converted is not value:
        return converted
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def _canonical(value):
    return json.dumps(_safe(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _sha(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _employee(employee):
    if employee is None:
        return {
            "employee_id": None,
            "personnel_number": "",
            "full_name": "",
            "position": "",
            "division": "",
            "workplace": "",
        }
    full_name = " ".join(
        part for part in (employee.last_name, employee.first_name, employee.middle_name) if part
    )
    return {
        "employee_id": employee.pk,
        "personnel_number": employee.personnel_number,
        "full_name": full_name,
        "position": employee.position.name if employee.position_id else "",
        "division": employee.division.name if employee.division_id else "",
        "workplace": employee.workplace.name if employee.workplace_id else "",
    }


def forwards(apps, schema_editor):
    Document = apps.get_model("documents", "Document")
    DocumentVersion = apps.get_model("documents", "DocumentVersion")
    SignedSnapshot = apps.get_model("documents", "SignedSnapshot")
    DocumentSignature = apps.get_model("documents", "DocumentSignature")
    AuditEvent = apps.get_model("documents", "AuditEvent")
    documents = Document.objects.filter(status="REGISTERED").select_related(
        "organization",
        "document_type",
        "created_by__position",
        "created_by__division",
        "created_by__workplace",
        "registered_by__position",
        "registered_by__division",
        "registered_by__workplace",
        "registered_by__user",
    )
    for document in documents.iterator():
        if document.current_version_id is None:
            continue
        if SignedSnapshot.objects.filter(
            document_id=document.pk,
            document_version_id=document.current_version_id,
            purpose="REGISTRATION",
        ).exists():
            continue
        version = DocumentVersion.objects.get(pk=document.current_version_id)
        actor = document.registered_by
        roles = []
        migrated_at = timezone.now()
        context = {
            "organization": {
                "id": document.organization_id,
                "code": document.organization.code,
                "name": document.organization.name,
                "short_name": document.organization.short_name,
            },
            "document_type": {
                "id": document.document_type_id,
                "code": document.document_type.code,
                "name": document.document_type.name,
                "number_prefix": document.document_type.number_prefix,
            },
            "created_by": _employee(document.created_by),
            "registered_by": _employee(actor),
            "effective_roles": roles,
            "legacy_migration": {
                "migrated_at": migrated_at,
                "repeat_authentication_performed": False,
                "effective_roles_reconstructed": False,
                "identity_quality": "best_available_directory_values_at_migration",
            },
        }
        payload = {
            "schema": SNAPSHOT_SCHEMA,
            "purpose": "REGISTRATION",
            "document": {
                "id": document.pk,
                "public_id": str(document.public_id),
                "organization_id": document.organization_id,
                "document_type_id": document.document_type_id,
                "title": document.title,
                "status": document.status,
                "current_version_id": document.current_version_id,
                "registration_year": document.registration_year,
                "sequence_number": document.sequence_number,
                "registration_number": document.registration_number,
                "registered_at": document.registered_at,
                "registered_by_id": document.registered_by_id,
            },
            "version": {
                "id": version.pk,
                "document_id": version.document_id,
                "version_number": version.version_number,
                "status": version.status,
                "title": version.title,
                "content": version.content,
                "registered_at": version.registered_at,
                "registered_by_id": version.registered_by_id,
            },
            "historical_context": context,
        }
        canonical = _canonical(payload)
        digest = _sha(canonical)
        snapshot = SignedSnapshot.objects.create(
            document_id=document.pk,
            document_version_id=version.pk,
            purpose="REGISTRATION",
            schema_version=SNAPSHOT_SCHEMA,
            canonical_json=canonical,
            hash_algorithm="SHA-256",
            digest=digest,
            created_at=migrated_at,
        )
        identity = _employee(actor)
        user = actor.user if actor is not None and actor.user_id else None
        username = user.username if user is not None else ""
        signature_payload = {
            "schema": SIGNATURE_SCHEMA,
            "snapshot_digest": digest,
            "purpose": "REGISTRATION",
            "confirmation_method": "LEGACY_MIGRATION",
            "user_id": user.pk if user is not None else None,
            "employee_id": actor.pk if actor is not None else None,
            "username_snapshot": username,
            "full_name_snapshot": identity["full_name"],
            "position_snapshot": identity["position"],
            "division_snapshot": identity["division"],
            "workplace_snapshot": identity["workplace"],
            "roles_snapshot": roles,
            "signed_at": migrated_at,
        }
        checksum = _sha(_canonical(signature_payload))
        signature = DocumentSignature.objects.create(
            snapshot_id=snapshot.pk,
            purpose="REGISTRATION",
            confirmation_method="LEGACY_MIGRATION",
            user_id=user.pk if user is not None else None,
            employee_id=actor.pk if actor is not None else None,
            username_snapshot=username,
            full_name_snapshot=identity["full_name"],
            position_snapshot=identity["position"],
            division_snapshot=identity["division"],
            workplace_snapshot=identity["workplace"],
            roles_snapshot=roles,
            signed_at=migrated_at,
            checksum_algorithm="SHA-256",
            checksum=checksum,
        )
        AuditEvent.objects.create(
            organization_id=document.organization_id,
            event_type="LEGACY_SIGNATURE_MIGRATED",
            occurred_at=migrated_at,
            actor_user_id=None,
            actor_employee_id=None,
            document_id=document.pk,
            document_version_id=version.pk,
            entity_type="document_signature",
            entity_id=str(signature.pk),
            payload={
                "confirmation_method": "LEGACY_MIGRATION",
                "snapshot_digest": digest,
                "signature_checksum": checksum,
                "effective_roles_reconstructed": False,
                "repeat_authentication_performed": False,
            },
        )


def backwards(apps, schema_editor):
    AuditEvent = apps.get_model("documents", "AuditEvent")
    DocumentSignature = apps.get_model("documents", "DocumentSignature")
    SignedSnapshot = apps.get_model("documents", "SignedSnapshot")
    legacy_ids = list(
        DocumentSignature.objects.filter(confirmation_method="LEGACY_MIGRATION").values_list("pk", flat=True)
    )
    AuditEvent.objects.filter(
        event_type="LEGACY_SIGNATURE_MIGRATED",
        entity_type="document_signature",
        entity_id__in=[str(item) for item in legacy_ids],
    ).delete()
    snapshot_ids = list(
        DocumentSignature.objects.filter(pk__in=legacy_ids).values_list("snapshot_id", flat=True)
    )
    DocumentSignature.objects.filter(pk__in=legacy_ids).delete()
    SignedSnapshot.objects.filter(pk__in=snapshot_ids).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("documents", "0002_signature_integrity"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
