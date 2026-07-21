from __future__ import annotations

from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import Client, SimpleTestCase
from django.urls import reverse

from .base import OperationalLogTestCase

ROOT = Path(__file__).resolve().parents[3]
REVISION = "011360"


class RichSemanticPreviewCatalogTests(OperationalLogTestCase):
    def setUp(self) -> None:
        self.client = Client()
        self.client.force_login(
            get_user_model().objects.get(username="operator.demo")
        )

    def workspace_response(self):
        return self.client.get(
            reverse(
                "operational_log:shift_workspace",
                args=(self.journal.pk,),
            )
        )

    def test_related_entry_preview_contains_content_and_operational_context(
        self,
    ) -> None:
        response = self.workspace_response()
        self.assertEqual(response.status_code, 200)
        item = response.context["semantic_reference_catalog"][
            "related_entry"
        ][0]
        preview = item["preview"]
        self.assertIn("summary", preview)
        self.assertIn("status", preview)
        facts = {row["label"]: row["value"] for row in preview["facts"]}
        self.assertIn("Дата и время", facts)
        self.assertIn("Тип записи", facts)
        self.assertIn("Автор", facts)

    def test_equipment_person_and_document_have_rich_preview(self) -> None:
        response = self.workspace_response()
        catalog = response.context["semantic_reference_catalog"]
        for kind in ("equipment", "person", "document"):
            self.assertTrue(catalog[kind])
            preview = catalog[kind][0]["preview"]
            self.assertTrue(preview["summary"])
            self.assertTrue(preview["facts"])

    def test_workspace_exposes_normative_actions_and_visual_hosts(self) -> None:
        response = self.workspace_response()
        for marker in (
            "data-normative-trigger",
            "data-normative-menu",
            'data-normative-action="emergency"',
            'data-normative-action="zn_on"',
            'data-normative-action="zn_off"',
            'data-normative-action="pz_install"',
            'data-normative-action="pz_remove"',
            "data-draft-visas",
            f"?v={REVISION}",
        ):
            self.assertContains(response, marker)


class RichSemanticPreviewRuntimeContractTests(SimpleTestCase):
    def source(self, relative: str) -> str:
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_preview_hides_identity_behind_technical_details(self) -> None:
        navigation = self.source(
            "static/operational_log/draft_reference_navigation.js"
        )
        self.assertIn("draft-reference-preview-summary", navigation)
        self.assertIn("draft-reference-preview-facts", navigation)
        self.assertIn("draft-reference-preview-technical", navigation)
        self.assertIn("function renderPreviewFacts(facts)", navigation)
        self.assertIn("eod:reference-catalog-updated", navigation)

    def test_normative_marker_contract_matches_local_instruction(self) -> None:
        editor = self.source("static/operational_log/draft_editor.js")
        css = self.source("static/system/app.css")
        self.assertIn('top.textContent = annotation.kind.startsWith("pz_") ? "ПЗ" : "ЗН";', editor)
        self.assertIn('bottom.textContent = annotation.pz_number ? `№${annotation.pz_number}` : "";', editor)
        self.assertIn("draft-normative-marker-cross", editor)
        self.assertIn("is-normative-cleared", editor)
        self.assertIn(".draft-normative-marker.is-cleared", css)
        self.assertIn("rotate(45deg)", css)
        self.assertIn("rotate(-45deg)", css)
        self.assertIn("is-emergency-event", css)
