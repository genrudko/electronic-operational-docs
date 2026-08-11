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
