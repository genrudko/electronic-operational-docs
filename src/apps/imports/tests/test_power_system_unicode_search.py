from pathlib import Path

from django.test import SimpleTestCase

from apps.imports.unicode_search import unicode_casefold, unicode_text_matches

ROOT = Path(__file__).resolve().parents[3]


class PowerSystemUnicodeSearchTests(SimpleTestCase):
    def test_cyrillic_search_is_case_insensitive(self):
        self.assertTrue(unicode_text_matches("ШОТ", "шот"))
        self.assertTrue(unicode_text_matches("ЩПТ-1", "щпт"))
        self.assertTrue(unicode_text_matches("шкаф ШОТ КТП-1", "ШОТ"))

    def test_nfkc_normalizes_compatible_unicode(self):
        self.assertEqual(unicode_casefold("ＡＢＣ ШОТ"), "abc шот")

    def test_nested_json_values_are_searchable(self):
        value = {
            "source_flags": {
                "dc_equipment_designation": "ЩПТ",
                "dispatcher_name": "ЩПТ-1",
            }
        }
        self.assertTrue(unicode_text_matches(value, "щпт-1"))
        self.assertFalse(unicode_text_matches(value, "шот"))

    def test_runtime_contract_uses_database_independent_filter(self):
        views = (ROOT / "apps/imports/views.py").read_text(encoding="utf-8")
        helper = (ROOT / "apps/imports/unicode_search.py").read_text(encoding="utf-8")
        self.assertIn("filter_power_system_occurrences", views)
        self.assertIn('unicodedata.normalize("NFKC"', helper)
        self.assertIn(".casefold()", helper)

    def test_publication_preview_is_lazy_and_has_progress_feedback(self):
        detail = (ROOT / "templates/imports/power_system_detail.html").read_text(
            encoding="utf-8"
        )
        publication = (
            ROOT / "templates/imports/power_system_publication.html"
        ).read_text(encoding="utf-8")
        review_js = (
            ROOT / "static/imports/power_system_review.js"
        ).read_text(encoding="utf-8")
        self.assertIn("data-power-system-preview-trigger", detail)
        self.assertIn("request.GET.show_snapshot", publication)
        self.assertIn("ps-canonical-snapshot-placeholder", publication)
        self.assertIn('setAttribute("aria-busy", "true")', review_js)
