#!/usr/bin/env python3
"""Classify colour-related !important declarations in screen and print CSS."""

import argparse
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GLOBS = ("src/static/system/*.css", "src/static/equipment_defects/*.css", "src/static/operational_log/*.css")
PROPS = {
    "background",
    "background-color",
    "border",
    "border-color",
    "box-shadow",
    "color",
    "color-scheme",
    "fill",
    "outline",
    "outline-color",
    "text-shadow",
}
RULE = re.compile(r"(?P<selector>[^{}]+)\{(?P<body>[^{}]*)\}", re.S)
DECL = re.compile(r"(?P<property>[-\w]+)\s*:\s*(?P<value>[^;{}]*!important)", re.I)


def read(path, ref):
    if not ref:
        return path.read_text(encoding="utf-8")
    return subprocess.run(
        ["git", "show", f"{ref}:{path.relative_to(ROOT).as_posix()}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def audit(ref=None):
    findings = []
    for path in sorted({p for glob in GLOBS for p in ROOT.glob(glob)}):
        css = re.sub(r"/\*.*?\*/", "", read(path, ref), flags=re.S)
        print_at = css.find("@media print")
        for rule in RULE.finditer(css):
            for decl in DECL.finditer(rule["body"]):
                prop = decl["property"].lower()
                if prop not in PROPS and not prop.startswith("border-"):
                    continue
                findings.append(
                    {
                        "file": path.relative_to(ROOT).as_posix(),
                        "selector": " ".join(rule["selector"].split()),
                        "property": prop,
                        "value": " ".join(decl["value"].split()),
                        "line": css.count("\n", 0, rule.start()) + 1,
                        "media": "print" if print_at >= 0 and rule.start() > print_at else "screen",
                    }
                )
    return {
        "ref": ref or "working-tree",
        "screen_count": sum(x["media"] == "screen" for x in findings),
        "print_count": sum(x["media"] == "print" for x in findings),
        "findings": findings,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ref")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--max-screen", type=int)
    args = parser.parse_args()
    report = audit(args.ref)
    payload = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    if args.max_screen is not None and report["screen_count"] > args.max_screen:
        raise SystemExit(
            f"screen colour-related !important count {report['screen_count']} exceeds {args.max_screen}"
        )


if __name__ == "__main__":
    main()
