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
    importer = read("src/apps/imports/workplace_documents.py")
    import_models = read("src/apps/imports/models.py")
    workdoc_models = read("src/apps/workplace_docs/models.py")
    workdoc_services = read("src/apps/workplace_docs/services.py")
    forms = read("src/apps/imports/forms.py")
    views = read("src/apps/imports/views.py")
    urls = read("src/apps/imports/urls.py")
    list_template = read("src/templates/imports/workplace_document_list.html")
    upload_template = read("src/templates/imports/workplace_document_upload.html")
    detail_template = read("src/templates/imports/workplace_document_detail.html")
    publication_template = read("src/templates/imports/workplace_document_publication.html")
    registry_template = read("src/templates/workplace_docs/detail.html")
    tests = read("src/apps/imports/tests/test_workplace_document_register_importer.py")
    helper = read("src/apps/imports/tests/workplace_document_register_csv.py")
    adr = read("docs/adr/ADR-011-6-2-workplace-document-register-importer.md")
    target_workplace_migration = read(
        "src/apps/imports/migrations/0008_workplace_document_target_workplace_context.py"
    )

    header_contract = importer.split("WORKPLACE_DOCUMENT_HEADER = (", 1)[1].split(
        ")\nDIRECT_PUBLISHER_ROLE", 1
    )[0]
    require(
        "WORKDOC_STRICT_DIRECT_CSV_CONTRACT",
        "WORKPLACE_DOCUMENT_HEADER" in importer
        and '"register_entry_no"' in header_contract
        and '"index"' not in header_contract
        and '"source_notes"' in header_contract
        and "UTF-8 или UTF-8 с BOM" in importer
        and "Заголовок eod_workplace_document_register.csv" in importer
        and 'attrs={"accept": ".csv,text/csv"}' in forms,
    )
    personnel_row_contract = import_models.split(
        "class PersonnelSourceRow", 1
    )[1].split("class PersonnelAuthorityCell", 1)[0]
    require(
        "PERSONNEL_SOURCE_ROW_CONTRACT_PRESERVED",
        "class ReviewDecision" not in personnel_row_contract
        and "initial_review_status" not in personnel_row_contract
        and "review_decision" not in personnel_row_contract
        and "decision_note" not in personnel_row_contract
        and "reviewed_by" not in personnel_row_contract
        and "reviewed_at" not in personnel_row_contract
        and "reviewed_workplace_document_source_rows" not in personnel_row_contract,
    )
    require(
        "WORKDOC_STAGING_AND_PROVENANCE",
        "class WorkplaceDocumentSourceRevision" in import_models
        and "class WorkplaceDocumentSourceRow" in import_models
        and "class WorkplaceDocumentPublication" in import_models
        and '"source_bytes_persisted": False' in importer
        and "header_signature" in importer
        and "file_sha256" in import_models,
    )
    require(
        "WORKDOC_DEVELOPMENT_LOCAL_PROFILE_ONLY",
        "_require_development_database()" in importer
        and 'code="local-validation"' in importer
        and "ExportPolicy.PROHIBITED" in importer
        and "Презентационная база не изменена" in importer,
    )
    require(
        "WORKDOC_NUMBERING_AND_QUARANTINE",
        "повторяется внутри того же раздела или подраздела" in importer
        and "имеет пропуск или начинается не с 1" in importer
        and "source_index = source_row_number - 2" in importer
        and "Технический index" not in importer
        and "ReviewStatus.REVIEW_REQUIRED" in importer
        and "ReviewStatus.BLOCKED" in importer,
    )
    require(
        "WORKDOC_ELECTRONIC_MARK_NO_PAPER_WAIVER",
        "ElectronicStorageInterpretation" in workdoc_models
        and "NOT_INDICATED" in workdoc_models
        and "storage_form = StorageForm.UNKNOWN" in importer
        and "Источник указывает электронную форму; это не отменяет требования" in importer
        and '"paper_storage_waivers_created": 0' in importer
        and "не разрешение отказаться от бумаги" in detail_template
        and "Отказов от бумаги" in publication_template,
    )
    require(
        "WORKDOC_EXISTING_DOMAIN_PUBLICATION",
        "WorkplaceDocumentList.objects.get_or_create" in importer
        and "WorkplaceDocumentRevision.objects.create" in importer
        and "WorkplaceDocumentEntry.objects.create" in importer
        and "approve_revision" in importer
        and "source_register_entry_no" in workdoc_services
        and "electronic_storage_interpretation" in workdoc_services,
    )
    require(
        "WORKDOC_CONTROLLED_WORKPLACE_MATCH",
        "CONTROLLED_WORKPLACE_ALIASES" in importer
        and '"KOCH_CONTROL_ROOM"' in importer
        and '"CONTROLLED_ALIAS"' in importer
        and "Сопоставлено" in detail_template,
    )
    require(
        "WORKDOC_EXPLICIT_TARGET_WORKPLACE",
        "target_workplace = WorkplaceChoiceField" in forms
        and 'target_workplace=form.cleaned_data["target_workplace"]' in views
        and "target_workplace: Workplace | None = None" in importer
        and '"MANUAL_SELECTION"' in importer
        and '"selected_workplace_code"' in importer
        and "по явному выбору администратора" in detail_template
        and '"matched_workplace"' in target_workplace_migration
        and '"uniq_workdoc_src_context_wp"' in target_workplace_migration,
    )
    require(
        "WORKDOC_CONTROLLED_PUBLICATION",
        "DIRECT_PUBLISHER_ROLE" in importer
        and "expected_digest" in importer
        and "check_password" in views
        and "preview_digest" in forms
        and "только готовые позиции" in publication_template.lower()
        and "Перед публикацией примите решение" in importer,
    )
    require(
        "WORKDOC_AUDITED_ROW_DECISIONS",
        "decide_workplace_document_source_row" in importer
        and "ACCEPT_AS_IS" in import_models
        and "reviewed_by" in import_models
        and "reviewed_at" in import_models
        and "Исключить можно только строку, изначально требующую проверки" in importer
        and "Решение по неоднозначной строке" in detail_template
        and "review_decision" in importer,
    )
    require(
        "WORKDOC_PUBLISHED_STATE_COUNTERS",
        "_refresh_workplace_document_revision_counts(locked)" in importer
        and 'status=PUBLISHED' in detail_template
        and "published_rows_count" in views,
    )
    require(
        "WORKDOC_SEARCH_CARDS_AND_HISTORY",
        "document_type_proposed__icontains" in views
        and "section_name__icontains" in views
        and "document_type_label__icontains" in read("src/apps/workplace_docs/views.py")
        and "Источники импорта" in registry_template
        and "Утверждённые редакции" in registry_template,
    )
    require(
        "WORKDOC_ROUTES_AND_UI",
        "workplace_document_import_upload" in urls
        and "workplace_document_import_publication" in urls
        and "Загрузить CSV-реестр" in list_template
        and "Разобрать в staging" in upload_template
        and "Готово" in detail_template
        and "На проверке" in detail_template
        and "Заблокировано" in detail_template,
    )
    require(
        "WORKDOC_SYNTHETIC_TESTS",
        "synthetic_workplace_document_csv" in helper
        and '"index"' not in helper
        and "test_parser_accepts_exact_header_utf8_bom_and_counts_sections" in tests
        and 'self.assertNotIn("index", WORKPLACE_DOCUMENT_HEADER)' in tests
        and "test_electronic_marker_is_preserved_without_paper_waiver" in tests
        and "test_explicit_workplace_selection_resolves_unknown_source_scope" in tests
        and "test_same_source_context_may_be_reloaded_for_another_explicit_workplace" in tests
        and "test_controlled_publication_creates_approved_revision" in tests
        and "test_upload_detail_preview_and_published_registry_are_visible" in tests,
    )
    require(
        "WORKDOC_NO_REAL_SOURCE_DATA_IN_PATCH",
        "только синтетические" in adr
        and "Реальный CSV" in adr
        and "не включён" in adr,
    )
    print("PATCH_011_6_2_WORKPLACE_DOCUMENT_REGISTER_IMPORTER_GATE_PASSED")


if __name__ == "__main__":
    main()
