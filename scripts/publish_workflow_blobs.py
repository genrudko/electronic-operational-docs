#!/usr/bin/env python3
"""Create remote Git blob objects for exact generated workflow bytes.

The GitHub Actions token may create content-addressed blob objects but is not
used to update a branch ref containing workflow changes. The connector applies
the resulting immutable blob SHAs atomically after verifying this manifest.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_ROOT = ROOT / ".github/workflows"
OUTPUT = ROOT / "supply-chain/workflow-blobs.json"


def post_blob(repository: str, token: str, content: bytes) -> str:
    request = urllib.request.Request(
        f"https://api.github.com/repos/{repository}/git/blobs",
        data=json.dumps(
            {
                "content": base64.b64encode(content).decode("ascii"),
                "encoding": "base64",
            }
        ).encode("utf-8"),
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "eod-dependency-provenance/1",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    sha = payload.get("sha", "")
    if len(sha) != 40:
        raise RuntimeError(f"invalid Git blob response: {payload}")
    return sha


def main() -> int:
    repository = os.environ["GITHUB_REPOSITORY"]
    token = os.environ["GITHUB_TOKEN"]
    files = []
    for path in sorted(WORKFLOW_ROOT.glob("*.yml")):
        content = path.read_bytes()
        files.append(
            {
                "path": path.relative_to(ROOT).as_posix(),
                "git_blob_sha": post_blob(repository, token, content),
                "sha256": hashlib.sha256(content).hexdigest(),
                "size": len(content),
            }
        )
    payload = {
        "schema": 1,
        "source_head": os.environ.get("GITHUB_SHA", ""),
        "files": files,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"WORKFLOW_BLOB_MANIFEST=PASS files={len(files)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
