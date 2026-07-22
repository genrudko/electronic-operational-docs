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
    import_urls = read("src/apps/imports/urls.py")
    detail_template = read("src/templates/imports/power_system_detail.html")
    upload_template = read("src/templates/imports/power_system_upload.html")
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
        and "Строки источника" in detail_template
        and "Происхождение из источника" in equipment_template
        and "SOURCE OCCURRENCES" not in detail_template
        and ">STAGING<" not in upload_template,
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
        and "test_manual_decision_is_audited" in tests
        and "test_publication_rebuilds_hierarchy" in tests
        and "test_views_expose_staging_without_publishing" in tests,
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
    print("PATCH_011_5_POWER_SYSTEM_ASSET_IMPORTER_GATE_PASSED")


if __name__ == "__main__":
    main()
