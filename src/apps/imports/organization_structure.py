from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from typing import TYPE_CHECKING

from django.core.exceptions import ValidationError
from django.db.models import Model

from apps.equipment.models import EnergySite
from apps.organizations.models import Division, Workplace

if TYPE_CHECKING:
    from .models import ImportBatch, ImportRow


DIVISION = "DIVISION"
WORKPLACE = "WORKPLACE"
ENERGY_SITE = "ENERGY_SITE"
STRUCTURE_KIND_CHOICES = (
    (DIVISION, "Подразделение"),
    (WORKPLACE, "Рабочее место"),
    (ENERGY_SITE, "Энергообъект"),
)


def _token(value: str) -> str:
    return " ".join(str(value or "").replace("\u00a0", " ").split()).casefold()


def _yes(value: str, *, default: bool) -> bool:
    token = _token(value)
    if not token:
        return default
    if token in {"да", "1", "true", "yes", "y", "on", "истина"}:
        return True
    if token in {"нет", "0", "false", "no", "n", "off", "ложь"}:
        return False
    raise ValidationError("Логическое значение не удалось преобразовать.")


@dataclass(frozen=True, slots=True)
class StructureRegistryContext:
    existing_codes: dict[str, frozenset[str]]
    active_names: dict[str, dict[str, tuple[str, ...]]]
    division_codes: frozenset[str]


def build_registry_context(batch: ImportBatch) -> StructureRegistryContext:
    organization = batch.organization
    existing_codes: dict[str, frozenset[str]] = {}
    active_names: dict[str, dict[str, tuple[str, ...]]] = {}

    sources: tuple[tuple[str, Iterable[Model]], ...] = (
        (
            DIVISION,
            Division.objects.filter(organization=organization).only(
                "code", "name", "is_active"
            ),
        ),
        (
            WORKPLACE,
            Workplace.objects.filter(organization=organization).only(
                "code", "name", "is_active"
            ),
        ),
        (
            ENERGY_SITE,
            EnergySite.objects.filter(organization=organization).only(
                "code", "name", "is_active"
            ),
        ),
    )
    division_codes: frozenset[str] = frozenset()
    for kind, queryset in sources:
        code_tokens: set[str] = set()
        name_codes: dict[str, list[str]] = defaultdict(list)
        for item in queryset:
            code_token = _token(item.code)
            name_token = _token(item.name)
            code_tokens.add(code_token)
            if name_token and item.is_active:
                name_codes[name_token].append(str(item.code))
        existing_codes[kind] = frozenset(code_tokens)
        active_names[kind] = {
            name: tuple(sorted(codes, key=str.casefold))
            for name, codes in name_codes.items()
        }
        if kind == DIVISION:
            division_codes = frozenset(code_tokens)

    return StructureRegistryContext(
        existing_codes=existing_codes,
        active_names=active_names,
        division_codes=division_codes,
    )


def validate_structure_values(values: dict[str, str]) -> list[str]:
    issues: list[str] = []
    kind = values.get("structure_kind", "")
    code = values.get("code", "")
    name = values.get("name", "")
    parent_code = values.get("parent_code", "")
    division_code = values.get("division_code", "")
    short_name = values.get("short_name", "")
    site_type = values.get("site_type", "")
    is_external = values.get("is_external", "")

    if kind not in {DIVISION, WORKPLACE, ENERGY_SITE}:
        return issues

    if kind in {DIVISION, WORKPLACE}:
        if len(code) > 32:
            issues.append(
                "Код подразделения или рабочего места длиннее допустимых 32 символов."
            )
        if len(name) > 255:
            issues.append(
                "Наименование подразделения или рабочего места длиннее допустимых 255 символов."
            )
    if kind == ENERGY_SITE and len(code) > 64:
        issues.append("Код энергообъекта длиннее допустимых 64 символов.")

    if kind == DIVISION:
        if parent_code and _token(parent_code) == _token(code):
            issues.append("Подразделение не может ссылаться на себя как на родителя.")
        if division_code:
            issues.append("Поле «Код подразделения» не применяется к строке подразделения.")
        if short_name:
            issues.append("Краткое наименование применяется только к энергообъекту.")
        if site_type:
            issues.append("Тип энергообъекта применяется только к энергообъекту.")
        if _token(is_external) == "да":
            issues.append("Признак внешнего объекта применяется только к энергообъекту.")
    elif kind == WORKPLACE:
        if parent_code:
            issues.append("Родительский код применяется только к подразделению.")
        if short_name:
            issues.append("Краткое наименование применяется только к энергообъекту.")
        if site_type:
            issues.append("Тип энергообъекта применяется только к энергообъекту.")
        if _token(is_external) == "да":
            issues.append("Признак внешнего объекта применяется только к энергообъекту.")
    else:
        if parent_code:
            issues.append("Родительский код применяется только к подразделению.")
        if division_code:
            issues.append("Код подразделения применяется только к рабочему месту.")
        if not site_type:
            issues.append("Для энергообъекта требуется тип энергообъекта.")

    return issues


def _append_unique(items: list[str], message: str) -> None:
    if message not in items:
        items.append(message)


def _row_values(row: ImportRow) -> dict[str, str]:
    return {key: str(value or "") for key, value in row.effective_values.items()}


def _cycle_codes(parent_by_code: dict[str, str]) -> set[str]:
    state: dict[str, int] = {}
    stack: list[str] = []
    position: dict[str, int] = {}
    cycles: set[str] = set()

    def visit(code: str) -> None:
        current = state.get(code, 0)
        if current == 2:
            return
        if current == 1:
            cycles.update(stack[position[code] :])
            return
        state[code] = 1
        position[code] = len(stack)
        stack.append(code)
        parent = parent_by_code.get(code, "")
        if parent in parent_by_code:
            visit(parent)
        stack.pop()
        position.pop(code, None)
        state[code] = 2

    for code in sorted(parent_by_code):
        visit(code)
    return cycles


def apply_batch_review(
    *,
    batch: ImportBatch,
    rows: list[ImportRow],
    context: StructureRegistryContext,
) -> None:
    by_key: dict[tuple[str, str], list[ImportRow]] = defaultdict(list)
    by_name: dict[tuple[str, str], list[ImportRow]] = defaultdict(list)
    values_by_row: dict[int, dict[str, str]] = {}

    considered_rows = [
        row
        for row in rows
        if row.decision != row.Decision.REJECTED
        and row.status != row.Status.REJECTED
    ]

    for row in considered_rows:
        values = _row_values(row)
        values_by_row[row.pk or -row.row_number] = values
        kind = values.get("structure_kind", "")
        code_token = _token(values.get("code", ""))
        name_token = _token(values.get("name", ""))
        if kind and code_token:
            by_key[(kind, code_token)].append(row)
        if kind and name_token:
            by_name[(kind, name_token)].append(row)

    for (kind, code_token), matching_rows in sorted(by_key.items()):
        if len(matching_rows) > 1:
            numbers = ", ".join(str(item.row_number) for item in matching_rows)
            message = (
                "Дублирующая пара «вид структуры + код» внутри файла: "
                f"строки {numbers}."
            )
            for row in matching_rows:
                _append_unique(row.registry_conflicts, message)
        if code_token in context.existing_codes.get(kind, frozenset()):
            for row in matching_rows:
                _append_unique(
                    row.registry_conflicts,
                    "Запись этого вида с таким точным кодом уже существует.",
                )

    for (kind, name_token), matching_rows in sorted(by_name.items()):
        distinct_codes = {
            _token(_row_values(row).get("code", "")) for row in matching_rows
        }
        if len(distinct_codes) > 1:
            numbers = ", ".join(str(item.row_number) for item in matching_rows)
            message = (
                "Неоднозначное совпадение наименования внутри файла: "
                f"строки {numbers} содержат разные коды."
            )
            for row in matching_rows:
                _append_unique(row.registry_conflicts, message)
        existing_codes = context.active_names.get(kind, {}).get(name_token, ())
        if existing_codes:
            rendered = ", ".join(existing_codes)
            for row in matching_rows:
                _append_unique(
                    row.registry_conflicts,
                    "Наименование совпадает с действующей записью и не может быть "
                    f"однозначно создано как новая запись (коды: {rendered}).",
                )

    unique_rows: dict[tuple[str, str], ImportRow] = {
        key: matching_rows[0]
        for key, matching_rows in by_key.items()
        if len(matching_rows) == 1
    }
    dependency_by_row: dict[int, ImportRow] = {}
    parent_by_code: dict[str, str] = {}

    for row in considered_rows:
        values = values_by_row[row.pk or -row.row_number]
        kind = values.get("structure_kind", "")
        code_token = _token(values.get("code", ""))
        if kind == DIVISION:
            parent_token = _token(values.get("parent_code", ""))
            if not parent_token:
                continue
            parent_rows = by_key.get((DIVISION, parent_token), [])
            if len(parent_rows) == 1:
                dependency_by_row[row.pk or -row.row_number] = parent_rows[0]
                if code_token:
                    parent_by_code[code_token] = parent_token
            elif len(parent_rows) > 1:
                _append_unique(
                    row.validation_issues,
                    "Родительское подразделение неоднозначно из-за дублирующего кода в файле.",
                )
            elif parent_token not in context.division_codes:
                _append_unique(
                    row.validation_issues,
                    "Родительское подразделение не найдено ни в текущем файле, "
                    "ни в действующем справочнике.",
                )
        elif kind == WORKPLACE:
            division_token = _token(values.get("division_code", ""))
            if not division_token:
                continue
            division_rows = by_key.get((DIVISION, division_token), [])
            if len(division_rows) == 1:
                dependency_by_row[row.pk or -row.row_number] = division_rows[0]
            elif len(division_rows) > 1:
                _append_unique(
                    row.validation_issues,
                    "Подразделение рабочего места неоднозначно из-за дублирующего кода в файле.",
                )
            elif division_token not in context.division_codes:
                _append_unique(
                    row.validation_issues,
                    "Подразделение рабочего места не найдено ни в текущем файле, "
                    "ни в действующем справочнике.",
                )

    cycle_codes = _cycle_codes(parent_by_code)
    if cycle_codes:
        rendered = ", ".join(sorted(cycle_codes))
        for code in cycle_codes:
            row = unique_rows.get((DIVISION, code))
            if row is not None:
                _append_unique(
                    row.validation_issues,
                    f"Обнаружен цикл иерархии подразделений: {rendered}.",
                )

    blocked_ids = {
        row.pk or -row.row_number
        for row in rows
        if row.validation_issues or row.registry_conflicts
    }
    changed = True
    while changed:
        changed = False
        for row in sorted(rows, key=lambda item: item.row_number):
            row_id = row.pk or -row.row_number
            dependency = dependency_by_row.get(row_id)
            if dependency is None:
                continue
            dependency_id = dependency.pk or -dependency.row_number
            if dependency_id in blocked_ids and row_id not in blocked_ids:
                _append_unique(
                    row.validation_issues,
                    "Зависимость в текущем файле заблокирована и не может быть опубликована.",
                )
                blocked_ids.add(row_id)
                changed = True


def _active_conflicts(
    *,
    values: dict[str, str],
    context: StructureRegistryContext,
) -> list[str]:
    kind = values.get("structure_kind", "")
    code_token = _token(values.get("code", ""))
    name_token = _token(values.get("name", ""))
    conflicts: list[str] = []
    if code_token and code_token in context.existing_codes.get(kind, frozenset()):
        conflicts.append("Запись этого вида с таким точным кодом уже существует.")
    existing_codes = context.active_names.get(kind, {}).get(name_token, ())
    if name_token and existing_codes:
        conflicts.append(
            "Наименование совпадает с действующей записью и не может быть "
            "однозначно создано как новая запись "
            f"(коды: {', '.join(existing_codes)})."
        )
    return conflicts


def publication_rows_and_effects(
    *,
    batch: ImportBatch,
    accepted_rows: tuple[ImportRow, ...],
) -> tuple[tuple[ImportRow, ...], tuple[dict[str, object], ...]]:
    context = build_registry_context(batch)
    rows = list(accepted_rows)
    by_key: dict[tuple[str, str], list[ImportRow]] = defaultdict(list)
    by_name: dict[tuple[str, str], list[ImportRow]] = defaultdict(list)

    for row in rows:
        values = _row_values(row)
        issues = validate_structure_values(values)
        conflicts = _active_conflicts(values=values, context=context)
        kind = values.get("structure_kind", "")
        code_token = _token(values.get("code", ""))
        name_token = _token(values.get("name", ""))
        if issues or conflicts:
            detail = "; ".join(issues + conflicts)
            raise ValidationError(
                f"Строка {row.row_number} больше не готова к публикации: {detail}"
            )
        by_key[(kind, code_token)].append(row)
        by_name[(kind, name_token)].append(row)

    for matching_rows in by_key.values():
        if len(matching_rows) > 1:
            numbers = ", ".join(str(item.row_number) for item in matching_rows)
            raise ValidationError(
                "В публикации повторяется пара «вид структуры + код»: "
                f"строки {numbers}."
            )
    for matching_rows in by_name.values():
        codes = {_token(_row_values(row).get("code", "")) for row in matching_rows}
        if len(codes) > 1:
            numbers = ", ".join(str(item.row_number) for item in matching_rows)
            raise ValidationError(
                "В публикации неоднозначно повторяется наименование: "
                f"строки {numbers}."
            )

    division_rows = {
        _token(_row_values(row).get("code", "")): row
        for row in rows
        if _row_values(row).get("structure_kind") == DIVISION
    }
    parent_by_code: dict[str, str] = {}
    for code_token, row in division_rows.items():
        parent_token = _token(_row_values(row).get("parent_code", ""))
        if not parent_token:
            continue
        if parent_token in division_rows:
            parent_by_code[code_token] = parent_token
        elif parent_token not in context.division_codes:
            raise ValidationError(
                f"Строка {row.row_number}: родительское подразделение отсутствует "
                "среди принятых строк и в действующем справочнике."
            )

    for row in rows:
        values = _row_values(row)
        if values.get("structure_kind") != WORKPLACE:
            continue
        division_token = _token(values.get("division_code", ""))
        if not division_token:
            continue
        if division_token not in division_rows and division_token not in context.division_codes:
            raise ValidationError(
                f"Строка {row.row_number}: подразделение рабочего места отсутствует "
                "среди принятых строк и в действующем справочнике."
            )

    cycle_codes = _cycle_codes(parent_by_code)
    if cycle_codes:
        raise ValidationError(
            "Публикация содержит цикл иерархии подразделений: "
            + ", ".join(sorted(cycle_codes))
            + "."
        )

    children: dict[str, list[str]] = defaultdict(list)
    indegree = {code: 0 for code in division_rows}
    for child, parent in parent_by_code.items():
        children[parent].append(child)
        indegree[child] += 1
    ready = sorted(
        (code for code, value in indegree.items() if value == 0),
        key=lambda code: division_rows[code].row_number,
    )
    ordered_divisions: list[ImportRow] = []
    while ready:
        code = ready.pop(0)
        ordered_divisions.append(division_rows[code])
        for child in sorted(
            children.get(code, []),
            key=lambda item: division_rows[item].row_number,
        ):
            indegree[child] -= 1
            if indegree[child] == 0:
                ready.append(child)
                ready.sort(key=lambda item: division_rows[item].row_number)

    workplaces = sorted(
        (
            row
            for row in rows
            if _row_values(row).get("structure_kind") == WORKPLACE
        ),
        key=lambda row: row.row_number,
    )
    energy_sites = sorted(
        (
            row
            for row in rows
            if _row_values(row).get("structure_kind") == ENERGY_SITE
        ),
        key=lambda row: row.row_number,
    )
    ordered = tuple(ordered_divisions + workplaces + energy_sites)
    effects = tuple(publication_effect(row) for row in ordered)
    return ordered, effects


def publication_effect(row: ImportRow) -> dict[str, object]:
    values = _row_values(row)
    kind = values["structure_kind"]
    target_model = {
        DIVISION: "organizations.Division",
        WORKPLACE: "organizations.Workplace",
        ENERGY_SITE: "equipment.EnergySite",
    }[kind]
    return {
        "row_number": row.row_number,
        "action": "create",
        "target_model": target_model,
        "label": f"{values['code']} · {values['name']}",
    }


def publish_row(
    *,
    batch: ImportBatch,
    values: dict[str, str],
) -> tuple[str, str, dict[str, object]]:
    kind = values["structure_kind"]
    is_active = _yes(values.get("is_active", ""), default=True)

    if kind == DIVISION:
        parent = None
        parent_code = values.get("parent_code", "")
        if parent_code:
            parent = Division.objects.get(
                organization=batch.organization,
                code__iexact=parent_code,
            )
        item = Division(
            organization=batch.organization,
            parent=parent,
            code=values["code"],
            name=values["name"],
            is_active=is_active,
        )
        item.full_clean()
        item.save()
        return (
            "organizations.Division",
            str(item.pk),
            {
                "division_id": item.pk,
                "code": item.code,
                "parent_id": item.parent_id,
            },
        )

    if kind == WORKPLACE:
        division = None
        division_code = values.get("division_code", "")
        if division_code:
            division = Division.objects.get(
                organization=batch.organization,
                code__iexact=division_code,
            )
        item = Workplace(
            organization=batch.organization,
            division=division,
            code=values["code"],
            name=values["name"],
            is_active=is_active,
        )
        item.full_clean()
        item.save()
        return (
            "organizations.Workplace",
            str(item.pk),
            {
                "workplace_id": item.pk,
                "code": item.code,
                "division_id": item.division_id,
            },
        )

    item = EnergySite(
        organization=batch.organization,
        code=values["code"],
        name=values["name"],
        short_name=values.get("short_name", ""),
        site_type=values["site_type"],
        is_external=_yes(values.get("is_external", ""), default=False),
        is_active=is_active,
    )
    item.full_clean()
    item.save()
    return (
        "equipment.EnergySite",
        str(item.pk),
        {
            "energy_site_id": item.pk,
            "public_id": str(item.public_id),
            "code": item.code,
        },
    )
