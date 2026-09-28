"""Local Development overlay bundle validator and extractor."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import stat
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

DEFAULT_INBOX = Path("/home/eodadmin/.local/state/development-bridge/eod-overlay")
MAX_BUNDLE_BYTES = 16 * 1024 * 1024  # 16 MiB
MAX_DECODED_FILE_BYTES = 2 * 1024 * 1024  # 2 MiB
MAX_TOTAL_DECODED_BYTES = 8 * 1024 * 1024  # 8 MiB
MAX_FILES_COUNT = 64
ALLOWED_PREFIXES = ("src/templates/", "src/static/")
PATH_REGEX = re.compile(r"^[A-Za-z0-9._/-]+$")
SHA256_REGEX = re.compile(r"^[0-9a-fA-F]{64}$")
RUN_ID_REGEX = re.compile(r"^[A-Za-z0-9._-]+$")


class LocalOverlayValidationError(Exception):
    """Raised when an overlay bundle or file violates security/format constraints."""


@dataclass(frozen=True)
class LocalOverlayFile:
    path: str
    content_bytes: bytes
    sha256: str


def validate_overlay_path(raw_path: str) -> str:
    if not isinstance(raw_path, str):
        raise LocalOverlayValidationError("file path must be a string")
    if not PATH_REGEX.match(raw_path):
        raise LocalOverlayValidationError(f"path contains unsupported characters: {raw_path}")
    if raw_path.startswith("/"):
        raise LocalOverlayValidationError(f"absolute path is forbidden: {raw_path}")
    if "//" in raw_path:
        raise LocalOverlayValidationError(f"non-canonical path with double slash: {raw_path}")
    if (
        raw_path in {".", ".."}
        or "/./" in f"/{raw_path}/"
        or "/../" in f"/{raw_path}/"
    ):
        raise LocalOverlayValidationError(f"path traversal or non-canonical component: {raw_path}")
    pure = PurePosixPath(raw_path)
    if str(pure) != raw_path:
        raise LocalOverlayValidationError(f"non-canonical path representation: {raw_path}")
    if any(part in {"", ".", ".."} for part in pure.parts):
        raise LocalOverlayValidationError(f"path traversal or non-canonical component: {raw_path}")
    if not raw_path.startswith(ALLOWED_PREFIXES):
        raise LocalOverlayValidationError(f"path is outside allowlist: {raw_path}")
    if raw_path in {"src/templates/", "src/static/"}:
        raise LocalOverlayValidationError(f"path must identify a file, not directory: {raw_path}")
    return str(pure)


def _verify_bundle_path(bundle_path: Path, inbox_dir: Path) -> Path:
    inbox = inbox_dir.resolve()
    try:
        st = bundle_path.lstat()
    except FileNotFoundError:
        raise LocalOverlayValidationError(f"bundle file not found: {bundle_path}")
    except OSError as err:
        raise LocalOverlayValidationError(f"cannot stat bundle file: {err}")

    if stat.S_ISLNK(st.st_mode):
        raise LocalOverlayValidationError("bundle must be a regular non-symlink file")
    if not stat.S_ISREG(st.st_mode):
        raise LocalOverlayValidationError("bundle must be a regular file")

    # Verify no intermediate symlink in parent components and resolved location inside inbox
    resolved_bundle = bundle_path.resolve()
    if resolved_bundle != inbox and inbox not in resolved_bundle.parents:
        raise LocalOverlayValidationError(f"bundle is outside the fixed inbox ({inbox}): {bundle_path}")

    current = bundle_path.parent
    while True:
        try:
            curr_st = current.lstat()
        except OSError as err:
            raise LocalOverlayValidationError(f"cannot access directory component {current}: {err}")
        if stat.S_ISLNK(curr_st.st_mode):
            raise LocalOverlayValidationError(f"symlink in bundle path component: {current}")
        if current.resolve() == inbox:
            break
        if current == current.parent:
            raise LocalOverlayValidationError(f"bundle path is outside inbox: {bundle_path}")
        current = current.parent

    if st.st_size == 0:
        raise LocalOverlayValidationError("bundle file is empty")
    if st.st_size > MAX_BUNDLE_BYTES:
        raise LocalOverlayValidationError(f"bundle exceeds maximum allowed size of {MAX_BUNDLE_BYTES} bytes")

    return bundle_path


def validate_local_overlay_bundle(
    bundle_path: Path | str,
    *,
    expected_run_id: str | None = None,
    inbox_dir: Path | str = DEFAULT_INBOX,
) -> list[LocalOverlayFile]:
    bundle_p = Path(bundle_path)
    inbox_p = Path(inbox_dir)
    _verify_bundle_path(bundle_p, inbox_p)

    try:
        raw_text = bundle_p.read_text(encoding="utf-8")
        data = json.loads(raw_text)
    except json.JSONDecodeError as err:
        raise LocalOverlayValidationError(f"invalid JSON bundle: {err}")
    except Exception as err:
        raise LocalOverlayValidationError(f"cannot read bundle file: {err}")

    if not isinstance(data, dict):
        raise LocalOverlayValidationError("bundle JSON root must be an object")

    # Strict version check: must equal integer 1
    if type(data.get("version")) is not int or data.get("version") != 1:
        raise LocalOverlayValidationError("bundle version must equal integer 1")

    # Strict run_id check: required non-empty string, and if expected_run_id is provided, must match
    run_id = data.get("run_id")
    if not isinstance(run_id, str) or not run_id:
        raise LocalOverlayValidationError("bundle must contain a non-empty string 'run_id'")
    if not RUN_ID_REGEX.match(run_id):
        raise LocalOverlayValidationError(f"bundle run_id contains invalid characters: {run_id}")
    if expected_run_id is not None and run_id != expected_run_id:
        raise LocalOverlayValidationError(
            f"bundle run_id '{run_id}' does not match expected run_id '{expected_run_id}'"
        )

    # Strict files list check: must be a list
    if "files" not in data or not isinstance(data["files"], list):
        raise LocalOverlayValidationError("bundle JSON must contain a 'files' list")

    raw_files = data["files"]
    if len(raw_files) < 1 or len(raw_files) > MAX_FILES_COUNT:
        raise LocalOverlayValidationError(
            f"bundle must contain 1..{MAX_FILES_COUNT} files; got {len(raw_files)}"
        )

    validated_files: list[LocalOverlayFile] = []
    seen_paths: set[str] = set()
    total_decoded_bytes = 0

    for idx, item in enumerate(raw_files):
        if not isinstance(item, dict):
            raise LocalOverlayValidationError(f"file entry #{idx} is not an object")

        # Strict canonical field names check: must use exactly 'path', 'content', 'sha256'
        # Reject aliases like 'filename', 'content_base64', 'sha_256', 'hash'
        if "path" not in item or not isinstance(item["path"], str):
            raise LocalOverlayValidationError(f"file entry #{idx} is missing canonical string field 'path'")
        if "content" not in item or not isinstance(item["content"], str):
            raise LocalOverlayValidationError(f"file entry #{idx} is missing canonical string field 'content'")
        if "sha256" not in item or not isinstance(item["sha256"], str):
            raise LocalOverlayValidationError(f"file entry #{idx} is missing canonical string field 'sha256'")

        for forbidden_alias in ("filename", "content_base64", "sha_256", "hash"):
            if forbidden_alias in item:
                raise LocalOverlayValidationError(
                    f"file entry #{idx} contains forbidden field alias '{forbidden_alias}'"
                )

        raw_p = item["path"]
        norm_path = validate_overlay_path(raw_p)
        if norm_path in seen_paths:
            raise LocalOverlayValidationError(f"duplicate file path in bundle: {norm_path}")
        seen_paths.add(norm_path)

        b64_content = item["content"]
        try:
            content_bytes = base64.b64decode(b64_content, validate=True)
        except Exception:
            raise LocalOverlayValidationError(f"invalid base64 content for {norm_path}")

        if len(content_bytes) > MAX_DECODED_FILE_BYTES:
            raise LocalOverlayValidationError(
                f"file {norm_path} decoded size ({len(content_bytes)} bytes) exceeds maximum {MAX_DECODED_FILE_BYTES} bytes (2 MiB)"
            )

        total_decoded_bytes += len(content_bytes)
        if total_decoded_bytes > MAX_TOTAL_DECODED_BYTES:
            raise LocalOverlayValidationError(
                f"bundle total decoded size ({total_decoded_bytes} bytes) exceeds maximum {MAX_TOTAL_DECODED_BYTES} bytes (8 MiB)"
            )

        expected_sha = item["sha256"]
        if not SHA256_REGEX.match(expected_sha):
            raise LocalOverlayValidationError(f"missing or invalid sha256 checksum format for {norm_path}")

        computed_sha = hashlib.sha256(content_bytes).hexdigest()
        if computed_sha.lower() != expected_sha.lower():
            raise LocalOverlayValidationError(
                f"sha256 mismatch for {norm_path}: expected {expected_sha}, got {computed_sha}"
            )

        validated_files.append(
            LocalOverlayFile(
                path=norm_path,
                content_bytes=content_bytes,
                sha256=computed_sha.lower(),
            )
        )

    return validated_files


def extract_local_overlay_bundle(
    bundle_path: Path | str,
    destination_dir: Path | str,
    *,
    expected_run_id: str | None = None,
    inbox_dir: Path | str = DEFAULT_INBOX,
) -> list[LocalOverlayFile]:
    dest = Path(destination_dir)
    dest.mkdir(parents=True, exist_ok=True)

    files = validate_local_overlay_bundle(
        bundle_path, expected_run_id=expected_run_id, inbox_dir=inbox_dir
    )
    manifest = []
    for idx, item in enumerate(files):
        out_file = dest / str(idx)
        out_file.write_bytes(item.content_bytes)
        os.chmod(out_file, 0o600)
        manifest.append({"index": idx, "path": item.path, "sha256": item.sha256})

    (dest / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return files


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate and extract local overlay bundle")
    parser.add_argument("action", choices=["validate", "extract"])
    parser.add_argument("bundle_path", type=Path)
    parser.add_argument("stage_dir", type=Path, nargs="?")
    parser.add_argument("--run-id", type=str, default=None, help="Expected run_id matching bundle")
    parser.add_argument("--inbox-dir", type=Path, default=DEFAULT_INBOX)

    args = parser.parse_args()
    try:
        if args.action == "validate":
            files = validate_local_overlay_bundle(
                args.bundle_path, expected_run_id=args.run_id, inbox_dir=args.inbox_dir
            )
            print(f"VALID: {len(files)} files")
            for f in files:
                print(f"{f.sha256} {f.path}")
        elif args.action == "extract":
            if not args.stage_dir:
                parser.error("stage_dir is required for extract")
            files = extract_local_overlay_bundle(
                args.bundle_path,
                args.stage_dir,
                expected_run_id=args.run_id,
                inbox_dir=args.inbox_dir,
            )
            print(f"EXTRACTED: {len(files)} files to {args.stage_dir}")
            for idx, f in enumerate(files):
                print(f"{idx}\t{f.path}\t{f.sha256}")
    except LocalOverlayValidationError as err:
        print(f"ERROR: {err}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
