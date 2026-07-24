from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    path = ROOT / relative
    if not path.is_file():
        raise AssertionError(f"Отсутствует обязательный файл: {relative}")
    return path.read_text(encoding="utf-8")


def require(text: str, *tokens: str) -> None:
    missing = [token for token in tokens if token not in text]
    if missing:
        raise AssertionError("Не найдены обязательные маркеры: " + ", ".join(missing))


def forbid(text: str, *tokens: str) -> None:
    present = [token for token in tokens if token in text]
    if present:
        raise AssertionError("Обнаружены запрещённые маркеры: " + ", ".join(present))


def main() -> None:
    settings = read("src/eod_config/settings.py")
    root_urls = read("src/eod_config/urls.py")
    app_urls = read("src/apps/operational_documents/urls.py")
    base = read("src/templates/base.html")
    home = read("src/templates/system/home.html")
    system_smoke = read("src/apps/system/tests/test_system.py")
    require(settings, "apps.operational_documents.apps.OperationalDocumentsConfig")
    require(root_urls, 'include("apps.operational_documents.urls")')
    require(app_urls, 'app_name = "operational_documents"', 'name="registry"')
    require(base, "operational_documents:registry", "Оперативные документы")
    require(
        home,
        "Утверждённые формы журналов",
        "Ядро структурированных журналов готово к установке утверждённых форм",
        "Ядро готово",
    )
    require(
        system_smoke,
        "Утверждённые формы журналов",
        "Ядро структурированных журналов готово к установке утверждённых форм",
    )
    print("OPDOC_APP_WIRING=PASSED")

    models = read("src/apps/operational_documents/models.py")
    services = read("src/apps/operational_documents/services.py")
    migration = read("src/apps/operational_documents/migrations/0001_initial.py")
    require(
        models,
        "class OperationalDocumentType(models.Model)",
        "class OperationalDocumentTypeRevision(models.Model)",
        "canonical_snapshot = models.JSONField",
        "class OperationalDocumentRecord(models.Model)",
        "class OperationalDocumentRecordRevision(models.Model)",
        "class OperationalDocumentAuditEvent(models.Model)",
    )
    require(
        services,
        "def publish_type_revision",
        "def create_record",
        "def update_record",
        "def transition_record",
        "def normalize_search_text",
        'unicodedata.normalize("NFKC", str(value)).casefold()',
    )
    require(migration, 'name="OperationalDocumentTypeRevision"')
    print("OPDOC_CORE_INVARIANTS=PASSED")

    catalog = read("src/apps/operational_documents/journal_forms.py")
    require(
        catalog,
        'SOURCE_DOCUMENT_TITLE = "И-00-007-ОР-2025 версия 2"',
        'code="journal-orders"',
        'source_section="7"',
        'source_appendix="4"',
        'code="journal-outage-requests"',
        'source_section="8"',
        'source_appendix="5"',
        'code="journal-equipment-commissioning"',
        'source_section="9"',
        'source_appendix="6"',
        'code="journal-rza-telemechanics"',
        'source_section="10"',
        'source_appendix="7"',
        'code="journal-equipment-defects"',
        'source_section="11"',
        'source_appendix="8"',
    )
    forbid(catalog, "PRIORITY", "TEMPERATURE", "CONFIRMED")
    print("APPROVED_JOURNAL_SOURCE_CATALOG=PASSED")

    forms = read("src/apps/operational_documents/forms.py")
    require(
        forms,
        "APPROVED_JOURNAL_FORM_CODES",
        'code__in=APPROVED_JOURNAL_FORM_CODES',
        'cleaned["_empty_definition"] = not meaningful',
        'form.cleaned_data.get("_empty_definition")',
        'extra=1',
        'class": "opdoc-multi-select"',
        "def main_fields",
        "def subject_fields",
        "def participant_fields",
        "def relation_fields",
    )
    forbid(forms, "initial=True,\n    )\n    choice_options")
    print("OPDOC_FORMSET_AND_EDITOR_GROUPS=PASSED")

    views = read("src/apps/operational_documents/views.py")
    require(
        views,
        "APPROVED_JOURNAL_FORM_CODES",
        "APPROVED_JOURNAL_FORMS",
        "def _catalog_rows",
        "def _require_source_bound_record",
        "Ручное создание форм отключено",
        "Запись нельзя создать по технической тестовой схеме",
        "source_form = approved_journal_form",
        "search_text__contains=normalize_search_text(q)",
        "workplace__code",
    )
    forbid(
        views,
        "OperationalDocumentTypeForm",
        "OperationalFieldDefinitionFormSet",
        "create_and_publish_type",
        "field_definitions_from_formset",
    )
    require(services, 'return bool(getattr(user, "is_superuser", False))')
    forbid(services, 'user_has_role(user, "shift_supervisor")')
    print("SOURCE_BOUND_ACTION_GUARD=PASSED")

    registry = read("src/templates/operational_documents/registry.html")
    type_registry = read("src/templates/operational_documents/type_registry.html")
    type_detail = read("src/templates/operational_documents/type_detail.html")
    choose_type = read("src/templates/operational_documents/choose_type.html")
    record_form = read("src/templates/operational_documents/record_form.html")
    record_detail = read("src/templates/operational_documents/record_detail.html")
    templates = "\n".join(
        (registry, type_registry, type_detail, choose_type, record_form, record_detail)
    )
    require(
        registry,
        "Формы по утверждённым источникам",
        "Оперативный персонал не конструирует формы журналов",
        "Техническая запись",
        "Нет установленных форм",
    )
    require(
        type_registry,
        "Источник → форма → запись",
        "Ручное создание произвольных журналов отключено",
        "Раздел {{ row.form.source_section }}",
        "Приложение № {{ row.form.source_appendix }}",
        "Состав граф по памяти не создаётся",
    )
    forbid(type_registry, "Создать тип")
    require(
        type_detail,
        "Утверждённая форма",
        "Источник формы не привязан",
        "Технические сведения",
        "type_label",
    )
    require(
        choose_type,
        "только формы, установленные по утверждённым источникам",
        "Утверждённые формы ещё не установлены",
    )
    require(
        record_form,
        "Данные установленной формы",
        "Оборудование и связанные документы",
        "Поиск по списку",
        "удерживать Ctrl не требуется",
        'select.addEventListener("mousedown"',
    )
    require(
        record_detail,
        "Данные формы",
        "Техническая запись общего ядра",
        "неизменяемый журнал аудита",
        "data-required-message",
        "Без комментария действие не будет выполнено",
    )
    forbid(templates, "Append-only аудит", ">LONG_TEXT<", ">BOOLEAN<")
    print("OPDOC_SOURCE_BOUND_RUSSIAN_UI=PASSED")

    css = read("src/static/system/app.css")
    reference_contract = read("src/apps/operational_log/tests/test_reference_navigation.py")
    require(base, "system/app.css' %}?v=011702")
    require(reference_contract, 'SYSTEM_CSS_REVISION = "011702"')
    require(
        css,
        "Patch 011.7 Repair 2 — source-bound journal UX",
        ".approved-form-catalog",
        ".opdoc-multi-picker",
        ".sticky-form-actions",
        ".hash-value",
    )
    print("OPDOC_ASSET_AND_LAYOUT_CONTRACT=PASSED")

    tests = read("src/apps/operational_documents/tests/test_operational_document_core.py")
    tree = ast.parse(tests)
    test_count = sum(
        1
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test_")
    )
    if test_count < 11:
        raise AssertionError(f"Ожидалось не менее 11 профильных тестов, найдено {test_count}")
    require(
        tests,
        "test_manual_type_builder_is_disabled_and_catalog_is_source_bound",
        "test_browser_default_field_type_does_not_activate_empty_form",
        '"fields-1-field_type": "TEXT"',
        'self.assertEqual([item["code"] for item in definitions], ["CONTENT"])',
        'code="journal-equipment-defects"',
        '"q": "НАГРЕВ"',
    )
    print(f"OPDOC_REPAIR2_TEST_CONTRACT=PASSED COUNT={test_count}")

    adr = read("docs/adr/ADR-011-7-operational-documentation-core.md")
    current_state = read("docs/project/CURRENT_STATE.md")
    decision_log = read("docs/project/DECISION_LOG.md")
    patch_history = read("docs/project/PATCH_HISTORY.md")
    domain_invariants = read("docs/project/DOMAIN_INVARIANTS.md")
    handoff = read("docs/project/CURRENT_HANDOFF.md")
    require(
        adr,
        "Источник формы обязателен",
        "Пользовательский интерфейс не предоставляет конструктор",
        "source-bound",
    )
    require(
        current_state,
        "source-bound каталог рабочих форм",
        "PLAN-001 — ревизия фактической реализации",
        "один журнал полностью",
    )
    require(decision_log, "рабочие формы только из утверждённых источников")
    require(patch_history, "Patch 011.7 Repair 1 Revision 10", "Patch 011.7 Repair 2")
    require(
        domain_invariants,
        "оператор не проектирует состав граф",
        "source-bound",
        "точная форма не восстанавливается по памяти",
    )
    require(
        handoff,
        "GitHub-first/VPS-first",
        "PLAN-001 — доказательная ревизия плана и реализации",
        "журналы доводятся по одному",
    )
    for relative in (
        "docs/adr/ADR-011-7-operational-documentation-core.md",
        "docs/project/CURRENT_STATE.md",
        "docs/project/DECISION_LOG.md",
        "docs/project/PATCH_HISTORY.md",
        "docs/project/DOMAIN_INVARIANTS.md",
        "docs/project/CURRENT_HANDOFF.md",
    ):
        bad_lines = [
            number
            for number, line in enumerate(read(relative).splitlines(), start=1)
            if line.endswith((" ", "\t"))
        ]
        if bad_lines:
            raise AssertionError(f"Trailing whitespace в {relative}: строки {bad_lines}")
    print("PROJECT_STATE_SOURCE_BOUND_DECISION=PASSED")

    print("PATCH_011_7_REPAIR2_SOURCE_BOUND_JOURNAL_UX_GATE_PASSED")


if __name__ == "__main__":
    main()
