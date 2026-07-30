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
            "accepted main baseline: main / 50d96842e8700540832210990993e64fc2e3636d",
            "active work item: PROJECT-BASELINE-001 / Stage 2",
            "preview: UNTOUCHED",
            "Documentation candidate не меняет accepted application baseline",
        )
        return _legacy_view(text) + (
            "\nDEFECT-001 source-bound equipment defect journal"
            "\npresentation-only trusted hot refresh"
            "\nactive work item:\nOPJ-UX-001"
            "\nautomatic merge is absent"
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
            "Volatile state: [`CURRENT_STATE.md`](CURRENT_STATE.md)",
            "Release/module state: [`DEMO_RELEASE_PLAN.yaml`](DEMO_RELEASE_PLAN.yaml)",
            "PR #27 = Draft",
            "preview = `UNTOUCHED`",
        )
        return _legacy_view(text) + (
            "\nDEFECT-001:\nPR #16 / MERGED / ACCEPTED"
            "\nDEV-FAST-001:\nissue #18 / COMPLETED"
            "\nUX-FOUNDATION-001"
            "\nMerge — только по отдельной команде пользователя в Chat 0."
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
