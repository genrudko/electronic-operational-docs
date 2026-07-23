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


def main() -> None:
    settings = read("src/eod_config/settings.py")
    root_urls = read("src/eod_config/urls.py")
    app_urls = read("src/apps/operational_documents/urls.py")
    base = read("src/templates/base.html")
    home = read("src/templates/system/home.html")
    system_smoke = read("src/apps/system/tests/test_system.py")
    require(settings, "apps.operational_documents.apps.OperationalDocumentsConfig")
    require(root_urls, 'include("apps.operational_documents.urls")')
    require(app_urls, 'app_name = "operational_documents"', 'name="registry"', 'name="record_transition"')
    require(base, "operational_documents:registry", "Оперативные документы")
    require(
        home,
        "Настраиваемые журналы, статусы, связи и история редакций",
        "Единое ядро оперативной документации готово к наполнению",
    )
    require(
        system_smoke,
        "Единое ядро оперативной документации готово к наполнению",
        "Оперативные документы",
    )
    if "Базовые реестры готовы к демонстрации" in system_smoke:
        raise AssertionError("Smoke-тест главной страницы ожидает устаревший текст")
    print("SYSTEM_HOME_SMOKE_COPY_CONTRACT=PASSED")
    print("OPDOC_APP_WIRING=PASSED")

    models = read("src/apps/operational_documents/models.py")
    services = read("src/apps/operational_documents/services.py")
    migration = read("src/apps/operational_documents/migrations/0001_initial.py")
    require(
        models,
        "class OperationalDocumentType(models.Model)",
        "class OperationalDocumentTypeRevision(models.Model)",
        "class SchemaPublicationStatus(models.TextChoices)",
        "Опубликованная редакция типа неизменяема",
        "canonical_snapshot = models.JSONField",
        'sha256 = models.CharField("SHA-256"',
    )
    require(
        services,
        "def publish_type_revision",
        '"schema": "eod.operational-document-type.v1"',
        "snapshot = json.loads(canonical_json(snapshot))",
        "sha256_text(canonical_json(snapshot))",
    )
    require(migration, 'name="OperationalDocumentTypeRevision"', 'name="uniq_opdoc_type_revision_number"')
    print("OPDOC_PUBLISHED_SCHEMA_IMMUTABILITY=PASSED")

    require(
        models,
        "class FieldType(models.TextChoices)",
        "field_definitions = models.JSONField",
        "status_definitions = models.JSONField",
        "transition_definitions = models.JSONField",
        "participant_role_definitions = models.JSONField",
    )
    require(
        services,
        "def normalize_field_definitions",
        "def normalize_status_definitions",
        "def normalize_transition_definitions",
        "DEFAULT_STATUS_DEFINITIONS",
        "DEFAULT_TRANSITION_DEFINITIONS",
        "DEFAULT_PARTICIPANT_ROLE_DEFINITIONS",
    )
    forms = read("src/apps/operational_documents/forms.py")
    require(
        forms,
        'searchable = forms.BooleanField(label="Учитывать в поиске", required=False)',
        "OperationalFieldDefinitionFormSet = formset_factory",
    )
    if 'searchable = forms.BooleanField(label="Учитывать в поиске", required=False, initial=True)' in forms:
        raise AssertionError("Пустые дополнительные строки formset ошибочно считаются изменёнными")
    print("OPDOC_CONFIGURABLE_FIELDS_STATUSES_TRANSITIONS=PASSED")

    require(
        models,
        "class OperationalDocumentNumberSequence(models.Model)",
        "class OperationalDocumentRecord(models.Model)",
        "registration_number = models.CharField",
        "workplace_name_snapshot",
        "created_by_full_name_snapshot",
        "Идентификационные реквизиты записи неизменяемы",
    )
    require(
        services,
        "def _allocate_number",
        "select_for_update().get_or_create",
        "def _registration_number",
        'f"{revision.number_prefix}-{year}-{value:0{revision.number_width}d}"',
        '"schema": "eod.operational-document-record.v1"',
        '"code": record.workplace.code if record.workplace_id else ""',
    )
    print("OPDOC_RECORD_NUMBERING_AND_SNAPSHOTS=PASSED")

    require(
        models,
        "class OperationalDocumentParticipant(models.Model)",
        "class OperationalDocumentEquipmentLink(models.Model)",
        "class OperationalDocumentExternalDocumentLink(models.Model)",
        "class OperationalDocumentRelation(models.Model)",
        "Связываемые записи относятся к разным организациям",
    )
    require(
        services,
        "def _validate_participants",
        "def _validate_related_collections",
        "def _sync_participants",
        "def _sync_equipment",
        "def _sync_documents",
        "def _sync_relations",
    )
    print("OPDOC_PARTICIPANTS_EQUIPMENT_DOCUMENT_RELATIONS=PASSED")

    require(
        models,
        "class OperationalDocumentRecordRevision(models.Model)",
        "class OperationalDocumentAuditEvent(models.Model)",
        "Редакция оперативной записи неизменяема",
        "Событие аудита неизменяемо",
        "Массовое изменение защищённых записей",
    )
    require(
        services,
        "def _append_record_revision",
        'event_type="RECORD_CREATED"',
        'event_type="RECORD_UPDATED"',
        'event_type="STATUS_CHANGED"',
    )
    print("OPDOC_APPEND_ONLY_REVISIONS_AND_AUDIT=PASSED")

    views = read("src/apps/operational_documents/views.py")
    registry = read("src/templates/operational_documents/registry.html")
    require(
        views,
        "def registry",
        "search_text__contains=normalize_search_text(q)",
        "document_type__public_id",
        "status_code=status_code",
        "workplace__code",
        "equipment_links__equipment__public_id",
        "event_at__date__gte",
        "event_at__date__lte",
    )
    require(
        services,
        "import unicodedata",
        "def normalize_search_text",
        'unicodedata.normalize("NFKC", str(value)).casefold()',
        "return normalize_search_text(rendered)",
    )
    if "Q(search_text__icontains=q)" in views:
        raise AssertionError("SQLite icontains не обеспечивает Unicode casefold для кириллицы")
    if "workplace__public_id" in views:
        raise AssertionError("Workplace не имеет public_id; фильтр должен использовать code")
    require(registry, "Всего записей", "Оборудование", "С даты", "По дату", "Предметные данные")
    print("OPDOC_COMMON_REGISTRY_SEARCH_FILTERS=PASSED")

    base_template = read("src/templates/base.html")
    reference_contract = read(
        "src/apps/operational_log/tests/test_reference_navigation.py"
    )
    require(base_template, "system/app.css' %}?v=011700")
    require(reference_contract, 'SYSTEM_CSS_REVISION = "011700"')
    if "011610" in reference_contract:
        raise AssertionError("Старый CSS cache revision сохранён в regression-тесте")
    print("SYSTEM_CSS_CACHE_REVISION_CONTRACT=PASSED")

    templates = "\n".join(
        read(f"src/templates/operational_documents/{name}")
        for name in (
            "registry.html",
            "type_registry.html",
            "type_form.html",
            "type_detail.html",
            "choose_type.html",
            "record_form.html",
            "record_detail.html",
        )
    )
    require(
        templates,
        "Единое структурированное ядро",
        "Публикуемая конфигурация",
        "Новая запись",
        "История редакций",
        "Доступные переходы состояния",
    )
    print("OPDOC_RUSSIAN_UI=PASSED")

    tests = read("src/apps/operational_documents/tests/test_operational_document_core.py")
    tree = ast.parse(tests)
    test_count = sum(
        1
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_")
    )
    if test_count < 10:
        raise AssertionError(f"Ожидалось не менее 10 профильных тестов, найдено {test_count}")
    require(
        tests,
        "test_published_type_revision_has_canonical_hash_and_is_immutable",
        "test_server_numbering_increments_per_type_and_year",
        "test_update_creates_new_immutable_revision_and_preserves_first_snapshot",
        "test_cross_organization_equipment_and_participant_are_rejected",
        "test_common_registry_search_and_filters_show_only_own_organization",
        '"q": "НАГРЕВ"',
        'self.assertIn("нагрев", record.search_text)',
        'self.assertNotIn("Нагрев", record.search_text)',
    )
    if '"q": "теплов"' in tests or '"q": "нагрев"' in tests:
        raise AssertionError("Поисковый тест не проверяет Unicode-регистронезависимый контракт")
    print(f"OPDOC_SYNTHETIC_TESTS=PASSED COUNT={test_count}")

    adr = read("docs/adr/ADR-011-7-operational-documentation-core.md")
    require(adr, "единое ядро", "Границы Patch 011.7", "Patch 011.8")
    print("OPDOC_ARCHITECTURE_DECISION=PASSED")

    workflow = read("docs/project_state/WORKFLOW_CONTRACT.md")
    current_state = read("docs/project_state/CURRENT_STATE.md")
    patch_history = read("docs/project_state/PATCH_HISTORY.md")
    handoff = read("docs/project_state/CHAT_HANDOFF.md")
    start_text = read("docs/project_state/START_NEW_CHAT.txt")
    context_manager = read("scripts/eod_context_manager.py")
    require(
        workflow,
        "pre-patch snapshot",
        "EOD_CURRENT_CONTEXT.zip",
        "визуально принятого Patch/Repair",
        "ровно один завершающий перевод строки",
    )
    require(
        current_state,
        "b73510a5b64b4f7faf9d80996c8ad3dba4822d6f",
        "Patch 011.7 Repair 1",
        "исправленная ревизия 10",
        "Конкретный SHA ZIP не",
    )
    require(
        patch_history,
        "Patch 011.7 — первая попытка",
        "отказ на Ruff",
        "rollback: clean",
        "Patch 011.7 Repair 1 Revision 1",
        "двумя LF",
        "Patch 011.7 Repair 1 Revision 2",
        "I001 и B904",
        "Patch 011.7 Repair 1 Revision 3",
        "повторно выявил I001",
        "Patch 011.7 Repair 1 Revision 4",
        "Workplace",
        "Patch 011.7 Repair 1 Revision 5",
        "9 прошло, 1 failure",
        "запрос `теплов` отсутствовал",
        "Patch 011.7 Repair 1 Revision 6",
        "SQLite `icontains`",
        "Patch 011.7 Repair 1 Revision 7",
        "SYSTEM_CSS_REVISION",
        "011610",
        "Patch 011.7 Repair 1 Revision 8",
        "Базовые реестры готовы к демонстрации",
        "495",
        "Patch 011.7 Repair 1 Revision 9",
        "495/495",
        "git diff --cached --check",
        "trailing whitespace",
    )
    require(handoff, "двухфазный", "START_NEW_CHAT.txt")
    require(start_text, "Восстанови основной интеграционный контекст", "Не создавай новый патч")
    require(
        context_manager,
        'stable_name = "EOD_CURRENT_CONTEXT.zip"',
        'stable_name = "EOD_PREPATCH_SNAPSHOT_CURRENT.zip"',
        '"START_NEW_CHAT.txt"',
        "from datetime import datetime",
        "raise SystemExit(1) from None",
        "# isort: skip_file",
    )
    if "import datetime as dt" in context_manager:
        raise AssertionError("В context manager сохранён aliased datetime import")
    print("PROJECT_CONTEXT_CONTINUITY=PASSED")

    text_contract_paths = (
        "docs/adr/ADR-011-7-operational-documentation-core.md",
        "docs/project_state/CHAT_HANDOFF.md",
        "docs/project_state/CURRENT_STATE.md",
        "docs/project_state/DECISION_LOG.md",
        "docs/project_state/OPEN_ITEMS.md",
        "docs/project_state/PATCH_HISTORY.md",
        "docs/project_state/START_NEW_CHAT.txt",
        "docs/project_state/WORKFLOW_CONTRACT.md",
    )
    for relative in text_contract_paths:
        bad_lines = [
            number
            for number, line in enumerate(read(relative).splitlines(), start=1)
            if line.endswith((" ", "\t"))
        ]
        if bad_lines:
            raise AssertionError(
                f"Trailing whitespace в {relative}: строки {bad_lines}"
            )
    print("PROJECT_STATE_TRAILING_WHITESPACE_CONTRACT=PASSED")

    require(
        models,
        'return f"{self.record.registration_number}: {self.dispatcher_name_snapshot}"',
        'return f"{self.record.registration_number}: {self.title_snapshot}"',
        'f"{self.source_record.registration_number} → "',
    )
    if "from typing import Any" in views:
        raise AssertionError("В views.py сохранён неиспользуемый импорт typing.Any")
    print("PATCH_011_7_REPAIR1_RUFF_CONTRACT=PASSED")
    print("PATCH_011_7_OPERATIONAL_DOCUMENTATION_CORE_GATE_PASSED")


if __name__ == "__main__":
    main()
