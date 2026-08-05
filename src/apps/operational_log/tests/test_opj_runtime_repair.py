from __future__ import annotations

from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase

from apps.operational_log.opj_runtime_repair import (
    clean_journal_runtime_view,
)


class OperationalJournalRuntimeRepairTests(SimpleTestCase):
    def setUp(self) -> None:
        self.request = RequestFactory().get("/operations/journal/1/")

    def test_clean_journal_response_uses_current_asset_revision(self) -> None:
        def stale_view(request, journal_id):
            self.assertIs(request, self.request)
            self.assertEqual(journal_id, 1)
            return HttpResponse(
                '<html><head>'
                '<link href="repair.css?v=opjlifecycle00501">'
                '<script src="clean.js?v=opjlifecycle00501"></script>'
                '</head><body></body></html>',
                content_type="text/html; charset=utf-8",
            )

        response = clean_journal_runtime_view(
            self.request,
            1,
            view=stale_view,
        )

        body = response.content.decode("utf-8")
        self.assertNotIn("opjlifecycle00501", body)
        self.assertEqual(body.count("opjlifecycle00615"), 2)
        self.assertEqual(body.count('id="opj-runtime-acceptance-00615"'), 1)
        self.assertIn("td.approved-journal-date-time", body)
        self.assertIn('aria-expanded="true"', body)
        self.assertIn("+ .opj-entry-actions-menu:not(.is-floating)", body)
        self.assertEqual(response.headers["Cache-Control"], "no-store, max-age=0")
        self.assertEqual(response.headers["Pragma"], "no-cache")

    def test_acceptance_style_is_not_duplicated(self) -> None:
        html = (
            '<html><head><style id="opj-runtime-acceptance-00615"></style>'
            '</head><body></body></html>'
        )
        response = clean_journal_runtime_view(
            self.request,
            1,
            view=lambda _request, _journal_id: HttpResponse(
                html,
                content_type="text/html; charset=utf-8",
            ),
        )

        self.assertEqual(
            response.content.decode("utf-8").count("opj-runtime-acceptance-00615"),
            1,
        )

    def test_non_html_response_is_not_rewritten(self) -> None:
        response = clean_journal_runtime_view(
            self.request,
            1,
            view=lambda _request, _journal_id: HttpResponse(
                b"opjlifecycle00501",
                content_type="application/octet-stream",
            ),
        )

        self.assertEqual(response.content, b"opjlifecycle00501")
        self.assertNotIn("Cache-Control", response.headers)
