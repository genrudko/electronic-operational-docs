from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any

from django.core.exceptions import ValidationError

EDITOR_SCHEMA_VERSION = "operational-draft-editor.v1"
MAX_EDITOR_TEXT_LENGTH = 20_000
MAX_EDITOR_JSON_LENGTH = 100_000
MAX_BLOCKS = 250
MAX_LIST_ITEMS = 500
MAX_SEGMENTS = 4_000
ALLOWED_BLOCK_TYPES = frozenset(
    {"paragraph", "bullet_list", "ordered_list"}
)
ALLOWED_MARKS = frozenset({"bold", "underline"})
MARK_ORDER = {"bold": 0, "underline": 1}


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
            {"text", "marks"},
            "Сегмент текста",
        )
        text = raw_segment.get("text", "")
        if not isinstance(text, str):
            raise _validation_error("Текст сегмента должен быть строкой.")
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        if "\x00" in text:
            raise _validation_error(
                "Текст содержит недопустимый нулевой символ."
            )
        marks = _normalize_marks(raw_segment.get("marks", []))
        if not text:
            continue
        if result and result[-1]["marks"] == marks:
            result[-1]["text"] += text
        else:
            result.append({"text": text, "marks": marks})
    return result


def plain_text_to_editor_document(value: str) -> dict[str, Any]:
    text = str(value or "").replace("\r\n", "\n").replace("\r", "\n")
    blocks = []
    for line in text.split("\n"):
        segments = [{"text": line, "marks": []}] if line else []
        blocks.append({"type": "paragraph", "segments": segments})
    return {
        "schema_version": EDITOR_SCHEMA_VERSION,
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
        _assert_exact_keys(
            value,
            {"schema_version", "blocks"},
            "Документ редактора",
        )
        if value.get("schema_version") != EDITOR_SCHEMA_VERSION:
            raise _validation_error("Неизвестная версия структуры редактора.")
        blocks = value.get("blocks")
        if (
            not isinstance(blocks, Sequence)
            or isinstance(blocks, (str, bytes, bytearray))
        ):
            raise _validation_error("Блоки редактора должны быть списком.")
        if len(blocks) > MAX_BLOCKS:
            raise _validation_error("В записи слишком много блоков.")
        document = {
            "schema_version": EDITOR_SCHEMA_VERSION,
            "blocks": [_normalize_block(block) for block in blocks],
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
