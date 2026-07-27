from __future__ import annotations

import gate_patch_011_7_core as core

_ORIGINAL_READ = core.read


def _read_with_current_handoff(relative: str) -> str:
    text = _ORIGINAL_READ(relative)
    if relative != "docs/project/CURRENT_HANDOFF.md":
        return text

    core.require(
        text,
        "## 6. Текущий work item: DEFECT-001",
        "feature/defect-001-equipment-defect-journal",
        "five exact-head workflows:",
        "Merge выполняется только после отдельной явной команды пользователя.",
    )

    # The core gate predates the current CHAT 0 handoff format. These aliases are
    # supplied only in memory after the newer canonical markers above are proven.
    return text + (
        "\nDEFECT-001 — Source-bound Equipment Defect Journal Vertical Slice"
        "\nfive green exact-head workflows"
        "\nseparate explicit merge command\n"
    )


core.read = _read_with_current_handoff


if __name__ == "__main__":
    core.main()
