from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

UTF8_BOM = b"\xef\xbb\xbf"
STABLE_PORT = 8765


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def decode_utf8(data: bytes, label: str) -> str:
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RuntimeError(f"{label} is not valid UTF-8.") from exc


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    launcher = root / "scripts" / "run_dev.ps1"
    raw = launcher.read_bytes()

    require(raw.startswith(UTF8_BOM), "run_dev.ps1 must start with an UTF-8 BOM.")
    text = raw.decode("utf-8-sig")
    require("\r\n" in text, "run_dev.ps1 must use CRLF line endings.")
    require("\n" not in text.replace("\r\n", ""), "run_dev.ps1 contains lone LF line endings.")

    required_fragments = (
        "[int]$Port = 8765",
        "[Console]::InputEncoding = $Utf8Encoding",
        "[Console]::OutputEncoding = $Utf8Encoding",
        "$OutputEncoding = $Utf8Encoding",
        '$env:PYTHONUTF8 = "1"',
        '$env:PYTHONIOENCODING = "utf-8"',
        '"http://127.0.0.1:$Port"',
        'manage.py runserver "127.0.0.1:$Port"',
    )
    for fragment in required_fragments:
        require(fragment in text, f"Missing launcher fragment: {fragment}")

    for fragment in ("[int]$Port = 0", "Get-FreeLocalPort", "LocalEndpoint).Port"):
        require(fragment not in text, f"Dynamic-port fragment remains: {fragment}")

    print("UTF8_BOM=PASSED")
    print("CRLF=PASSED")
    print(f"DEFAULT_PORT={STABLE_PORT}")
    print("DYNAMIC_PORT_FALLBACK=DISABLED")

    if os.name != "nt":
        print("WINDOWS_POWERSHELL_RUNTIME_CHECK=DEFERRED_NON_WINDOWS")
        return 0

    powershell = shutil.which("powershell.exe") or shutil.which("powershell")
    require(powershell is not None, "Windows PowerShell executable was not found.")

    result = subprocess.run(
        [
            powershell,
            "-NoLogo",
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(launcher),
            "-CheckOnly",
        ],
        cwd=root,
        capture_output=True,
        check=False,
    )
    stdout = decode_utf8(result.stdout, "PowerShell stdout")
    stderr = decode_utf8(result.stderr, "PowerShell stderr")
    combined = stdout + "\n" + stderr

    require(
        result.returncode == 0,
        f"run_dev.ps1 -CheckOnly failed: {result.returncode}\n{stdout}\n{stderr}",
    )

    expected = (
        "Электронная оперативная документация",
        "Локальный профиль: SQLite",
        "Постоянный адрес: http://127.0.0.1:8765/",
        "Проверка состояния: http://127.0.0.1:8765/health/",
        "Проверка запуска выполнена успешно.",
    )
    for fragment in expected:
        require(fragment in combined, f"Expected UTF-8 output is missing: {fragment}")

    for fragment in ("ForegroundColor", "\ufffd", "Р­Р", "РџС", "Р»Р"):
        require(fragment not in combined, f"Mojibake marker found: {fragment}")

    print("WINDOWS_POWERSHELL_RUNTIME_CHECK=PASSED")
    print("PATCH_003_1_RUNTIME_LAUNCHER_GATE_PASSED")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"LAUNCHER GATE FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
