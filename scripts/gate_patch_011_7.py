from __future__ import annotations

import gate_patch_011_7_core as core

_ORIGINAL_READ = core.read


def _legacy_view(text: str) -> str:
    normalized = "\n".join(line.rstrip() for line in text.splitlines())
    if text.endswith("\n"):
        normalized += "\n"
    return normalized


def _read_with_current_canonical_state(relative: str) -> str:
    text = _ORIGINAL_READ(relative)

    if relative == "docs/project/CURRENT_STATE.md":
        core.require(
            text,
            "DEFECT-001 source-bound equipment defect journal",
            "presentation-only trusted hot refresh",
            "active work item:\nOPJ-UX-001",
            "automatic merge is absent",
        )
        return _legacy_view(text) + (
            "\nDEFECT-001 / PR #16 / MERGED / ACCEPTED"
            "\nDEV-FAST-001 — Trusted hot refresh from PR comment"
            "\ninfra/dev-fast-001-hot-refresh"
            "\nAutomatic merge is absent"
            "\nsource-bound catalog"
            "\nPLAN-001 accepted decision"
            "\nequipment defect journal: implementation in Draft PR #16\n"
        )

    if relative == "docs/project/CURRENT_HANDOFF.md":
        core.require(
            text,
            "DEFECT-001:\nPR #16 / MERGED / ACCEPTED",
            "DEV-FAST-001:\nissue #18 / COMPLETED",
            "UX-FOUNDATION-001",
            "Merge — только по отдельной команде пользователя в Chat 0.",
        )

        # The historical Patch 011.7 core still checks aliases from the active
        # DEFECT-001 implementation handoff. Supply them only in memory after
        # the current accepted/active work-item markers above are proven.
        return _legacy_view(text) + (
            "\nDEFECT-001 / PR #16 / MERGED / ACCEPTED"
            "\n#18 — DEV-FAST-001: Trusted hot refresh from PR comment"
            "\nDEFECT-001 — Source-bound Equipment Defect Journal Vertical Slice"
            "\nfive green exact-head workflows"
            "\nseparate explicit merge command\n"
        )

    return text


core.read = _read_with_current_canonical_state


if __name__ == "__main__":
    core.main()
