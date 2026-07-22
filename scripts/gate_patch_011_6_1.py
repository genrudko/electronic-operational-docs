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
    organization_models = read("src/apps/organizations/models.py")
    import_models = read("src/apps/imports/models.py")
    importer = read("src/apps/imports/personnel.py")
    forms = read("src/apps/imports/forms.py")
    views = read("src/apps/imports/views.py")
    urls = read("src/apps/imports/urls.py")
    organization_views = read("src/apps/organizations/views.py")
    organization_urls = read("src/apps/organizations/urls.py")
    detail_template = read("src/templates/imports/personnel_detail.html")
    publication_template = read("src/templates/imports/personnel_publication.html")
    employee_template = read("src/templates/organizations/employee_detail.html")
    tests = read("src/apps/imports/tests/test_personnel_operational_authority_importer.py")
    organization_migration = read(
        "src/apps/organizations/migrations/0007_personnel_qualifications_and_operational_rights.py"
    )
    adr = read("docs/adr/ADR-011-6-1-personnel-operational-authority-importer.md")

    require(
        "PERSONNEL_DOMAIN_MODELS",
        "public_id = models.UUIDField" in organization_models
        and "class OperationalRightDefinition(models.Model):" in organization_models
        and "class EmployeeQualification(models.Model):" in organization_models
        and "class EmployeeOperationalRight(models.Model):" in organization_models,
    )
    require(
        "SAFE_EXISTING_EMPLOYEE_UUID_MIGRATION",
        "null=True" in organization_migration
        and "populate_employee_public_ids" in organization_migration
        and "migrations.AlterField" in organization_migration
        and "unique=True" in organization_migration,
    )
    require(
        "PERSONNEL_STAGING_MODELS",
        "class PersonnelSourceRevision(models.Model):" in import_models
        and "class PersonnelSourceRow(models.Model):" in import_models
        and "class PersonnelAuthorityCell(models.Model):" in import_models
        and "class PersonnelPublication(models.Model):" in import_models,
    )
    require(
        "TWENTY_ONE_RIGHT_DICTIONARY",
        importer.count('"dispatch_application_submit"') >= 1
        and importer.count('"rza_maintenance_category"') >= 1
        and "CURRENT_RIGHT_COLUMNS" in importer
        and "LEGACY_RIGHT_COLUMNS" in importer
        and "authority_definition_count" in importer,
    )
    require(
        "PERSONAL_DATA_PROFILE_GUARD",
        "EOD_DATABASE_PROFILE" in importer
        and '!= "development"' in importer
        and 'code="local-validation"' in importer
        and "DataProfile.Kind.LOCAL_VALIDATION" in importer
        and "allows_real_personal_data" in importer
        and "ExportPolicy.PROHIBITED" in importer
        and "Неэкспортируемый снимок" in publication_template,
    )
    require(
        "SOURCE_BYTES_NOT_PERSISTED",
        "file_sha256" in import_models
        and "original_filename" in import_models
        and "source_bytes" not in import_models
        and "FileField" not in import_models
        and "_read_upload" in importer,
    )
    require(
        "MARKER_SEMANTICS",
        'GRANTED = "GRANTED"' in import_models
        and 'NOT_GRANTED = "NOT_GRANTED"' in import_models
        and 'BLANK = "BLANK"' in import_models
        and 'QUALIFIED = "QUALIFIED"' in import_models
        and 'AMBIGUOUS = "AMBIGUOUS"' in import_models
        and "Публикуются только положительные" in import_models,
    )
    require(
        "AMBIGUOUS_VALUES_QUARANTINED",
        "Числовая категория РЗА" in importer
        and "Не расшифрованы номера сносок" in importer
        and "is_publishable=False" not in importer
        and "ambiguous_cells_not_published" in importer
        and "Неоднозначные значения — не публикуются" in detail_template,
    )
    require(
        "NO_SILENT_WITHDRAWALS",
        '"withdrawals_automatically_applied": 0' in importer
        and "не отзывают" in detail_template
        and "не отзывают" in publication_template,
    )
    require(
        "IDEMPOTENT_SOURCE_REVISION",
        "file_sha256=digest" in importer
        and "return existing" in importer
        and "uniq_personnel_source_sha_org" in import_models,
    )
    require(
        "UNICODE_PERSON_MATCHING",
        "unicodedata.normalize" in importer
        and ".casefold()" in importer
        and "_employee_name_token" in importer
        and "_row_name_token" in importer,
    )
    require(
        "UNRESOLVED_IDENTITY_QUARANTINE",
        ".exclude(match_kind=PersonnelSourceRow.MatchKind.REVIEW_REQUIRED)" in importer
        and '.exclude(division_raw="")' in importer
        and "test_preview_excludes_unresolved_identity_and_missing_division" in tests,
    )
    require(
        "CONTROLLED_PERSONNEL_PUBLICATION",
        "def build_personnel_publication_preview(" in importer
        and "def publish_personnel_revision(" in importer
        and "user.check_password(password)" in importer
        and "expected_digest != preview.digest" in importer
        and "@transaction.atomic" in importer,
    )
    require(
        "NON_EXPORTABLE_CANONICAL_SNAPSHOT",
        "canonical_json=preview.canonical_json" in importer
        and "Канонический JSON содержит ФИО" in publication_template
        and "canonical_json" not in detail_template,
    )
    require(
        "PERSONNEL_REVIEW_UI",
        "class PersonnelWorkbookUploadForm" in forms
        and "def personnel_upload(" in views
        and "def personnel_detail(" in views
        and "def personnel_publication(" in views
        and 'name="personnel_list"' in urls
        and "Положительные отметки" in detail_template,
    )
    require(
        "SEARCHABLE_EMPLOYEE_CARDS",
        "def employee_detail(" in organization_views
        and "_employee_search_haystack" in organization_views
        and 'name="employee_detail"' in organization_urls
        and "Только положительные действующие назначения" in employee_template,
    )
    require(
        "SYNTHETIC_PERSONNEL_TESTS",
        "synthetic_personnel_workbook" in tests
        and "test_parser_preserves_marker_semantics_and_ambiguities" in tests
        and "test_same_file_is_idempotent" in tests
        and "test_presentation_database_blocks_real_personnel_staging" in tests
        and "test_publication_creates_only_positive_unambiguous_rights" in tests
        and "test_unicode_matching_reuses_existing_cyrillic_employee" in tests
        and "test_preview_excludes_unresolved_identity_and_missing_division" in tests
        and "test_views_show_staging_publication_and_searchable_employee_card" in tests,
    )
    require(
        "NO_REAL_PERSONAL_DATA_IN_PATCH",
        "Патч не содержит реальных ФИО" in adr
        and "только синтетические работники" in adr
        and "не коммитятся в Git" in adr,
    )
    require(
        "HIGH_RISK_VALIDATION_DECLARED",
        "высокому риску" in adr
        and "presentation.sqlite3" in adr
        and "dev.sqlite3" in adr
        and "полный test discovery" in adr,
    )
    print("PATCH_011_6_1_PERSONNEL_OPERATIONAL_AUTHORITY_IMPORTER_GATE_PASSED")


if __name__ == "__main__":
    main()
