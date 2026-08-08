#!/usr/bin/env python3
"""Regenerate all five locks from the accepted non-circular bootstrap root.

The accepted repository locks are never overwritten by this verifier. Candidate
locks are produced in an isolated temporary directory and compared byte for byte.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import dependency_provenance_implementation as implementation

ROOT = Path(__file__).resolve().parents[1]
LOCK_DIR = ROOT / "requirements/locks"
BOOTSTRAP = ROOT / "requirements/bootstrap.txt"
PROFILES = ("tooling", "build", "runtime", "dev", "browser")


def main() -> int:
    # Keep the verifier work-root inside the canonical generator namespace so
    # normalize_lock_header() removes the ephemeral path exactly as it does for
    # the accepted apply path. A distinct random prefix would leak into
    # pip-compile "via" comments and make byte-exact regeneration impossible.
    with tempfile.TemporaryDirectory(prefix="eod-supply-") as directory:
        work = Path(directory)
        distributions = implementation.verified_bootstrap_wheelhouse(work)
        rendered_bootstrap = implementation.render_bootstrap(distributions)
        accepted_bootstrap = BOOTSTRAP.read_text(encoding="utf-8")
        if rendered_bootstrap != accepted_bootstrap:
            print(
                "LOCK_REGENERATION=FAIL rule=tooling-bootstrap-root "
                "evidence=bootstrap-manifest-drift",
                file=sys.stderr,
            )
            return 1

        generator_python = implementation.bootstrap_environment(work)
        candidate_dir = work / "candidate-locks"
        original_lock_dir = implementation.LOCK_DIR
        implementation.LOCK_DIR = candidate_dir
        try:
            implementation.generate_locks(generator_python, work)
        finally:
            implementation.LOCK_DIR = original_lock_dir

        mismatches = []
        digests = {}
        for profile in PROFILES:
            accepted = LOCK_DIR / f"{profile}.txt"
            candidate = candidate_dir / f"{profile}.txt"
            if accepted.read_bytes() != candidate.read_bytes():
                mismatches.append(profile)
            digests[profile] = implementation.sha256_file(candidate)

        if mismatches:
            print(
                "LOCK_REGENERATION=FAIL rule=exact-generated-lock "
                f"evidence={','.join(mismatches)}",
                file=sys.stderr,
            )
            return 1

    print(
        "LOCK_REGENERATION=PASS "
        + json.dumps(digests, sort_keys=True, separators=(",", ":"))
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
