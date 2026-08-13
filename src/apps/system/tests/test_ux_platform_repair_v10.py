from __future__ import annotations

from pathlib import Path

from django.test import SimpleTestCase

ROOT = Path(__file__).resolve().parents[4]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


class UxPlatformRepairV10SourceContractTests(SimpleTestCase):
    def test_operational_documents_registry_uses_canonical_hierarchy_and_filter_spans(self) -> None:
        template = read("src/templates/operational_documents/registry.html")

        self.assertIn("operational_documents/operational_documents.css", template)
        self.assertIn('class="da-page-header opdoc-page-header"', template)
        self.assertNotIn('class="da-page-header da-page-header-compact"', template)
        self.assertIn('class="ux-kicker">Формы по утверждённым источникам', template)
        self.assertIn('class="da-field ux-field-two-thirds"', template)
        self.assertGreaterEqual(template.count('class="da-field ux-field-third"'), 4)
        self.assertIn('class="opdoc-date-range ux-field-full"', template)
        self.assertIn('class="ux-form-actions"', template)

    def test_operational_documents_related_entities_are_semantic_navigation_surfaces(self) -> None:
        template = read("src/templates/operational_documents/record_detail.html")

        self.assertIn("operational_documents/operational_documents.css", template)
        self.assertIn('class="opdoc-record-detail"', template)
        self.assertIn('>← К журналам</a>', template)
        self.assertIn(
            'href="{% url \'equipment:detail\' item.equipment.public_id %}"', template
        )
        self.assertIn('class="ux-value-primary">{{ item.dispatcher_name_snapshot }}', template)
        self.assertIn('class="ux-technical">{{ item.equipment_code_snapshot }}', template)
        self.assertIn(
            'href="{% url \'documents:detail\' item.document.public_id %}"', template
        )
        self.assertIn('class="ux-value-primary">{{ item.title_snapshot }}', template)
        self.assertIn(
            'class="ux-technical">{{ item.registration_number_snapshot|default:"Без номера" }}',
            template,
        )
        self.assertIn('class="opdoc-related-relation">{{ item.get_link_type_display }}', template)
        self.assertIn('class="opdoc-related-relation">{{ item.relation_name_snapshot }}', template)
        self.assertNotIn(
            "{{ item.target_record.registration_number }} · {{ item.target_record.title }}",
            template,
        )
        self.assertNotIn(
            "{{ item.source_record.registration_number }} · {{ item.source_record.title }}",
            template,
        )

    def test_operational_documents_feature_css_owns_density_padding_and_affordance(self) -> None:
        css = read("src/static/operational_documents/operational_documents.css")

        for contract in (
            ".opdoc-registry-notices",
            ".opdoc-summary",
            ".opdoc-date-range",
            ".opdoc-related-list",
            ".opdoc-related-link",
            "padding: var(--theme-space-3)",
            ".opdoc-related-link:hover",
            ".opdoc-related-link:focus-visible",
        ):
            self.assertIn(contract, css)
        self.assertNotIn("!important", css)
        self.assertNotIn("margin-left: -", css)
        self.assertNotIn("margin-inline-start: -", css)

    def test_personnel_current_view_is_server_rendered_navigation_state(self) -> None:
        template = read("src/templates/organizations/directory.html")

        self.assertIn(
            'class="personnel-contour-card is-current" '
            'href="{% url \'organizations:directory\' %}" aria-current="page"',
            template,
        )
        current_card = template.index('class="personnel-contour-card is-current"')
        dispatch_card = template.index("#dispatch")
        self.assertLess(current_card, dispatch_card)
        self.assertIn("personnel_directory.css' %}?v=pa001d3", template)

    def test_personnel_workspace_and_category_density_have_feature_owned_geometry(self) -> None:
        css = read("src/static/organizations/personnel_directory.css")

        self.assertIn(
            "grid-template-columns:minmax(19rem,22rem) minmax(0,1fr)", css
        )
        self.assertIn(
            "grid-template-columns:clamp(19rem,17vw,23rem) minmax(0,1fr)", css
        )
        self.assertIn("gap:var(--theme-space-3)", css)
        self.assertIn('.personnel-contour-card[aria-current="page"]', css)
        self.assertIn("background:var(--theme-selected)", css)
        self.assertNotIn("clamp(20rem,24%,30rem)", css)
        self.assertNotIn("margin-left:-", css.replace(" ", ""))
        self.assertNotIn("margin-inline-start:-", css.replace(" ", ""))

    def test_v10_does_not_create_repair_stylesheet(self) -> None:
        self.assertTrue(
            (ROOT / "src/static/operational_documents/operational_documents.css").exists()
        )
        for path in (
            "src/static/system/repair_v10.css",
            "src/static/system/owner_final.css",
            "src/static/system/last_fix.css",
        ):
            self.assertFalse((ROOT / path).exists())
