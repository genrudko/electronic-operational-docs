#!/usr/bin/env python3
# isort: skip_file
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path


START_TEXT = """Восстанови основной интеграционный контекст проекта
«Электронная оперативная документация» исключительно из приложенного
`EOD_CURRENT_CONTEXT.zip` и материалов, созданных после него.

Сначала, не создавая патч, выведи:

1. назначение проекта и границы независимого демонстрационного прототипа;
2. роль пользователя и формат полностью автономных Python-патчей;
3. project root, branch, полный Git HEAD и состояние worktree;
4. последний визуально принятый patch и commit;
5. технические изменения после принятого baseline, если они есть;
6. последнюю неуспешную попытку, причину и результат rollback;
7. текущий этап и следующий конкретный шаг;
8. обязательный двухфазный workflow:
   - pre-patch snapshot перед каждым Patch/Repair;
   - обновление `EOD_CURRENT_CONTEXT.zip` после каждого визуально принятого Patch/Repair;
9. ограничения по реальным данным, SQLite, push и промышленному статусу;
10. перечень файлов или данных, которых не хватает для безопасного продолжения.

При расхождении применяй приоритет:

1. Git bundle и manifest;
2. CURRENT_STATE.md;
3. миграции и diagnostics;
4. patch-логи;
5. PATCH_HISTORY.md и DECISION_LOG.md;
6. чат;
7. исторические планы.

Не создавай новый патч, пока не подтвердил целостность пакета и точный baseline.
Не проси пользователя вручную редактировать код.
Каждый Patch/Repair должен быть единым полным Python-скриптом с preflight,
backup обеих БД, rollback, Ruff, compileall, Django check, миграциями,
gate, тестами, локальным commit и без автоматического push.
"""


class ContextError(RuntimeError):
    pass


def run(
    args: list[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        args,
        cwd=str(cwd),
        env=env,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if check and completed.returncode != 0:
        raise ContextError(
            f"Команда завершилась с кодом {completed.returncode}: "
            f"{subprocess.list2cmdline(args)}\n{completed.stdout}"
        )
    return completed


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        text.replace("\r\n", "\n"),
        encoding="utf-8",
        newline="\n",
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_token(value: str) -> str:
    token = re.sub(r"[^0-9A-Za-zА-Яа-я._-]+", "_", value.strip())
    return token.strip("._-")[:80] or "unspecified"


def find_python(root: Path) -> Path:
    for candidate in (
        root / ".venv" / "Scripts" / "python.exe",
        root / ".venv" / "bin" / "python",
    ):
        if candidate.exists():
            return candidate
    return Path(sys.executable)


def capture(
    destination: Path,
    title: str,
    args: list[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
) -> dict[str, object]:
    completed = run(args, cwd=cwd, env=env, check=False)
    write_text(
        destination,
        f"# {title}\n\n"
        f"COMMAND: {subprocess.list2cmdline(args)}\n"
        f"RETURN_CODE: {completed.returncode}\n\n"
        f"{completed.stdout}",
    )
    return {
        "title": title,
        "command": args,
        "return_code": completed.returncode,
        "file": destination.name,
    }


def copy_recent_logs(root: Path, destination: Path) -> dict[str, object]:
    destination.mkdir(parents=True, exist_ok=True)
    logs_dir = root / "logs"
    copied: list[str] = []
    skipped: list[dict[str, object]] = []
    if not logs_dir.exists():
        return {"copied": copied, "skipped": skipped}

    candidates = sorted(
        (path for path in logs_dir.glob("*.log") if path.is_file()),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )[:30]
    for path in candidates:
        size = path.stat().st_size
        if size > 4 * 1024 * 1024:
            skipped.append(
                {"name": path.name, "size_bytes": size, "reason": "too_large"}
            )
            continue
        shutil.copy2(path, destination / path.name)
        copied.append(path.name)
    return {"copied": copied, "skipped": skipped}


def zip_tree(source: Path, destination: Path) -> None:
    with zipfile.ZipFile(
        destination,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as archive:
        for path in sorted(source.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(source).as_posix())


def verify_git(root: Path, allow_dirty: bool) -> tuple[str, str, str, bool]:
    git_root = Path(
        run(["git", "rev-parse", "--show-toplevel"], cwd=root).stdout.strip()
    ).resolve()
    if git_root != root:
        raise ContextError(f"Ожидался Git root {root}, получен {git_root}")

    branch = run(["git", "branch", "--show-current"], cwd=root).stdout.strip()
    head = run(["git", "rev-parse", "HEAD"], cwd=root).stdout.strip()
    status = run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=root,
    ).stdout
    clean = not status.strip()
    if not clean and not allow_dirty:
        raise ContextError(
            "Worktree не чистый. Контекстный пакет принятого baseline "
            "или pre-patch snapshot создаётся только из чистого состояния."
        )
    return branch, head, status, clean


def make_package(args: argparse.Namespace) -> int:
    root = Path(args.root).expanduser().resolve()
    if not root.exists():
        raise ContextError(f"Корень проекта не существует: {root}")

    branch, head, status, clean = verify_git(root, args.allow_dirty)
    now = datetime.now().astimezone()
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    output_dir = (
        Path(args.output).expanduser().resolve()
        if args.output
        else root / "backups" / "context_snapshots"
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.command == "pre-patch":
        subject = args.for_patch
        subject_token = safe_token(subject)
        archive_name = (
            f"eod_prepatch_snapshot_{timestamp}_{head[:8]}_{subject_token}.zip"
        )
        stable_name = "EOD_PREPATCH_SNAPSHOT_CURRENT.zip"
        marker_name = "latest_prepatch_snapshot.json"
        package_kind = "PRE_PATCH"
        accepted_patch = ""
        next_patch = subject
        note = args.note
    else:
        subject = args.accepted_patch
        subject_token = safe_token(subject)
        archive_name = (
            f"eod_accepted_context_{timestamp}_{head[:8]}_{subject_token}.zip"
        )
        stable_name = "EOD_CURRENT_CONTEXT.zip"
        marker_name = "latest_accepted_context.json"
        package_kind = "ACCEPTED"
        accepted_patch = args.accepted_patch
        next_patch = args.next_patch
        note = args.acceptance_note

    archive_path = output_dir / archive_name
    stable_path = output_dir / stable_name
    project_python = find_python(root)

    with tempfile.TemporaryDirectory(
        prefix="eod_context_",
        dir=str(output_dir),
    ) as temp_name:
        staging = Path(temp_name)
        metadata_dir = staging / "metadata"
        source_dir = staging / "source"
        state_dir = staging / "project_state"
        logs_dir = staging / "recent_logs"
        metadata_dir.mkdir(parents=True, exist_ok=True)
        source_dir.mkdir(parents=True, exist_ok=True)

        commands: list[dict[str, object]] = []
        command_specs = [
            (
                "git_status.txt",
                "Git status",
                ["git", "status", "--short", "--branch", "--untracked-files=all"],
            ),
            (
                "git_log.txt",
                "Последние 100 коммитов",
                [
                    "git",
                    "log",
                    "-100",
                    "--decorate",
                    "--date=iso-strict",
                    "--pretty=format:%H%x09%ad%x09%an%x09%s",
                ],
            ),
            (
                "git_branches.txt",
                "Git branches",
                ["git", "branch", "-vv", "--all"],
            ),
            ("git_tags.txt", "Git tags", ["git", "tag", "--sort=-creatordate"]),
            ("git_remotes.txt", "Git remotes", ["git", "remote", "-v"]),
            ("tracked_files.txt", "Git tracked files", ["git", "ls-files"]),
            (
                "working_diff.patch",
                "Working tree diff",
                ["git", "diff", "--binary"],
            ),
            (
                "staged_diff.patch",
                "Staged diff",
                ["git", "diff", "--cached", "--binary"],
            ),
            (
                "head_summary.txt",
                "HEAD summary",
                ["git", "show", "--stat", "--oneline", "--decorate", "HEAD"],
            ),
        ]
        for filename, title, command in command_specs:
            commands.append(
                capture(
                    metadata_dir / filename,
                    title,
                    command,
                    cwd=root,
                )
            )

        commands.append(
            capture(
                metadata_dir / "python_environment.txt",
                "Python and Django environment",
                [
                    str(project_python),
                    "-c",
                    (
                        "import sys; "
                        "print('executable=' + sys.executable); "
                        "print('version=' + sys.version.replace('\\n', ' ')); "
                        "import django; "
                        "print('django=' + django.get_version())"
                    ),
                ],
                cwd=root,
            )
        )

        if (root / "manage.py").exists():
            for profile in ("presentation", "development"):
                env = os.environ.copy()
                env["EOD_DATABASE_PROFILE"] = profile
                commands.append(
                    capture(
                        metadata_dir / f"django_check_{profile}.txt",
                        f"Django check ({profile})",
                        [str(project_python), "manage.py", "check"],
                        cwd=root,
                        env=env,
                    )
                )
                commands.append(
                    capture(
                        metadata_dir / f"migrations_{profile}.txt",
                        f"Migration plan ({profile})",
                        [str(project_python), "manage.py", "showmigrations", "--plan"],
                        cwd=root,
                        env=env,
                    )
                )

        source_archive = source_dir / "tracked_source_at_head.zip"
        run(
            [
                "git",
                "archive",
                "--format=zip",
                f"--output={source_archive}",
                "HEAD",
            ],
            cwd=root,
        )
        git_bundle = source_dir / "repository_all_refs.bundle"
        run(["git", "bundle", "create", str(git_bundle), "--all"], cwd=root)

        repo_state = root / "docs" / "project_state"
        if repo_state.exists():
            shutil.copytree(repo_state, state_dir, dirs_exist_ok=True)
        else:
            state_dir.mkdir(parents=True, exist_ok=True)
            write_text(
                state_dir / "MISSING_PROJECT_STATE_NOTICE.md",
                "# Внимание\n\n"
                "`docs/project_state/` ещё не внедрён в принятый baseline.\n",
            )

        logs_inventory = copy_recent_logs(root, logs_dir)

        handoff = (
            "# ЭОД — CHAT_HANDOFF\n\n"
            f"- Тип пакета: `{package_kind}`\n"
            f"- Создан: `{now.isoformat()}`\n"
            f"- Root: `{root}`\n"
            f"- Branch: `{branch}`\n"
            f"- HEAD: `{head}`\n"
            f"- Worktree clean: `{str(clean).lower()}`\n"
            f"- Принятый patch: `{accepted_patch or 'не применимо'}`\n"
            f"- Следующий patch: `{next_patch or 'не указан'}`\n"
            f"- Примечание: {note or 'не указано'}\n\n"
            "Начинать новый чат следует с файла `START_NEW_CHAT.txt`, "
            "лежащего в корне этого архива.\n"
        )
        readme = (
            "# ПРОЧИТАТЬ СНАЧАЛА\n\n"
            "1. Загрузите этот ZIP в новый основной интеграционный чат.\n"
            "2. Откройте `START_NEW_CHAT.txt` из корня архива.\n"
            "3. Скопируйте его текст первым сообщением.\n"
            "4. Не используйте старый чат или исторический master plan "
            "как единственный источник baseline.\n"
        )
        write_text(staging / "README_FIRST.md", readme)
        write_text(staging / "START_NEW_CHAT.txt", START_TEXT)
        write_text(staging / "CHAT_HANDOFF.md", handoff)

        manifest = {
            "schema_version": 2,
            "project": "electronic-operational-docs",
            "package_kind": package_kind,
            "project_root": str(root),
            "created_at": now.isoformat(),
            "branch": branch,
            "head": head,
            "worktree_clean": clean,
            "worktree_status_porcelain": status.splitlines(),
            "accepted_patch": accepted_patch,
            "next_patch": next_patch,
            "note": note,
            "python_executable": str(project_python),
            "source_archive": source_archive.name,
            "git_bundle": git_bundle.name,
            "start_text": "START_NEW_CHAT.txt",
            "handoff": "CHAT_HANDOFF.md",
            "recent_logs": logs_inventory,
            "captured_commands": commands,
            "excluded_sensitive_content": [
                "SQLite databases",
                ".env and secrets",
                "real personal data",
                "real production source documents",
                "virtual environment",
                "database backups",
            ],
        }
        write_text(
            staging / "snapshot_manifest.json",
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        )
        zip_tree(staging, archive_path)

    archive_sha = sha256_file(archive_path)
    archive_sha_path = archive_path.with_suffix(".zip.sha256")
    write_text(archive_sha_path, f"{archive_sha}  {archive_path.name}\n")

    shutil.copy2(archive_path, stable_path)
    stable_sha = sha256_file(stable_path)
    stable_sha_path = stable_path.with_suffix(".zip.sha256")
    write_text(stable_sha_path, f"{stable_sha}  {stable_path.name}\n")
    write_text(output_dir / "START_NEW_CHAT.txt", START_TEXT)

    marker = {
        "schema_version": 2,
        "project": "electronic-operational-docs",
        "package_kind": package_kind,
        "created_at": now.isoformat(),
        "branch": branch,
        "head": head,
        "worktree_clean": clean,
        "accepted_patch": accepted_patch,
        "next_patch": next_patch,
        "archive_path": str(archive_path),
        "archive_name": archive_path.name,
        "archive_sha256": archive_sha,
        "stable_archive_path": str(stable_path),
        "stable_archive_name": stable_path.name,
        "stable_archive_sha256": stable_sha,
        "start_text_path": str(output_dir / "START_NEW_CHAT.txt"),
    }
    marker_path = output_dir / marker_name
    write_text(
        marker_path,
        json.dumps(marker, ensure_ascii=False, indent=2) + "\n",
    )

    print("EOD_CONTEXT_PACKAGE_CREATED")
    print(f"KIND={package_kind}")
    print(f"ARCHIVE={archive_path}")
    print(f"SHA256={archive_sha}")
    print(f"STABLE_ARCHIVE={stable_path}")
    print(f"STABLE_SHA256={stable_sha}")
    print(f"START_TEXT={output_dir / 'START_NEW_CHAT.txt'}")
    print(f"MARKER={marker_path}")
    print(f"BRANCH={branch}")
    print(f"HEAD={head}")
    print(f"WORKTREE_CLEAN={clean}")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Управление snapshot и continuity package проекта ЭОД."
    )
    parser.add_argument(
        "--root",
        default=r"G:\electronic-operational-docs",
        help="Корень Git-репозитория.",
    )
    parser.add_argument(
        "--output",
        default="",
        help="Каталог результатов; по умолчанию backups/context_snapshots.",
    )
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="Разрешить аварийный пакет грязного worktree.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    pre = subparsers.add_parser(
        "pre-patch",
        help="Создать snapshot перед Patch/Repair.",
    )
    pre.add_argument("--for-patch", required=True)
    pre.add_argument("--note", default="")

    accepted = subparsers.add_parser(
        "accepted",
        help="Обновить главный пакет после визуальной приёмки.",
    )
    accepted.add_argument("--accepted-patch", required=True)
    accepted.add_argument("--next-patch", required=True)
    accepted.add_argument("--acceptance-note", default="")

    return parser.parse_args()


def main() -> int:
    return make_package(parse_args())


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ContextError as exc:
        print(f"CONTEXT_ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from None
