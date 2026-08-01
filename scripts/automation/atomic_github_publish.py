from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Protocol

SHA_RE = re.compile(r"^[0-9a-f]{40}$")
REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
BRANCH_RE = re.compile(r"^[A-Za-z0-9._/-]+$")


class PublishError(RuntimeError):
    pass


@dataclass(frozen=True)
class FileSpec:
    repository_path: str
    local_path: Path
    sha256: str
    size: int


class Client(Protocol):
    def request(
        self, method: str, path: str, payload: dict[str, Any] | None = None
    ) -> dict[str, Any]: ...


class GithubClient:
    def __init__(self, token: str, api_url: str) -> None:
        self.token = token
        self.api_url = api_url.rstrip("/")

    def request(
        self, method: str, path: str, payload: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        body = json.dumps(payload).encode() if payload is not None else None
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "eod-atomic-publisher/1",
        }
        if body is not None:
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(
            f"{self.api_url}{path}", data=body, headers=headers, method=method
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                raw = response.read()
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(errors="replace")
            raise PublishError(f"GitHub HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise PublishError(f"GitHub network failure: {exc.reason}") from exc
        result = json.loads(raw.decode()) if raw else {}
        if not isinstance(result, dict):
            raise PublishError("GitHub returned non-object JSON")
        return result


def repository(value: str) -> str:
    result = value.strip()
    if not REPO_RE.fullmatch(result):
        raise PublishError("repository must be owner/name")
    return result


def branch(value: str) -> str:
    result = value.strip()
    if (
        not BRANCH_RE.fullmatch(result)
        or result.startswith("/")
        or result.endswith("/")
        or ".." in result
        or "@{" in result
        or result.endswith(".lock")
    ):
        raise PublishError(f"unsafe branch: {value!r}")
    return result


def repo_path(value: str) -> str:
    result = value.strip()
    if result.startswith("/") or "\\" in result or "\x00" in result:
        raise PublishError(f"unsafe repository path: {value!r}")
    pure = PurePosixPath(result)
    if not result or any(part in {"", ".", ".."} for part in pure.parts):
        raise PublishError(f"non-canonical repository path: {value!r}")
    return pure.as_posix()


def file_specs(values: list[str]) -> tuple[FileSpec, ...]:
    if not values:
        raise PublishError("at least one --file is required")
    result: list[FileSpec] = []
    seen: set[str] = set()
    for value in values:
        if "=" not in value:
            raise PublishError("--file must be repository/path=local/path")
        target, source = value.split("=", 1)
        target = repo_path(target)
        local = Path(source)
        if not local.is_file():
            raise PublishError(f"local file does not exist: {local}")
        if target in seen:
            raise PublishError(f"duplicate target: {target}")
        seen.add(target)
        content = local.read_bytes()
        result.append(
            FileSpec(
                target,
                local,
                hashlib.sha256(content).hexdigest(),
                len(content),
            )
        )
    return tuple(sorted(result, key=lambda item: item.repository_path))


def valid_sha(value: str, field: str) -> str:
    if not SHA_RE.fullmatch(value):
        raise PublishError(f"{field} must be lowercase 40-hex")
    return value


def ref_api(repo: str, ref: str) -> str:
    owner, name = repo.split("/", 1)
    encoded = urllib.parse.quote(ref, safe="/")
    return f"/repos/{owner}/{name}/git/ref/heads/{encoded}"


def publish(
    client: Client,
    repo: str,
    ref: str,
    expected_head: str,
    message: str,
    files: tuple[FileSpec, ...],
) -> dict[str, Any]:
    repo = repository(repo)
    ref = branch(ref)
    expected_head = valid_sha(expected_head, "expected_head")
    if not message.strip():
        raise PublishError("commit message is empty")
    owner, name = repo.split("/", 1)

    current = client.request("GET", ref_api(repo, ref))
    current_sha = current.get("object", {}).get("sha")
    if current_sha != expected_head:
        raise PublishError(
            f"optimistic lock failed: live={current_sha} expected={expected_head}"
        )

    commit = client.request(
        "GET", f"/repos/{owner}/{name}/git/commits/{expected_head}"
    )
    base_tree = commit.get("tree", {}).get("sha")
    valid_sha(base_tree, "base_tree")

    tree_entries: list[dict[str, str]] = []
    evidence: list[dict[str, Any]] = []
    for item in files:
        blob = client.request(
            "POST",
            f"/repos/{owner}/{name}/git/blobs",
            {
                "content": base64.b64encode(item.local_path.read_bytes()).decode(),
                "encoding": "base64",
            },
        )
        blob_sha = valid_sha(blob.get("sha"), f"blob {item.repository_path}")
        tree_entries.append(
            {
                "path": item.repository_path,
                "mode": "100644",
                "type": "blob",
                "sha": blob_sha,
            }
        )
        evidence.append(
            {
                "path": item.repository_path,
                "blob_sha": blob_sha,
                "sha256": item.sha256,
                "size": item.size,
            }
        )

    tree = client.request(
        "POST",
        f"/repos/{owner}/{name}/git/trees",
        {"base_tree": base_tree, "tree": tree_entries},
    )
    tree_sha = valid_sha(tree.get("sha"), "tree")
    new_commit = client.request(
        "POST",
        f"/repos/{owner}/{name}/git/commits",
        {"message": message.strip(), "tree": tree_sha, "parents": [expected_head]},
    )
    commit_sha = valid_sha(new_commit.get("sha"), "commit")

    client.request(
        "PATCH",
        ref_api(repo, ref),
        {"sha": commit_sha, "force": False},
    )
    final = client.request("GET", ref_api(repo, ref))
    if final.get("object", {}).get("sha") != commit_sha:
        raise PublishError("post-update ref verification failed")

    return {
        "repository": repo,
        "branch": ref,
        "previous_head": expected_head,
        "commit_sha": commit_sha,
        "tree_sha": tree_sha,
        "files": evidence,
        "optimistic_lock": "PASSED",
        "force_update": False,
    }


class FakeClient:
    def __init__(self, live: str, base_tree: str, result: str) -> None:
        self.live = live
        self.base_tree = base_tree
        self.result = result
        self.updated = False
        self.calls: list[tuple[str, str, dict[str, Any] | None]] = []

    def request(
        self, method: str, path: str, payload: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        self.calls.append((method, path, payload))
        if method == "GET" and "/git/ref/heads/" in path:
            return {"object": {"sha": self.result if self.updated else self.live}}
        if method == "GET" and "/git/commits/" in path:
            return {"tree": {"sha": self.base_tree}}
        if method == "POST" and path.endswith("/git/blobs"):
            count = sum(
                call[0] == "POST" and call[1].endswith("/git/blobs")
                for call in self.calls
            )
            return {"sha": f"{count:040x}"}
        if method == "POST" and path.endswith("/git/trees"):
            return {"sha": "2" * 40}
        if method == "POST" and path.endswith("/git/commits"):
            return {"sha": self.result}
        if method == "PATCH" and "/git/ref/heads/" in path:
            if payload != {"sha": self.result, "force": False}:
                raise AssertionError(payload)
            self.updated = True
            return {}
        raise AssertionError((method, path, payload))


def self_test() -> None:
    from tempfile import TemporaryDirectory

    with TemporaryDirectory() as directory:
        sample = Path(directory) / "sample.txt"
        sample.write_text("sample\n", encoding="utf-8")
        specs = file_specs([f"docs/sample.txt={sample}"])
        client = FakeClient("a" * 40, "b" * 40, "c" * 40)
        result = publish(
            client,
            "genrudko/electronic-operational-docs",
            "main",
            "a" * 40,
            "test",
            specs,
        )
        assert result["commit_sha"] == "c" * 40
        assert client.updated
        try:
            publish(
                FakeClient("d" * 40, "e" * 40, "f" * 40),
                "genrudko/electronic-operational-docs",
                "main",
                "a" * 40,
                "stale",
                specs,
            )
        except PublishError:
            pass
        else:
            raise AssertionError("stale expected head was accepted")
        for unsafe in ("../x", "/root", "a\\b", "a/../b"):
            try:
                repo_path(unsafe)
            except PublishError:
                pass
            else:
                raise AssertionError(f"unsafe path accepted: {unsafe}")


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("publish")
    run.add_argument("--repository", required=True)
    run.add_argument("--branch", required=True)
    run.add_argument("--expected-head", required=True)
    run.add_argument("--message", required=True)
    run.add_argument("--file", action="append", default=[])
    run.add_argument("--token-env", default="GITHUB_TOKEN")
    run.add_argument("--api-url", default="https://api.github.com")
    run.add_argument("--dry-run", action="store_true")
    sub.add_parser("self-test")
    args = parser.parse_args()
    try:
        if args.command == "self-test":
            self_test()
            print("atomic_github_publish self-test: OK")
            return 0
        files = file_specs(args.file)
        if args.dry_run:
            print(
                json.dumps(
                    {
                        "dry_run": True,
                        "repository": repository(args.repository),
                        "branch": branch(args.branch),
                        "expected_head": valid_sha(
                            args.expected_head, "expected_head"
                        ),
                        "files": [
                            {
                                "path": item.repository_path,
                                "sha256": item.sha256,
                                "size": item.size,
                            }
                            for item in files
                        ],
                        "protocol": [
                            "verify live ref equals expected head",
                            "create blobs and one tree",
                            "create one commit",
                            "update ref with force=false",
                            "verify final ref",
                        ],
                    },
                    indent=2,
                )
            )
            return 0
        token = os.environ.get(args.token_env)
        if not token:
            raise PublishError(f"{args.token_env} is not set")
        result = publish(
            GithubClient(token, args.api_url),
            args.repository,
            args.branch,
            args.expected_head,
            args.message,
            files,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (PublishError, OSError, json.JSONDecodeError) as exc:
        print(f"ATOMIC PUBLISH BLOCKED: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
