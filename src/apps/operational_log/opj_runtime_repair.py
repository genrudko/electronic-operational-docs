from __future__ import annotations

from collections.abc import Callable

from django.http import HttpRequest, HttpResponse

from .opj_lifecycle_acceptance import clean_journal_view

_STALE_ASSET_VERSION = b"opjlifecycle00501"
_CURRENT_ASSET_VERSION = b"opjlifecycle00615"
_ACCEPTANCE_STYLE_MARKER = b"opj-runtime-acceptance-00615"
_ACCEPTANCE_STYLE = b"""
<style id="opj-runtime-acceptance-00615">
html body.opj-clean-journal-page .approved-journal-table td.approved-journal-date-time {
    display: table-cell !important;
    padding-top: 5px !important;
    text-align: center !important;
    vertical-align: top !important;
}
html body.opj-clean-journal-page .approved-journal-date-time > .opj-entry-date-placeholder,
html body.opj-clean-journal-page .approved-journal-date-time > .opj-clean-time,
html body.opj-clean-journal-page .approved-journal-date-time > small {
    margin-top: 0 !important;
    margin-bottom: 0 !important;
}
html body.opj-clean-journal-page .approved-journal-date-time > .opj-entry-date-placeholder:empty {
    min-height: 0 !important;
}
html body.opj-clean-journal-page .opj-entry-actions-trigger[aria-expanded="true"]
    + .opj-entry-actions-menu:not(.is-floating) {
    position: absolute !important;
    z-index: 800 !important;
    top: calc(100% + 6px) !important;
    right: 0 !important;
    bottom: auto !important;
    left: auto !important;
    display: grid !important;
    width: min(310px, calc(100vw - 24px)) !important;
    max-height: min(420px, calc(100vh - 24px)) !important;
    overflow: auto !important;
    visibility: visible !important;
}
</style>
"""


def _replace_clean_journal_asset_version(response: HttpResponse) -> HttpResponse:
    content_type = response.headers.get("Content-Type", "")
    if response.status_code == 200 and content_type.startswith("text/html"):
        response.content = response.content.replace(
            _STALE_ASSET_VERSION,
            _CURRENT_ASSET_VERSION,
        )
        if _ACCEPTANCE_STYLE_MARKER not in response.content:
            response.content = response.content.replace(
                b"</head>",
                _ACCEPTANCE_STYLE + b"</head>",
                1,
            )
        response.headers["Cache-Control"] = "no-store, max-age=0"
        response.headers["Pragma"] = "no-cache"
    return response


def clean_journal_runtime_view(
    request: HttpRequest,
    journal_id: int,
    *,
    view: Callable[[HttpRequest, int], HttpResponse] = clean_journal_view,
) -> HttpResponse:
    """Serve the acceptance journal with the current JS/CSS asset revision.

    The accepted template still carries the previous revision token. During the
    open visual-acceptance cycle the response is rewritten at the route boundary
    so browsers cannot retain a stale actions controller between rebuilds.
    """

    return _replace_clean_journal_asset_version(view(request, journal_id))
