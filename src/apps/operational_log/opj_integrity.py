from __future__ import annotations

from typing import Any

from django.core.exceptions import ValidationError

from .models import OperationalLogAuditEvent, OperationalLogEntry
from .services import canonical_json, sha256_text, utc_iso


def _registered_audit(entry: OperationalLogEntry) -> OperationalLogAuditEvent:
    event = entry.audit_events.filter(
        event_type=OperationalLogAuditEvent.EventType.ENTRY_REGISTERED,
    ).first()
    if event is None:
        raise ValidationError("Для записи отсутствует событие регистрации.")
    return event


def _expect_equal(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        raise ValidationError(f"Нарушена целостность: {label}.")


def _snapshot_rows_by_id(rows: Any, id_key: str) -> dict[int, dict[str, Any]]:
    result: dict[int, dict[str, Any]] = {}
    for row in rows if isinstance(rows, list) else []:
        if not isinstance(row, dict):
            continue
        try:
            row_id = int(row[id_key])
        except (KeyError, TypeError, ValueError):
            continue
        result[row_id] = row
    return result


def verify_registered_snapshot(entry: OperationalLogEntry) -> bool:
    """Verify a registered OPJ entry against its frozen audit snapshot.

    Mutable directory labels (current workplace, journal title, current equipment
    or document names) are deliberately not reconstructed.  The registration
    audit snapshot is the canonical source for frozen labels; current database
    objects are checked only through stable identities and the snapshot fields
    persisted on append-only link rows.
    """

    event = _registered_audit(entry)
    snapshot = event.snapshot if isinstance(event.snapshot, dict) else {}
    if not snapshot:
        raise ValidationError("Снимок зарегистрированной записи отсутствует.")

    snapshot_digest = sha256_text(canonical_json(snapshot))
    _expect_equal(snapshot_digest, entry.digest, "контрольная сумма снимка")
    _expect_equal(event.digest, entry.digest, "контрольная сумма события")

    journal = snapshot.get("journal") if isinstance(snapshot.get("journal"), dict) else {}
    _expect_equal(journal.get("id"), entry.journal_id, "идентификатор журнала")
    _expect_equal(journal.get("code"), entry.journal.code, "код журнала")
    _expect_equal(
        journal.get("organization_id"),
        entry.journal.organization_id,
        "организация журнала",
    )
    _expect_equal(
        journal.get("workplace_id"),
        entry.journal.workplace_id,
        "рабочее место журнала",
    )

    payload = snapshot.get("entry") if isinstance(snapshot.get("entry"), dict) else {}
    _expect_equal(payload.get("sequence_number"), entry.sequence_number, "номер записи")
    _expect_equal(payload.get("event_at"), utc_iso(entry.event_at), "время события")
    _expect_equal(
        payload.get("registered_at"),
        utc_iso(entry.registered_at),
        "время регистрации",
    )
    _expect_equal(payload.get("entry_form"), entry.entry_form, "форма записи")
    _expect_equal(payload.get("type_code"), entry.type_code, "код типа")
    _expect_equal(payload.get("type_title"), entry.type_title, "наименование типа")
    _expect_equal(payload.get("content"), entry.content, "содержание")
    _expect_equal(payload.get("typed_payload"), entry.typed_payload, "типизированные данные")

    author = snapshot.get("author") if isinstance(snapshot.get("author"), dict) else {}
    _expect_equal(author.get("employee_id"), entry.author_id, "автор")
    _expect_equal(
        author.get("full_name"),
        entry.author_full_name_snapshot,
        "ФИО автора",
    )
    _expect_equal(
        author.get("position"),
        entry.author_position_snapshot,
        "должность автора",
    )
    _expect_equal(
        author.get("workplace"),
        entry.author_workplace_snapshot,
        "рабочее место автора",
    )

    expected_equipment = _snapshot_rows_by_id(snapshot.get("equipment"), "equipment_id")
    actual_equipment = {
        link.equipment_id: link
        for link in entry.equipment_links.all()
    }
    _expect_equal(set(actual_equipment), set(expected_equipment), "состав оборудования")
    for item_id, link in actual_equipment.items():
        frozen = expected_equipment[item_id]
        _expect_equal(
            frozen.get("code"),
            link.equipment_code_snapshot,
            "код оборудования",
        )
        _expect_equal(
            frozen.get("dispatcher_name"),
            link.dispatcher_name_snapshot,
            "диспетчерское наименование",
        )
        _expect_equal(
            frozen.get("site"),
            link.site_name_snapshot,
            "энергообъект оборудования",
        )

    expected_documents = _snapshot_rows_by_id(snapshot.get("documents"), "document_id")
    actual_documents = {
        link.document_id: link
        for link in entry.document_links.all()
    }
    _expect_equal(set(actual_documents), set(expected_documents), "состав документов")
    for item_id, link in actual_documents.items():
        frozen = expected_documents[item_id]
        _expect_equal(
            frozen.get("registration_number"),
            link.registration_number_snapshot,
            "регистрационный номер документа",
        )
        _expect_equal(
            frozen.get("title"),
            link.title_snapshot,
            "наименование документа",
        )

    return True
