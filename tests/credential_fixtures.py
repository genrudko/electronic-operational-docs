from __future__ import annotations

import secrets


def ephemeral_credential(label: str = "Synthetic") -> str:
    """Return a process-local test credential that is never stored as a tracked literal."""
    return "".join((label, "-", secrets.token_urlsafe(32)))
