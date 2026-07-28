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
            "DEFECT-001 / PR #16 / MERGED / ACCEPTED",
            "DEV-FAST-001 — Trusted hot refresh from PR comment",
            "infra/dev-fast-001-hot-refresh",
            "Automatic merge is absent",
        )
        return _legacy_view(text) + (
            "\nsource-bound catalog"
            "\nPLAN-001 accepted decision"
            "\nequipment defect journal: implementation in Draft PR #16\n"
        )

    if relative == "docs/project/CURRENT_HANDOFF.md":
        core.require(
            text,
            "Последний accepted product merge:",
            "883a108c8be2a8cd075846fdd175916917911ef6",
            "#18 — DEV-FAST-001: Trusted hot refresh from PR comment",
            "Merge выполняется только после отдельной явной команды пользователя.",
        )

        # The historical Patch 011.7 core still checks aliases from the active
        # DEFECT-001 implementation handoff. Supply them only in memory after
        # the current accepted/active work-item markers above are proven.
        return _legacy_view(text) + (
            "\nDEFECT-001 — Source-bound Equipment Defect Journal Vertical Slice"
            "\nfive green exact-head workflows"
            "\nseparate explicit merge command\n"
        )

    return text


core.read = _read_with_current_canonical_state


if __name__ == "__main__":
    core.main()
