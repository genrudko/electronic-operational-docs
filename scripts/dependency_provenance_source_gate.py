#!/usr/bin/env python3
"""Independent executable/config source discovery for dependency provenance.

This checker deliberately does not import dependency_provenance_core.  It is the
second implementation used to prove that the canonical inventory has not missed
an executable or configuration surface that can acquire dependency/build inputs.
"""

from __future__ import annotations

import ast
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SHELL_SUFFIXES = {".bash", ".sh"}
TASK_NAMES = {
    "build.xml",
    "gnumakefile",
    "justfile",
    "makefile",
    "pom.xml",
    "taskfile.yaml",
    "taskfile.yml",
}
TASK_SUFFIXES = (".gradle", ".gradle.kts", ".make", ".mk")
OPERATOR_NAME_RE = re.compile(
    r"(?:bootstrap|build|deploy|install|operator|provision|release|setup|task)",
    re.I,
)
SHELL_SHEBANG_RE = re.compile(r"^#!.*\b(?:ba|da|k|z)?sh\b")
PYTHON_SHEBANG_RE = re.compile(r"^#!.*\bpython(?:3(?:\.\d+)?)?\b")
PROCESS_CALLS = {
    "os.popen",
    "os.system",
    "subprocess.Popen",
    "subprocess.call",
    "subprocess.check_call",
    "subprocess.check_output",
    "subprocess.run",
}


@dataclass(frozen=True)
class TrackedPath:
    path: str
    mode: str


def tracked_records(root: Path = ROOT) -> list[TrackedPath]:
    result = subprocess.run(
        ["git", "ls-files", "--stage", "-z"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    records: list[TrackedPath] = []
    for raw in result.stdout.split(b"\0"):
        if not raw:
            continue
        metadata, raw_path = raw.split(b"\t", 1)
        mode = metadata.split(b" ", 1)[0].decode("ascii")
        records.append(TrackedPath(raw_path.decode("utf-8"), mode))
    return sorted(records, key=lambda item: item.path)


def first_line(root: Path, path: str) -> str:
    with (root / path).open(encoding="utf-8", errors="replace") as handle:
        return handle.readline().rstrip("\n")


def is_workflow(path: str) -> bool:
    return path.startswith(".github/workflows/") and path.endswith((".yml", ".yaml"))


def is_compose(path: str) -> bool:
    name = Path(path).name.lower()
    return name.startswith(("compose", "docker-compose")) and path.endswith((".yml", ".yaml"))


def is_dockerfile(path: str) -> bool:
    name = Path(path).name
    return name == "Dockerfile" or name.startswith("Dockerfile.")


def is_task_file(path: str) -> bool:
    name = Path(path).name.lower()
    lowered = path.lower()
    return name in TASK_NAMES or name.startswith("taskfile.") or lowered.endswith(TASK_SUFFIXES)


def call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = call_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    return ""


def python_invokes_process(root: Path, path: str) -> bool:
    try:
        tree = ast.parse((root / path).read_text(encoding="utf-8", errors="replace"))
    except SyntaxError:
        return False
    return any(
        isinstance(node, ast.Call) and call_name(node.func) in PROCESS_CALLS
        for node in ast.walk(tree)
    )


def independently_applicable_paths(root: Path = ROOT) -> set[str]:
    """Return the independently discovered applicable source boundary."""

    result: set[str] = set()
    for record in tracked_records(root):
        path = record.path
        suffix = Path(path).suffix.lower()
        name = Path(path).name.lower()
        if (
            is_workflow(path)
            or is_compose(path)
            or is_dockerfile(path)
            or suffix in SHELL_SUFFIXES | {".ps1"}
            or is_task_file(path)
        ):
            result.add(path)
            continue
        shebang = first_line(root, path)
        if not suffix and SHELL_SHEBANG_RE.search(shebang):
            result.add(path)
            continue
        if suffix != ".py":
            continue
        if (
            path.startswith("deploy/")
            or OPERATOR_NAME_RE.search(name)
            or record.mode == "100755"
            or PYTHON_SHEBANG_RE.search(shebang)
            or python_invokes_process(root, path)
        ):
            result.add(path)
    return result


def main() -> int:
    paths = independently_applicable_paths(ROOT)
    print(f"DEPENDENCY_PROVENANCE_SOURCE_GATE=PASS applicable={len(paths)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
