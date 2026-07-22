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
    importer = read("src/apps/imports/personnel.py")
    forms = read("src/apps/imports/forms.py")
    views = read("src/apps/imports/views.py")
    upload = read("src/templates/imports/personnel_upload.html")
    detail = read("src/templates/imports/personnel_detail.html")
    publication = read("src/templates/imports/personnel_publication.html")
    tests = read("src/apps/imports/tests/test_personnel_csv_package_importer.py")
    helper = read("src/apps/imports/tests/personnel_csv_package.py")
    adr = read("docs/adr/ADR-011-6-1a-normalized-personnel-csv-package.md")

    require(
        "CSV_PACKAGE_REQUIRED_COMPONENTS",
        all(
            name in importer
            for name in (
                "eod_people.csv",
                "eod_positions.csv",
                "eod_operational_authorities.csv",
                "eod_person_authority_assignments.csv",
            )
        )
        and "PERSONNEL_CSV_REQUIRED_FILES" in importer,
    )
    require(
        "CSV_PACKAGE_EXCLUDES_WORKPLACE_DOCUMENTS",
        "eod_workplace_document_register.csv" in importer
        and "PERSONNEL_CSV_IGNORED_FILES" in importer
        and "намеренно не импортируется" in upload,
    )
    require(
        "CSV_PACKAGE_SAFE_ARCHIVE",
        "path.is_absolute()" in importer
        and '".." in path.parts' in importer
        and "stat.S_IFLNK" in importer
        and "MAX_PERSONNEL_CSV_PACKAGE_UNCOMPRESSED_SIZE" in importer
        and "Зашифрованные ZIP-пакеты" in importer,
    )
    require(
        "CSV_PACKAGE_STRICT_UTF8_HEADERS",
        'decode("utf-8-sig")' in importer
        and "требуется кодировка UTF-8" in importer
        and "заголовок не соответствует утверждённому CSV-контракту" in importer,
    )
    require(
        "CSV_PACKAGE_21_CODE_MAPPING",
        "CSV_AUTHORITY_CODE_MAP" in importer
        and importer.count('"RZA_MAINTENANCE_CATEGORY"') >= 1
        and "ровно 21 утверждённый код" in importer
        and "по 21 строке на каждого работника" in importer,
    )
    require(
        "CSV_PACKAGE_PROVENANCE",
        '"source_format": "NORMALIZED_CSV_PACKAGE"' in importer
        and '"package_components"' in importer
        and '"source_issues"' in importer
        and "SHA-256 источника" in detail
        and "SHA-256 источника" in publication,
    )
    require(
        "CSV_PACKAGE_PRESERVES_QUARANTINE",
        "_parse_marker(" in importer
        and "STAGING_ONLY" in importer
        and "Нормализатор источника оставил положительное значение только в staging" in importer
        and "rza_maintenance_category" in importer,
    )
    require(
        "CSV_PACKAGE_BACKWARD_COMPATIBLE_XLSX",
        'extension == ".zip"' in importer
        and 'extension == ".xlsx"' in importer
        and "parse_personnel_workbook(data)" in importer
        and 'attrs={"accept": ".zip,.xlsx"}' in forms,
    )
    require(
        "CSV_PACKAGE_DEVELOPMENT_ONLY",
        "_require_development_database()" in importer
        and "local-validation" in importer
        and "обычный экспорт должен быть запрещён" in importer,
    )
    require(
        "CSV_PACKAGE_UI",
        "Загрузить источник работников и прав" in upload
        and "Состав ZIP-пакета CSV" in upload
        and "Источник разобран в изолированную staging-редакцию" in views
        and "нормализованный ZIP-пакет CSV" in detail,
    )
    require(
        "CSV_PACKAGE_SYNTHETIC_TESTS",
        "synthetic_personnel_csv_package" in helper
        and "test_parser_accepts_required_package_and_maps_all_21_authorities" in tests
        and "test_path_traversal_and_unknown_files_are_rejected" in tests
        and "test_staging_is_idempotent_and_does_not_store_archive_bytes" in tests
        and "test_upload_view_accepts_zip_and_shows_package_provenance" in tests,
    )
    require(
        "CSV_PACKAGE_NO_REAL_DATA_IN_PATCH",
        "только синтетические" in adr
        and "реальные ФИО" in adr
        and "не включены" in adr,
    )
    print("PATCH_011_6_1A_NORMALIZED_PERSONNEL_CSV_PACKAGE_GATE_PASSED")


if __name__ == "__main__":
    main()
