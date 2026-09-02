from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase

TEMPLATE_ROOTS = (
    "system",
    "organizations",
    "documents",
    "equipment",
    "dispatching",
    "normatives",
    "imports",
    "workplace_docs",
    "operational_documents",
    "equipment_defects",
    "operational_log",
)

# Generic presentation ownership that duplicates canonical UX Platform primitives.
# Feature-specific domain classes are intentionally not banned.
LEGACY_GENERIC_CLASS_TOKENS = frozenset(
    {
        "page-heading",
        "auth-shell",
        "auth-card",
        "auth-form",
        "demo-credentials",
        "button",
        "profile-card",
        "profile-grid",
        "metric",
        "summary-grid",
        "table-wrap",
        "status-chip",
        "form-errors",
        "field-errors",
        "empty-state",
        "clean-list",
    }
)

# These five declarations are legacy OPJ micro-interactions, not viewport/layout
# scaling. Keep the allowance exact: any additional scale declaration, another
# value, or use in another file must fail the contract.
_ALLOWED_SCALE_ANIMATIONS = {
    "src/static/system/app.css": Counter(
        {
            "transform: scale(.84);": 1,
            "transform: scale(.99);": 1,
            "transform: scale(1);": 3,
        }
    )
}

_CLASS_RE = re.compile(r'class=["\']([^"\']+)["\']')


def _class_tokens(source: str) -> set[str]:
    tokens: set[str] = set()
    for value in _CLASS_RE.findall(source):
        tokens.update(value.split())
    return tokens


class UXPlatformMigrationContractTests(SimpleTestCase):
    def test_owner_visible_templates_do_not_use_legacy_generic_design_system(self) -> None:
        template_root = Path(settings.BASE_DIR) / "src" / "templates"
        offenders: list[str] = []
        for root_name in TEMPLATE_ROOTS:
            root = template_root / root_name
            if not root.exists():
                continue
            for path in sorted(root.rglob("*.html")):
                # Print documents intentionally retain their specialised print layout.
                if path.name == "print.html":
                    continue
                source = path.read_text(encoding="utf-8")
                legacy = sorted(_class_tokens(source) & LEGACY_GENERIC_CLASS_TOKENS)
                if legacy:
                    relative = path.relative_to(template_root).as_posix()
                    offenders.append(f"{relative}: {', '.join(legacy)}")
        self.assertEqual(
            offenders,
            [],
            "Legacy generic UX ownership remains on owner-visible templates:\n"
            + "\n".join(offenders),
        )

    def test_core_templates_do_not_disable_mobile_zoom_or_use_scale_hacks(self) -> None:
        roots = [
            Path(settings.BASE_DIR) / "src" / "templates",
            Path(settings.BASE_DIR) / "src" / "static",
        ]
        forbidden = ("user-scalable=no", "maximum-scale=1", "zoom:")
        offenders: list[str] = []
        scale_declarations: dict[str, Counter[str]] = {}
        for root in roots:
            for path in root.rglob("*"):
                if path.suffix not in {".html", ".css"}:
                    continue
                relative = path.relative_to(Path(settings.BASE_DIR)).as_posix()
                source = path.read_text(encoding="utf-8").lower()
                for line_number, line in enumerate(source.splitlines(), start=1):
                    stripped = line.strip()
                    for marker in forbidden:
                        if marker in line:
                            offenders.append(f"{relative}:{line_number}: {marker}")
                    if "transform: scale(" in line:
                        scale_declarations.setdefault(relative, Counter())[stripped] += 1

        all_scale_paths = set(scale_declarations) | set(_ALLOWED_SCALE_ANIMATIONS)
        for relative in sorted(all_scale_paths):
            actual = scale_declarations.get(relative, Counter())
            expected = _ALLOWED_SCALE_ANIMATIONS.get(relative, Counter())
            if actual != expected:
                offenders.append(
                    f"{relative}: scale declarations actual={dict(actual)} expected={dict(expected)}"
                )

        self.assertEqual(
            offenders,
            [],
            "Unsafe mobile scaling contract found:\n" + "\n".join(offenders),
        )

    def test_repair_v7_profiles_reach_useful_inner_workspaces(self) -> None:
        css = (
            Path(settings.BASE_DIR) / "src/static/system/ux_platform_compositions.css"
        ).read_text(encoding="utf-8")
        compact = re.sub(r"\s+", "", css)

        self.assertIn(
            "body.ux-platform.opj-clean-journal-page.da-page:has(>main.opj-main)",
            compact,
        )
        self.assertIn(".da-page:has(.personnel-layout)", css)
        self.assertIn(".authority-workspace", css)
        self.assertIn(".authority-table-wrap", css)
        self.assertIn(".approved-journal-shell", css)
        self.assertIn("width:100%;max-width:none", compact)

    def test_repair_v7_opj_dense_geometry_uses_platform_tokens(self) -> None:
        css = (
            Path(settings.BASE_DIR) / "src/static/system/ux_platform_compositions.css"
        ).read_text(encoding="utf-8")
        compact = re.sub(r"\s+", "", css)

        self.assertIn(
            ":is(.opj-toolbar-primary,.opj-editor-toolbar,.opj-action-strip)",
            compact,
        )
        self.assertIn("padding:var(--theme-space-2)var(--theme-space-3)", compact)
        self.assertIn("min-height:var(--theme-control-height-sm)", compact)
        self.assertIn(
            'opj-workspace[data-page-width="full"].opj-editor-container', compact
        )
        self.assertIn(
            'opj-workspace[data-view-mode="spread"].opj-editor-container', compact
        )

    def test_repair_v7_core_relations_separate_human_and_technical_values(self) -> None:
        template_root = Path(settings.BASE_DIR) / "src/templates"
        equipment = (template_root / "equipment/site_detail.html").read_text(
            encoding="utf-8"
        )
        documents = (template_root / "documents/detail.html").read_text(
            encoding="utf-8"
        )

        for template in (equipment, documents):
            self.assertIn("ux-value-stack", template)
            self.assertIn("ux-value-primary", template)
            self.assertIn("ux-value-secondary ux-technical technical-only", template)

        self.assertNotIn("<strong>{{ row.display_name }}</strong><code", equipment)
        self.assertNotIn(
            "<strong>{{ row.display_name }}</strong></a>\n            <code", documents
        )

    def test_repair_v7_does_not_create_another_acceptance_stylesheet(self) -> None:
        static_root = Path(settings.BASE_DIR) / "src/static"
        forbidden = {"repair_v7.css", "final_fix.css", "owner_acceptance_patch.css"}
        existing = {path.name for path in static_root.rglob("*.css")}

        self.assertTrue(forbidden.isdisjoint(existing))