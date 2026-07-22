from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def require(name: str, condition: bool) -> None:
    if not condition:
        raise SystemExit(f"{name}=FAILED")
    print(f"{name}=PASSED")


def main() -> None:
    equipment_models = read("src/apps/equipment/models.py")
    equipment_services = read("src/apps/equipment/services.py")
    equipment_views = read("src/apps/equipment/views.py")
    dispatching_models = read("src/apps/dispatching/models.py")
    dispatching_services = read("src/apps/dispatching/services.py")
    import_models = read("src/apps/imports/models.py")
    importer = read("src/apps/imports/power_system.py")
    import_views = read("src/apps/imports/views.py")
    unicode_search = read("src/apps/imports/unicode_search.py")
    unicode_search_tests = read(
        "src/apps/imports/tests/test_power_system_unicode_search.py"
    )
    review_js = read("src/static/imports/power_system_review.js")
    import_urls = read("src/apps/imports/urls.py")
    detail_template = read("src/templates/imports/power_system_detail.html")
    list_template = read("src/templates/imports/list.html")
    power_system_list_template = read("src/templates/imports/power_system_list.html")
    publication_template = read("src/templates/imports/power_system_publication.html")
    upload_template = read("src/templates/imports/power_system_upload.html")
    equipment_registry_template = read("src/templates/equipment/registry.html")
    equipment_template = read("src/templates/equipment/detail.html")
    tests = read("src/apps/imports/tests/test_power_system_asset_importer.py")
    adr = read("docs/adr/ADR-011-5-power-system-asset-importer.md")

    require(
        "POWER_SYSTEM_SOURCE_REVISION",
        "class PowerSystemSourceRevision(models.Model):" in import_models
        and "file_sha256 = models.CharField" in import_models
        and "source_approval_status" in import_models
        and "diff_counts = models.JSONField" in import_models,
    )
    require(
        "SOURCE_OCCURRENCE_SEPARATION",
        "class PowerSystemAssetOccurrence(models.Model):" in import_models
        and "occurrence_id = models.CharField" in import_models
        and "logical_key = models.CharField" in import_models
        and "published_asset = models.ForeignKey" in import_models,
    )
    require(
        "ROW_LEVEL_QUARANTINE",
        'READY = "READY"' in import_models
        and 'REVIEW_REQUIRED = "REVIEW_REQUIRED"' in import_models
        and 'BLOCKED = "BLOCKED"' in import_models
        and 'EXCLUDED = "EXCLUDED"' in import_models
        and 'PUBLISHED = "PUBLISHED"' in import_models,
    )
    require(
        "STRICT_NORMALIZED_PACKAGE",
        "REQUIRED_CSV_FILES" in importer
        and "_safe_zip_entries" in importer
        and "MAX_POWER_SYSTEM_PACKAGE_SIZE" in importer
        and "headers != expected" in importer,
    )
    require(
        "IDEMPOTENT_SHA_AND_DIFF",
        "file_sha256=package_sha" in importer
        and "return existing, False" in importer
        and "previous_fingerprints" in importer
        and "missing_from_previous" in importer,
    )
    require(
        "DEPENDENCY_AWARE_HIERARCHY",
        "parent_external_key" in import_models
        and "pending_groups" in importer
        and "deferred_groups" in importer
        and "Не удалось разрешить иерархию" in importer,
    )
    require(
        "REAL_PACKAGE_HIERARCHY_REPAIR",
        "def _row_voltage_label(" in importer
        and 'if type_code == "unit_substation":' in importer
        and 'if type_code == "control_building":' in importer
        and 'type_code in {"overhead_line", "cable_line"}' in importer
        and 'comparison_token("ВЭУ")' in importer
        and "def reanalyze_power_system_revision(" in importer
        and "def reanalyze_staged_power_system_revisions(" in importer,
    )
    require(
        "SCOPED_EQUIPMENT_ALIASES",
        "scope_site = models.ForeignKey" in equipment_models
        and "scope_parent = models.ForeignKey" in equipment_models
        and "uniq_site_equipment_alias_start" in equipment_models
        and "uniq_parent_equipment_alias_start" in equipment_models
        and "scope_parent=parent" in equipment_services,
    )
    require(
        "MANAGEMENT_AND_CONDUCT_SEPARATED",
        "class PowerSystemAuthorityOccurrence(models.Model):" in import_models
        and 'OPERATIONAL_MANAGEMENT = "OPERATIONAL_MANAGEMENT"' in import_models
        and 'OPERATIONAL_CONDUCT = "OPERATIONAL_CONDUCT"' in import_models
        and "class ConductMode(models.TextChoices):" in dispatching_models
        and 'UNKNOWN = "UNKNOWN"' in dispatching_models
        and '"conduct_mode": locked.conduct_mode' in dispatching_services,
    )
    require(
        "CONTROLLED_PUBLICATION",
        "def build_power_system_publication_preview(" in importer
        and "def publish_power_system_revision(" in importer
        and "user.check_password(password)" in importer
        and "expected_digest != preview.digest" in importer
        and "transaction.atomic" in importer,
    )
    require(
        "RUSSIAN_USER_INTERFACE",
        'name="power_system_upload"' in import_urls
        and "Загрузить контролируемый пакет" in upload_template
        and "Конфликты и возможные дубли" in detail_template
        and "Происхождение из источника" in equipment_template
        and "Редакции импорта оборудования" in list_template
        and "Редакции импорта оборудования" in power_system_list_template
        and "Публикуются только строки со статусом «Готова»" in publication_template
        and "Редакции импорта оборудования" in equipment_registry_template
        and "SOURCE OCCURRENCES" not in detail_template
        and ">STAGING<" not in upload_template,
    )
    require(
        "ATTENTION_FIRST_REVIEW_UI",
        'status_filter = "ATTENTION"' in import_views
        and "needs_manual_decision" in import_views
        and "Показаны только строки, требующие решения" in detail_template
        and "Ручное действие не требуется" in detail_template
        and "POWER_SYSTEM_TEXT_REPLACEMENTS" in import_views
        and "Повторное представление КЛ 35 кВ" in import_views,
    )
    require(
        "SEARCH_AND_PROVENANCE",
        "voltage_level" in equipment_services
        and "source_provenance" in equipment_views
        and "Исходные строки" in equipment_template,
    )
    require(
        "SYNTHETIC_IMPORT_TESTS",
        "test_stage_is_idempotent" in tests
        and "test_hierarchy_is_recovered_from_semantic_context" in tests
        and "test_reanalysis_repairs_existing_staging" in tests
        and "test_manual_decision_is_audited" in tests
        and "test_publication_rebuilds_hierarchy" in tests
        and "test_detail_defaults_to_attention" in tests
        and "test_issue_descriptions_are_localized" in tests
        and "test_views_expose_staging_without_publishing" in tests
        and "test_repair6_normalizes_shot" in tests
        and "test_duplicate_group_decision_merges" in tests
        and "test_grouped_review_view_uses_detected_candidates" in tests,
    )
    require(
        "NO_REAL_SOURCE_DATA_IN_PATCH",
        "Патч не содержит реальных объектов" in adr
        and "коммитятся в Git" in adr
        and "подходящий профиль" in adr,
    )
    require(
        "HIGH_RISK_VALIDATION_DECLARED",
        "высокому риску" in adr
        and "чистой и рабочей БД" in adr
        and "полный test discovery" in adr,
    )
    require(
        "POWER_SYSTEM_VIEW_HANDLERS",
        "def power_system_upload(" in import_views
        and "def power_system_occurrence_decide(" in import_views
        and "def power_system_publication(" in import_views,
    )
    require(
        "CONTROLLED_SHOT_NORMALIZATION",
        'CONTROLLED_DC_EQUIPMENT_TYPE_CODE = "dc_distribution_board"' in importer
        and "SHOT_EXACT_UNDER_KTP" in importer
        and "Щит или шкаф оперативного постоянного тока" in importer,
    )
    require(
        "EXPLICIT_CONTROL_BUILDING_PARENT",
        'if type_code == "control_building":' in importer
        and "explicit_parent" in importer,
    )
    require(
        "ROOT_AND_ORPHAN_SEPARATION",
        'counters["root_without_parent"]' in importer
        and 'counters["orphan_parent"]' in importer
        and "Потерянные родители" in publication_template,
    )
    require(
        "GROUPED_CONFLICT_REVIEW",
        "def decide_power_system_duplicate_group(" in importer
        and "def power_system_duplicate_group_decide(" in import_views
        and "СГРУППИРОВАННАЯ ПРОВЕРКА" in detail_template,
    )
    require(
        "COMMON_DC_CONTROL_EQUIPMENT_FAMILY",
        'CONTROLLED_DC_EQUIPMENT_TYPE_CODE = "dc_distribution_board"' in importer
        and "dc_equipment_designation" in importer
        and "Оборудование оперативного постоянного тока" in detail_template
        and "Обозначение ШОТ" in detail_template
        and "Обозначение ЩПТ" in detail_template
        and "dc_control_equipment_rows" in publication_template,
    )
    require(
        "READABLE_CANONICAL_SNAPSHOT",
        "canonical_json_pretty" in importer
        and "ps-canonical-snapshot" in publication_template
        and "Отдельные строки вне групп" in detail_template,
    )
    require(
        "UNICODE_CASEFOLD_SEARCH",
        "unicodedata.normalize" in unicode_search
        and ".casefold()" in unicode_search
        and "filter_power_system_occurrences" in unicode_search
        and "filter_power_system_occurrences" in import_views
        and "test_cyrillic_search_is_case_insensitive" in unicode_search_tests,
    )
    require(
        "LAZY_PUBLICATION_SNAPSHOT",
        "request.GET.show_snapshot" in publication_template
        and "ps-canonical-snapshot-placeholder" in publication_template
        and "preview.canonical_json_pretty" in publication_template,
    )
    require(
        "PUBLICATION_PREVIEW_PROGRESS",
        "data-power-system-preview-trigger" in detail_template
        and "data-power-system-preview-progress" in detail_template
        and "aria-busy" in review_js
        and "Формируется предварительная проверка" in review_js,
    )
    print("PATCH_011_5_POWER_SYSTEM_ASSET_IMPORTER_GATE_PASSED")


if __name__ == "__main__":
    main()
