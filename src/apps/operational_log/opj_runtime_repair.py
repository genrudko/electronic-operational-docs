from __future__ import annotations

from collections.abc import Callable

from django.http import HttpRequest, HttpResponse

from .opj_lifecycle_acceptance import clean_journal_view

_STALE_ASSET_VERSION = b"opjlifecycle00501"
_CURRENT_ASSET_VERSION = b"opjlifecycle00614"


def _replace_clean_journal_asset_version(response: HttpResponse) -> HttpResponse:
    content_type = response.headers.get("Content-Type", "")
    if response.status_code == 200 and content_type.startswith("text/html"):
        response.content = response.content.replace(
            _STALE_ASSET_VERSION,
            _CURRENT_ASSET_VERSION,
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
