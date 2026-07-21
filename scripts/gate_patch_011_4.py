from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def require(name: str, condition: bool) -> None:
    if not condition:
        raise SystemExit(f"{name}=FAILED")
    print(f"{name}=PASSED")


def load_glossary_module():
    path = ROOT / "src/apps/imports/domain_glossary.py"
    spec = importlib.util.spec_from_file_location("eod_domain_glossary_gate", path)
    if spec is None or spec.loader is None:
        raise SystemExit("TECHNICAL_ENGLISH_GLOSSARY=FAILED")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> None:
    models = read("src/apps/imports/models.py")
    services = read("src/apps/imports/services.py")
    forms = read("src/apps/imports/forms.py")
    views = read("src/apps/imports/views.py")
    urls = read("src/apps/imports/urls.py")
    list_template = read("src/templates/imports/list.html")
    upload_template = read("src/templates/imports/upload.html")
    profile_template = read("src/templates/imports/data_profiles.html")
    detail_template = read("src/templates/imports/detail.html")
    publication_template = read("src/templates/imports/publication.html")
    migration = read("src/apps/imports/migrations/0004_data_profiles_import_foundation.py")
    adr = read("docs/adr/ADR-011-4-data-profiles-import-foundation.md")
    glossary_doc = read("docs/domain/technical-english-glossary.md")

    require(
        "CONTROLLED_DATA_PROFILES",
        "class DataProfile(models.Model):" in models
        and '"presentation-safe"' in models
        and '"local-validation"' in models
        and '"automated-tests"' in models
        and "uniq_default_data_profile_per_org" in models,
    )
    require(
        "PROFILE_SAFETY_POLICY",
        "allows_real_personal_data" in models
        and "class ExportPolicy(models.TextChoices):" in models
        and 'LOCAL_VALIDATION = "LOCAL_VALIDATION"' in models
        and "обычный экспорт должен быть запрещён" in models,
    )
    require(
        "PROFILE_BOUND_IMPORT_PROVENANCE",
        "data_profile = models.ForeignKey(" in models
        and "source_reference = models.CharField(" in models
        and "header_signature = models.CharField(" in models
        and '"data_profile": {' in services
        and '"reference": batch.source_reference' in services,
    )
    require(
        "REUSABLE_MAPPING_TEMPLATES",
        "class ImportMappingTemplate(models.Model):" in models
        and "def _matching_mapping_template(" in services
        and "def _save_mapping_template(" in services
        and "MAPPING_TEMPLATE_APPLIED" in models
        and "MAPPING_TEMPLATE_SAVED" in models
        and 'TEMPLATE = "TEMPLATE", "Из сохранённой схемы"' in models
        and "ImportColumn.MappingOrigin.TEMPLATE" in services,
    )
    require(
        "IMPORT_PROFILE_USER_INTERFACE",
        "DataProfileChoiceField" in forms
        and "organization=employee.organization" in views
        and 'name="data_profiles"' in urls
        and "Профили данных" in list_template
        and "Профиль данных" in upload_template
        and "Профиль является частью происхождения данных" in profile_template
        and "data-profile-notice" in detail_template
        and "Публикация в профиль" in publication_template,
    )
    require(
        "PUBLICATION_SCHEMA_V2",
        'eod.import.publication.v2' in models
        and 'PUBLICATION_SCHEMA = "eod.import.publication.v2"' in services
        and '"data_profile": {' in services,
    )

    glossary = load_glossary_module()
    issues = glossary.validate_technical_english_glossary()
    by_code = glossary.glossary_by_code_name()
    require(
        "TECHNICAL_ENGLISH_GLOSSARY",
        not issues
        and by_code["circuit_breaker"].english_term == "circuit breaker"
        and by_code["disconnector"].english_term == "disconnector"
        and by_code["earthing_switch"].english_term == "earthing switch"
        and by_code["operational_jurisdiction"].russian_term == "оперативное ведение"
        and "буквальный машинный" in glossary_doc.lower(),
    )
    require(
        "DATA_PROFILE_MIGRATION",
        "class Migration(migrations.Migration):" in migration
        and 'name="DataProfile"' in migration
        and 'name="ImportMappingTemplate"' in migration
        and "create_profiles_and_assign_batches" in migration
        and 'name="data_profile"' in migration,
    )
    require(
        "FULL_VALIDATION_PROFILE_DECLARED",
        "профиль `FULL`" in adr
        and "полный test discovery" in adr
        and "Patch 011.4 не содержит реальных ФИО" in adr,
    )
    print("PATCH_011_4_DATA_PROFILES_IMPORT_FOUNDATION_GATE_PASSED")


if __name__ == "__main__":
    main()
