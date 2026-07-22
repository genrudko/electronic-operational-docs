"""Unicode-stable search helpers for power-system staging rows."""

from __future__ import annotations

import json
import unicodedata
from collections.abc import Iterable, Mapping
from typing import Any

from django.db.models import QuerySet

_SEARCHABLE_INTERNAL_TYPES = frozenset(
    {
        "CharField",
        "TextField",
        "JSONField",
        "IntegerField",
        "PositiveIntegerField",
        "PositiveSmallIntegerField",
        "SmallIntegerField",
        "BigIntegerField",
    }
)


def unicode_casefold(value: object) -> str:
    """Return a compatibility-normalized, case-insensitive Unicode string."""

    if value is None:
        return ""
    return unicodedata.normalize("NFKC", str(value)).casefold()


def _iter_search_text(value: Any) -> Iterable[str]:
    if value is None:
        return
    if isinstance(value, Mapping):
        for key, nested in value.items():
            yield str(key)
            yield from _iter_search_text(nested)
        return
    if isinstance(value, (list, tuple, set, frozenset)):
        for nested in value:
            yield from _iter_search_text(nested)
        return
    if isinstance(value, str):
        yield value
        return
    if isinstance(value, (int, float, bool)):
        yield str(value)
        return
    try:
        rendered = json.dumps(value, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        rendered = str(value)
    yield rendered


def unicode_text_matches(value: Any, query: str) -> bool:
    """Return True when *query* occurs in *value* after NFKC + casefold."""

    folded_query = unicode_casefold(query).strip()
    if not folded_query:
        return True
    return any(folded_query in unicode_casefold(part) for part in _iter_search_text(value))


def _searchable_field_names(queryset: QuerySet) -> tuple[str, ...]:
    names: list[str] = []
    for field in queryset.model._meta.concrete_fields:
        if field.primary_key or field.is_relation:
            continue
        if field.get_internal_type() not in _SEARCHABLE_INTERNAL_TYPES:
            continue
        names.append(field.name)
    return tuple(names)


def filter_power_system_occurrences(queryset: QuerySet, query: str) -> QuerySet:
    """Filter a staging queryset with database-independent Unicode semantics.

    SQLite's default LIKE/NOCASE implementation is ASCII-oriented, therefore
    Django ``icontains`` does not reliably equate ``шот`` and ``ШОТ``. The
    current status/type queryset is projected to scalar values, compared in
    Python with NFKC + casefold, and then restricted by matching primary keys.
    The returned object remains a QuerySet, preserving its ordering and
    compatibility with the existing paginator.
    """

    folded_query = unicode_casefold(query).strip()
    if not folded_query:
        return queryset

    field_names = _searchable_field_names(queryset)
    if not field_names:
        return queryset.none()

    matched_ids: list[object] = []
    columns = ("pk", *field_names)
    for values in queryset.values_list(*columns).iterator(chunk_size=500):
        primary_key, *search_values = values
        if any(
            folded_query in unicode_casefold(part)
            for value in search_values
            for part in _iter_search_text(value)
        ):
            matched_ids.append(primary_key)

    if not matched_ids:
        return queryset.none()
    return queryset.filter(pk__in=matched_ids)
