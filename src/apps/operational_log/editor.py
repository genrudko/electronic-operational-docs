from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any

from django.core.exceptions import ValidationError

EDITOR_SCHEMA_VERSION = "operational-draft-editor.v3"
LEGACY_EDITOR_SCHEMA_VERSIONS = frozenset(
    {
        "operational-draft-editor.v1",
        "operational-draft-editor.v2",
    }
)
SUPPORTED_EDITOR_SCHEMA_VERSIONS = frozenset(
    {EDITOR_SCHEMA_VERSION, *LEGACY_EDITOR_SCHEMA_VERSIONS}
)
MAX_EDITOR_TEXT_LENGTH = 20_000
MAX_EDITOR_JSON_LENGTH = 100_000
MAX_BLOCKS = 250
MAX_LIST_ITEMS = 500
MAX_SEGMENTS = 4_000
MAX_REFERENCE_LABEL_LENGTH = 500
MAX_REFERENCE_VALUE_LENGTH = 200
ALLOWED_BLOCK_TYPES = frozenset(
    {"paragraph", "bullet_list", "ordered_list"}
)
ALLOWED_MARKS = frozenset({"bold", "underline"})
MARK_ORDER = {"bold": 0, "underline": 1}
ENTRY_KIND_LABELS = {
    "normal": "Обычная запись",
    "command": "Команда",
    "permission": "Разрешение",
    "message": "Сообщение",
    "warning": "Предупреждение",
    "carryover": "На следующую смену",
}
ENTRY_KIND_PREFIXES = {
    "normal": "",
    "command": "Команда: ",
    "permission": "Разрешение: ",
    "message": "Сообщение: ",
    "warning": "Предупреждение: ",
    "carryover": "На следующую смену: ",
}
ALLOWED_ENTRY_KINDS = frozenset(ENTRY_KIND_LABELS)
REFERENCE_KIND_LABELS = {
    "equipment": "Оборудование",
    "document": "Документ",
    "person": "Сотрудник или должность",
    "event_time": "Время события",
    "related_entry": "Связанная запись",
}
ALLOWED_REFERENCE_KINDS = frozenset(REFERENCE_KIND_LABELS)
LEGACY_SEMANTIC_KINDS = frozenset(
    {*ALLOWED_ENTRY_KINDS - {"normal"}, *ALLOWED_REFERENCE_KINDS}
)


def _validation_error(message: str) -> ValidationError:
    return ValidationError(message)


def _assert_exact_keys(
    value: Mapping[str, Any],
    allowed: set[str],
    label: str,
) -> None:
    unknown = set(value) - allowed
    if unknown:
        raise _validation_error(
            f"{label}: неизвестные поля {', '.join(sorted(unknown))}."
        )


def _normalize_marks(value: Any) -> list[str]:
    if value in (None, ""):
        return []
    if (
        not isinstance(value, Sequence)
        or isinstance(value, (str, bytes, bytearray))
    ):
        raise _validation_error("Форматирование сегмента должно быть списком.")
    result: list[str] = []
    for item in value:
        if not isinstance(item, str) or item not in ALLOWED_MARKS:
            raise _validation_error(
                "Допустимы только полужирное и подчёркивание."
            )
        if item not in result:
            result.append(item)
    return sorted(result, key=MARK_ORDER.__getitem__)


def _normalize_single_line(
    value: Any,
    *,
    label: str,
    max_length: int,
    required: bool,
) -> str:
    if not isinstance(value, str):
        raise _validation_error(f"{label} должно быть строкой.")
    normalized = " ".join(
        value.replace("\r\n", "\n").replace("\r", "\n").split()
    ).strip()
    if "\x00" in normalized:
        raise _validation_error(f"{label} содержит недопустимый символ.")
    if required and not normalized:
        raise _validation_error(f"{label} не должно быть пустым.")
    if len(normalized) > max_length:
        raise _validation_error(
            f"{label} не должно превышать {max_length} символов."
        )
    return normalized


def _normalize_entry_kind(value: Any) -> str:
    if not isinstance(value, str) or value not in ALLOWED_ENTRY_KINDS:
        raise _validation_error("Неизвестный тип записи оперативного журнала.")
    return value


def _normalize_reference(value: Any) -> dict[str, str]:
    if not isinstance(value, Mapping):
        raise _validation_error("Связанный объект должен быть JSON-объектом.")
    _assert_exact_keys(
        value,
        {"kind", "label", "reference"},
        "Связанный объект",
    )
    kind = value.get("kind")
    if not isinstance(kind, str) or kind not in ALLOWED_REFERENCE_KINDS:
        raise _validation_error("Неизвестный вид связанного объекта.")
    label = _normalize_single_line(
        value.get("label", ""),
        label="Отображаемый текст связанного объекта",
        max_length=MAX_REFERENCE_LABEL_LENGTH,
        required=True,
    )
    reference = _normalize_single_line(
        value.get("reference", ""),
        label="Идентификатор связанного объекта",
        max_length=MAX_REFERENCE_VALUE_LENGTH,
        required=False,
    )
    result = {"kind": kind, "label": label}
    if reference:
        result["reference"] = reference
    return result


def _legacy_semantic_projection(value: Mapping[str, Any]) -> str:
    kind = str(value.get("kind", ""))
    label = str(value.get("label", ""))
    return ENTRY_KIND_PREFIXES.get(kind, "") + label


def _normalize_legacy_semantic(value: Any) -> dict[str, str]:
    if not isinstance(value, Mapping):
        raise _validation_error(
            "Семантическая отметка старой версии должна быть JSON-объектом."
        )
    _assert_exact_keys(
        value,
        {"kind", "label", "reference"},
        "Семантическая отметка старой версии",
    )
    kind = value.get("kind")
    if not isinstance(kind, str) or kind not in LEGACY_SEMANTIC_KINDS:
        raise _validation_error("Неизвестный вид семантической отметки.")
    label = _normalize_single_line(
        value.get("label", ""),
        label="Подпись семантической отметки",
        max_length=MAX_REFERENCE_LABEL_LENGTH,
        required=True,
    )
    reference = _normalize_single_line(
        value.get("reference", ""),
        label="Ссылка семантической отметки",
        max_length=MAX_REFERENCE_VALUE_LENGTH,
        required=False,
    )
    result = {"kind": kind, "label": label}
    if reference:
        result["reference"] = reference
    return result


def _normalize_segments(value: Any) -> list[dict[str, Any]]:
    if value in (None, ""):
        return []
    if (
        not isinstance(value, Sequence)
        or isinstance(value, (str, bytes, bytearray))
    ):
        raise _validation_error("Сегменты текста должны быть списком.")
    if len(value) > MAX_SEGMENTS:
        raise _validation_error("В записи слишком много текстовых сегментов.")

    result: list[dict[str, Any]] = []
    for raw_segment in value:
        if not isinstance(raw_segment, Mapping):
            raise _validation_error(
                "Каждый сегмент должен быть JSON-объектом."
            )
        _assert_exact_keys(
            raw_segment,
            {"text", "marks", "reference"},
            "Сегмент текста",
        )
        marks = _normalize_marks(raw_segment.get("marks", []))
        reference_value = raw_segment.get("reference")
        if reference_value not in (None, "", {}):
            reference = _normalize_reference(reference_value)
            result.append(
                {
                    "text": reference["label"],
                    "marks": marks,
                    "reference": reference,
                }
            )
            continue

        text = raw_segment.get("text", "")
        if not isinstance(text, str):
            raise _validation_error("Текст сегмента должен быть строкой.")
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        if "\x00" in text:
            raise _validation_error(
                "Текст содержит недопустимый нулевой символ."
            )
        if not text:
            continue
        if (
            result
            and "reference" not in result[-1]
            and result[-1]["marks"] == marks
        ):
            result[-1]["text"] += text
        else:
            result.append({"text": text, "marks": marks})
    return result


def _upgrade_legacy_segments(
    value: Any,
    *,
    entry_kind: str,
) -> tuple[list[dict[str, Any]], str]:
    if value in (None, ""):
        return [], entry_kind
    if (
        not isinstance(value, Sequence)
        or isinstance(value, (str, bytes, bytearray))
    ):
        raise _validation_error("Сегменты текста должны быть списком.")
    upgraded: list[dict[str, Any]] = []
    current_entry_kind = entry_kind
    for raw_segment in value:
        if not isinstance(raw_segment, Mapping):
            raise _validation_error(
                "Каждый сегмент должен быть JSON-объектом."
            )
        _assert_exact_keys(
            raw_segment,
            {"text", "marks", "semantic"},
            "Сегмент старой версии",
        )
        marks = _normalize_marks(raw_segment.get("marks", []))
        semantic_value = raw_segment.get("semantic")
        if semantic_value not in (None, "", {}):
            semantic = _normalize_legacy_semantic(semantic_value)
            kind = semantic["kind"]
            if kind in ALLOWED_ENTRY_KINDS and kind != "normal":
                if current_entry_kind == "normal":
                    current_entry_kind = kind
                    upgraded.append(
                        {"text": semantic["label"], "marks": marks}
                    )
                else:
                    upgraded.append(
                        {
                            "text": _legacy_semantic_projection(semantic),
                            "marks": marks,
                        }
                    )
                continue
            reference = {
                "kind": kind,
                "label": semantic["label"],
            }
            if semantic.get("reference"):
                reference["reference"] = semantic["reference"]
            upgraded.append(
                {
                    "text": semantic["label"],
                    "marks": marks,
                    "reference": reference,
                }
            )
            continue
        text = raw_segment.get("text", "")
        if not isinstance(text, str):
            raise _validation_error("Текст сегмента должен быть строкой.")
        upgraded.append({"text": text, "marks": marks})
    return upgraded, current_entry_kind


def plain_text_to_editor_document(value: str) -> dict[str, Any]:
    text = str(value or "").replace("\r\n", "\n").replace("\r", "\n")
    blocks = []
    for line in text.split("\n"):
        segments = [{"text": line, "marks": []}] if line else []
        blocks.append({"type": "paragraph", "segments": segments})
    return {
        "schema_version": EDITOR_SCHEMA_VERSION,
        "entry_kind": "normal",
        "blocks": blocks or [{"type": "paragraph", "segments": []}],
    }


def _normalize_block(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise _validation_error(
            "Каждый блок редактора должен быть JSON-объектом."
        )
    block_type = value.get("type")
    if block_type not in ALLOWED_BLOCK_TYPES:
        raise _validation_error("Неизвестный тип блока редактора.")

    if block_type == "paragraph":
        _assert_exact_keys(value, {"type", "segments"}, "Абзац")
        return {
            "type": "paragraph",
            "segments": _normalize_segments(value.get("segments", [])),
        }

    _assert_exact_keys(value, {"type", "items"}, "Список")
    items = value.get("items", [])
    if (
        not isinstance(items, Sequence)
        or isinstance(items, (str, bytes, bytearray))
    ):
        raise _validation_error("Элементы списка должны быть списком.")
    if len(items) > MAX_LIST_ITEMS:
        raise _validation_error("В записи слишком много элементов списка.")
    normalized_items = []
    for raw_item in items:
        if not isinstance(raw_item, Mapping):
            raise _validation_error(
                "Каждый элемент списка должен быть JSON-объектом."
            )
        _assert_exact_keys(raw_item, {"segments"}, "Элемент списка")
        normalized_items.append(
            {"segments": _normalize_segments(raw_item.get("segments", []))}
        )
    return {"type": block_type, "items": normalized_items}


def _upgrade_legacy_block(
    value: Any,
    *,
    entry_kind: str,
) -> tuple[dict[str, Any], str]:
    if not isinstance(value, Mapping):
        raise _validation_error(
            "Каждый блок редактора должен быть JSON-объектом."
        )
    block_type = value.get("type")
    if block_type == "paragraph":
        _assert_exact_keys(value, {"type", "segments"}, "Абзац")
        segments, entry_kind = _upgrade_legacy_segments(
            value.get("segments", []),
            entry_kind=entry_kind,
        )
        return {"type": "paragraph", "segments": segments}, entry_kind
    if block_type not in {"bullet_list", "ordered_list"}:
        raise _validation_error("Неизвестный тип блока редактора.")
    _assert_exact_keys(value, {"type", "items"}, "Список")
    items = value.get("items", [])
    if not isinstance(items, Sequence) or isinstance(items, (str, bytes)):
        raise _validation_error("Элементы списка должны быть списком.")
    upgraded_items = []
    current_entry_kind = entry_kind
    for raw_item in items:
        if not isinstance(raw_item, Mapping):
            raise _validation_error(
                "Каждый элемент списка должен быть JSON-объектом."
            )
        _assert_exact_keys(raw_item, {"segments"}, "Элемент списка")
        segments, current_entry_kind = _upgrade_legacy_segments(
            raw_item.get("segments", []),
            entry_kind=current_entry_kind,
        )
        upgraded_items.append({"segments": segments})
    return (
        {"type": block_type, "items": upgraded_items},
        current_entry_kind,
    )


def editor_document_to_text(value: Mapping[str, Any]) -> str:
    lines: list[str] = []
    for block in value.get("blocks", []):
        block_type = block.get("type")
        if block_type == "paragraph":
            lines.append(
                "".join(segment["text"] for segment in block["segments"])
            )
            continue
        for index, item in enumerate(block.get("items", []), start=1):
            item_text = "".join(
                segment["text"] for segment in item["segments"]
            )
            prefix = "• " if block_type == "bullet_list" else f"{index}. "
            lines.append(prefix + item_text)
    body = "\n".join(lines)
    if not body.strip():
        return body
    entry_kind = str(value.get("entry_kind", "normal"))
    prefix = ENTRY_KIND_PREFIXES.get(entry_kind, "")
    if not prefix:
        return body
    for index, line in enumerate(lines):
        if line.strip():
            lines[index] = prefix + line
            break
    return "\n".join(lines)


def normalize_editor_document(
    value: Any,
    *,
    fallback_text: str = "",
) -> dict[str, Any]:
    if value in (None, "", {}):
        document = plain_text_to_editor_document(fallback_text)
    else:
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError as error:
                raise _validation_error(
                    "Структура редактора содержит некорректный JSON."
                ) from error
        if not isinstance(value, Mapping):
            raise _validation_error(
                "Структура редактора должна быть JSON-объектом."
            )
        schema_version = value.get("schema_version")
        if schema_version not in SUPPORTED_EDITOR_SCHEMA_VERSIONS:
            raise _validation_error("Неизвестная версия структуры редактора.")
        blocks = value.get("blocks")
        if (
            not isinstance(blocks, Sequence)
            or isinstance(blocks, (str, bytes, bytearray))
        ):
            raise _validation_error("Блоки редактора должны быть списком.")
        if len(blocks) > MAX_BLOCKS:
            raise _validation_error("В записи слишком много блоков.")

        if schema_version == EDITOR_SCHEMA_VERSION:
            _assert_exact_keys(
                value,
                {"schema_version", "entry_kind", "blocks"},
                "Документ редактора",
            )
            entry_kind = _normalize_entry_kind(
                value.get("entry_kind", "normal")
            )
            normalized_blocks = [_normalize_block(block) for block in blocks]
        else:
            _assert_exact_keys(
                value,
                {"schema_version", "blocks"},
                "Документ редактора старой версии",
            )
            entry_kind = "normal"
            upgraded_blocks = []
            for block in blocks:
                upgraded, entry_kind = _upgrade_legacy_block(
                    block,
                    entry_kind=entry_kind,
                )
                upgraded_blocks.append(upgraded)
            normalized_blocks = [
                _normalize_block(block) for block in upgraded_blocks
            ]

        document = {
            "schema_version": EDITOR_SCHEMA_VERSION,
            "entry_kind": entry_kind,
            "blocks": normalized_blocks,
        }
        if not document["blocks"]:
            document["blocks"] = [
                {"type": "paragraph", "segments": []}
            ]

    projection = editor_document_to_text(document)
    if len(projection) > MAX_EDITOR_TEXT_LENGTH:
        raise _validation_error(
            f"Содержание записи не должно превышать "
            f"{MAX_EDITOR_TEXT_LENGTH} символов."
        )
    serialized = serialize_editor_document(document)
    if len(serialized) > MAX_EDITOR_JSON_LENGTH:
        raise _validation_error("Структура редактора слишком велика.")
    return document


def serialize_editor_document(value: Mapping[str, Any]) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
