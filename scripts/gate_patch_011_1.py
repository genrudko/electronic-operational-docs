from __future__ import annotations

import ast
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eod_config.settings")

import django  # noqa: E402

django.setup()

from apps.operational_log.form_contracts import OPERATIONAL_JOURNAL_FORM  # noqa: E402
from apps.operational_log.forms import JournalDisplayPreferenceForm  # noqa: E402
from apps.organizations.models import InterfacePreference  # noqa: E402


def require_text(path: str, markers: tuple[str, ...]) -> str:
    content = (ROOT / path).read_text(encoding="utf-8")
    missing = [marker for marker in markers if marker not in content]
    if missing:
        raise AssertionError(
            f"{path}: отсутствуют обязательные маркеры: {missing}"
        )
    return content


def require_immediate_preference_save_contract(path: str) -> None:
    source = (ROOT / path).read_text(encoding="utf-8")
    module = ast.parse(source, filename=path)

    update_display = next(
        (
            node
            for node in module.body
            if isinstance(node, ast.FunctionDef)
            and node.name == "update_display"
        ),
        None,
    )
    if update_display is None:
        raise AssertionError(f"{path}: функция update_display не найдена")

    def inspect_update_fields(expression: ast.AST) -> tuple[bool, set[str]]:
        has_values_tuple = False
        names: set[str] = set()

        for node in ast.walk(expression):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                names.add(node.value)
            if not isinstance(node, ast.Call):
                continue
            if not isinstance(node.func, ast.Name) or node.func.id != "tuple":
                continue
            if (
                len(node.args) == 1
                and isinstance(node.args[0], ast.Name)
                and node.args[0].id == "values"
            ):
                has_values_tuple = True

        return has_values_tuple, names

    candidates: list[tuple[bool, set[str]]] = []
    for node in ast.walk(update_display):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Attribute) or node.func.attr != "save":
            continue
        if not (
            isinstance(node.func.value, ast.Name)
            and node.func.value.id == "preferences"
        ):
            continue

        update_fields = next(
            (
                keyword.value
                for keyword in node.keywords
                if keyword.arg == "update_fields"
            ),
            None,
        )
        if update_fields is not None:
            candidates.append(inspect_update_fields(update_fields))

    if not candidates:
        raise AssertionError(
            f"{path}: preferences.save(update_fields=...) не найден"
        )

    if not any(
        has_values_tuple
        and "updated_at" in names
        and "journal_simplified_time_input" in names
        for has_values_tuple, names in candidates
    ):
        raise AssertionError(
            f"{path}: update_fields должен включать tuple(values), "
            "journal_simplified_time_input и updated_at"
        )


def main() -> None:
    typography_fields = (
        "journal_font_size",
        "journal_time_font_size",
        "journal_date_font_size",
        "journal_table_header_font_size",
        "journal_title_font_size",
    )
    expected_choices = tuple(
        value for value, _label in InterfacePreference.JournalFontSize.choices
    )
    assert expected_choices == (
        "SMALL",
        "NORMAL",
        "LARGE",
        "EXTRA_LARGE",
    )
    for field_name in typography_fields:
        field = InterfacePreference._meta.get_field(field_name)
        assert field.default == InterfacePreference.JournalFontSize.NORMAL
        assert tuple(value for value, _label in field.choices) == expected_choices
    print("JOURNAL_TYPOGRAPHY_MODEL=PASSED")

    form = JournalDisplayPreferenceForm()
    assert all(field_name in form.fields for field_name in typography_fields)
    print("JOURNAL_TYPOGRAPHY_FORM=PASSED")

    require_text(
        "src/templates/operational_log/shift_workspace.html",
        (
            "data-initial-journal-entry-size",
            "data-initial-journal-time-size",
            "data-initial-journal-date-size",
            "data-initial-journal-table-header-size",
            "data-initial-journal-title-size",
            "data-typography-panel",
            'data-typography-preset="normal"',
            'data-typography-target="entry"',
            'data-typography-target="time"',
            'data-typography-target="date"',
            'data-typography-target="tableHeader"',
            'data-typography-target="title"',
            "Печатная форма не меняется",
        ),
    )
    print("JOURNAL_TYPOGRAPHY_QUICK_PANEL=PASSED")

    javascript = require_text(
        "src/static/operational_log/draft_workspace.js",
        (
            "normalizeJournalFontSize",
            "typographyPreferences",
            "selectTypographyPreference",
            "selectTypographyPreset",
            "journal_table_header_font_size",
            "journal_title_font_size",
            "data-typography-target",
            "schedulePagination(20)",
        ),
    )
    update_controls = javascript.split(
        "function updateRecordControls()",
        1,
    )[1].split(
        "function setRecordSetting",
        1,
    )[0]
    assert "addEventListener" not in update_controls
    assert javascript.count("const systemThemeQuery") == 1
    print("JOURNAL_TYPOGRAPHY_LIVE_PREVIEW=PASSED")

    css = require_text(
        "src/static/system/app.css",
        (
            "Patch 011.1: типографика журнала",
            "--journal-entry-font-size",
            "--journal-time-font-size",
            "--journal-date-font-size",
            "--journal-table-header-font-size",
            ".draft-typography-preset-group",
            ".draft-typography-size-group",
            ".journal-entry-size-extra_large",
            ".journal-title-size-extra_large",
            "Печатная типографика фиксирована утверждённой формой",
            "font-size: 16pt !important",
            "font-size: 9pt !important",
        ),
    )
    assert 'input type="number"' not in css.split(
        "Patch 011.1: типографика журнала",
        1,
    )[-1]
    print("JOURNAL_TYPOGRAPHY_CSS=PASSED")

    require_text(
        "src/templates/operational_log/detail.html",
        (
            "display_form.journal_time_font_size",
            "display_form.journal_date_font_size",
            "display_form.journal_table_header_font_size",
            "display_form.journal_title_font_size",
            "journal-entry-size-",
            "journal-time-size-",
            "journal-date-size-",
            "journal-table-header-size-",
            "journal-title-size-",
        ),
    )
    print("REGISTERED_JOURNAL_TYPOGRAPHY=PASSED")

    widths = tuple(
        column.width_percent for column in OPERATIONAL_JOURNAL_FORM.columns
    )
    assert widths == (14, 66, 20)
    assert OPERATIONAL_JOURNAL_FORM.columns[0].title == "Дата и время записи"
    print("APPROVED_JOURNAL_FORM_UNCHANGED=PASSED")

    require_text(
        "src/apps/operational_log/views.py",
        (
            '"journal_font_size": (',
            '"journal_time_font_size": (',
            '"journal_date_font_size": (',
            '"journal_table_header_font_size": (',
            '"journal_title_font_size": (',
        ),
    )
    require_immediate_preference_save_contract(
        "src/apps/operational_log/views.py"
    )
    print("TYPOGRAPHY_PREFERENCES_IMMEDIATE_SAVE=PASSED")

    print("EDITOR_PANEL_FOUNDATION=PASSED")
    print("PATCH_011_1_JOURNAL_TYPOGRAPHY_GATE_PASSED")


if __name__ == "__main__":
    main()
