from __future__ import annotations

from pathlib import Path


SRC_ROOT = Path(__file__).resolve().parents[3]


def _read(relative_path: str) -> str:
    return (SRC_ROOT / relative_path).read_text(encoding="utf-8")


def test_opj_width_profiles_have_distinct_geometry_and_persistence_chain() -> None:
    shared_css = _read("static/system/ux_platform_compositions.css")
    lifecycle_css = _read("static/operational_log/opj_lifecycle_acceptance_repair.css")
    workspace_js = _read("static/operational_log/draft_workspace.js")

    assert 'data-page-width="standard"' in shared_css
    assert "width:min(100%,72rem)" in shared_css
    assert 'data-page-width="wide"' in lifecycle_css
    assert "width: min(100%, 1680px) !important" in lifecycle_css
    assert 'data-page-width="full"' in lifecycle_css
    assert "width: 100% !important" in lifecycle_css

    assert '["standard", "wide", "full"].includes(normalized)' in workspace_js
    assert "workspace.dataset.pageWidth = pageWidthPreference" in workspace_js
    assert '"journal_width"' in workspace_js
    assert "pageWidthPreference.toUpperCase()" in workspace_js
    assert "payload.journal_width" in workspace_js


def test_personnel_contours_use_server_resolvable_destinations() -> None:
    directory = _read("templates/organizations/directory.html")
    authority = _read("templates/organizations/authority_registry.html")

    assert "authority_registry' %}#dispatch" not in directory
    assert "authority_registry' %}#related" not in directory
    assert "view=dispatch" in directory
    assert "view=related&amp;scope=grid" in directory
    assert "view=related&amp;scope=site" in directory
    assert "view=related&amp;scope=commercial" in directory

    assert 'data-initial-view="{{ initial_view }}"' in authority
    assert 'request.GET.view|default:"matrix"' in authority
    assert 'data-authority-panel="dispatch"{% if initial_view != \'dispatch\' %} hidden' in authority
    assert 'data-authority-panel="related"{% if initial_view != \'related\' %} hidden' in authority


def test_personnel_grid_geometry_has_intentional_stretch_ownership() -> None:
    css = _read("static/organizations/personnel_directory.css")

    assert ".personnel-contours {" in css
    assert "align-items:stretch" in css
    assert "grid-template-rows:auto minmax(0,1fr) auto" in css
    assert ".personnel-recent-grid {" in css
    assert "align-items:start" in css
    assert ".personnel-directory-relation-heading" in css
    assert "padding:var(--theme-space-2) var(--theme-space-4)" in css
    assert ".personnel-service-relations" in css
    assert ".personnel-service-relation" in css


def test_authority_controls_headers_and_audit_have_semantic_contracts() -> None:
    template = _read("templates/organizations/authority_registry.html")
    css = _read("static/organizations/personnel_authority_matrix.css")
    js = _read("static/organizations/personnel_authority_matrix.js")

    assert 'data-expand-all><svg' in template
    assert "#icon-add" not in template
    assert "data-expand-all-label" in template
    assert "Свернуть всё" in template
    assert "collapsed.size === 0" in js
    assert "Развернуть всё" in js
    assert "Свернуть всё" in js

    assert ".authority-right-header > :is(.matrix-sticky-name,.matrix-sticky-position,.matrix-sticky-qualification)" in css
    assert "vertical-align:middle" in css

    assert "data-active-view=\"{{ initial_view }}\"" in template
    assert 'authority-toolbar[data-active-view="checks"]' in css
    assert "toolbar.dataset.activeView = activeView" in js

    assert "authority-evaluation-header" in template
    for label in (
        "Дата и время",
        "Сотрудник",
        "Контекст",
        "Проверяемое действие",
        "Объект",
        "Результат",
    ):
        assert label in template
    assert "authority_action_label" in template
    assert "authority_action_technical_label" in template
    assert "item.subject_type }} · {{ item.subject_id" in template
    assert ".authority-evaluation-row[hidden] { display:none; }" in css
    assert "@media (max-width:56.25rem)" in css


def test_human_text_and_import_profiles_do_not_use_arbitrary_word_breaking() -> None:
    shared_css = _read("static/system/ux_platform_compositions.css")
    imports = _read("templates/imports/list.html")

    readable_rule = shared_css.split(
        ".ux-profile-strip .data-profile-chip strong,.ux-readable-value",
        maxsplit=1,
    )[1].split("}", maxsplit=1)[0]
    assert "overflow-wrap:break-word" in readable_rule
    assert "overflow-wrap:anywhere" not in readable_rule

    technical_rule = shared_css.split(
        ".ux-technical,.ux-technical-chip",
        maxsplit=1,
    )[1].split("}", maxsplit=1)[0]
    assert "overflow-wrap:anywhere" in technical_rule

    assert "import-profile-grid" in imports
    assert "import-profile-card" in imports
    assert "Уровень данных" in imports
    assert "Экспорт" in imports
    assert "mapping_template_count" in imports
    assert "import-safety-notice" in imports
    assert "import-header-actions__primary" in imports
    assert "import-header-nav" in imports


def test_management_filter_and_operational_document_metadata_are_compact() -> None:
    dispatching = _read("templates/dispatching/registry.html")
    opdocs = _read("templates/operational_documents/registry.html")

    assert "ux-compact-filter-row disclosure-body equipment-filter-form" in dispatching
    assert "ux-form-grid disclosure-body equipment-filter-form" not in dispatching

    assert "opdoc-record-meta__technical" in opdocs
    assert "Техническая запись" in opdocs
    assert 'class="da-status-chip is-warning">Техническая запись' not in opdocs
    assert "not record.is_source_bound" in opdocs
