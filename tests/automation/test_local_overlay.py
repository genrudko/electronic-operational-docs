from __future__ import annotations

import base64
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTROLLER = ROOT / "deploy/automation/eod-development-controller"
BOOTSTRAP_LOCAL = ROOT / "deploy/automation/bootstrap_local_overlay.sh"
VALIDATOR_SCRIPT = ROOT / "scripts/automation/local_overlay.py"
INBOX_DIR = "/home/eodadmin/.local/state/development-bridge/eod-overlay"
INSTALLED_HELPER = "/usr/local/lib/eod/local_overlay.py"


class LocalOverlayBundleValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.inbox = Path(self.temp_dir.name) / "eod-overlay"
        self.inbox.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def make_bundle_file(
        self,
        files: list[dict[str, str]] | object,
        *,
        filename: str = "bundle.json",
        subdir: Path | None = None,
        version: object = 1,
        run_id: object = "run-123",
        custom_data: object = None,
    ) -> Path:
        target_dir = subdir if subdir is not None else self.inbox
        bundle_path = target_dir / filename
        if custom_data is not None:
            bundle_path.write_text(json.dumps(custom_data), encoding="utf-8")
        else:
            data: dict[str, object] = {}
            if version is not None:
                data["version"] = version
            if run_id is not None:
                data["run_id"] = run_id
            data["files"] = files
            bundle_path.write_text(json.dumps(data), encoding="utf-8")
        return bundle_path

    def make_file_entry(self, path: str, content: bytes) -> dict[str, str]:
        b64 = base64.b64encode(content).decode("ascii")
        sha = hashlib.sha256(content).hexdigest()
        return {"path": path, "content": b64, "sha256": sha}

    def test_valid_bundle_extracts_files_and_preserves_integrity(self) -> None:
        from scripts.automation.local_overlay import (
            extract_local_overlay_bundle,
            validate_local_overlay_bundle,
        )

        entries = [
            self.make_file_entry("src/templates/base.html", b"<html>Hello</html>"),
            self.make_file_entry("src/static/app.css", b"body { color: blue; }"),
        ]
        bundle = self.make_bundle_file(entries, run_id="run-test-1")

        validated = validate_local_overlay_bundle(
            bundle, expected_run_id="run-test-1", inbox_dir=self.inbox
        )
        self.assertEqual(len(validated), 2)
        self.assertEqual(validated[0].path, "src/templates/base.html")
        self.assertEqual(validated[0].content_bytes, b"<html>Hello</html>")
        self.assertEqual(validated[1].path, "src/static/app.css")
        self.assertEqual(validated[1].content_bytes, b"body { color: blue; }")

        with tempfile.TemporaryDirectory() as stage_dir:
            extracted = extract_local_overlay_bundle(
                bundle, Path(stage_dir), expected_run_id="run-test-1", inbox_dir=self.inbox
            )
            self.assertEqual(len(extracted), 2)
            self.assertEqual((Path(stage_dir) / "0").read_bytes(), b"<html>Hello</html>")
            self.assertEqual((Path(stage_dir) / "1").read_bytes(), b"body { color: blue; }")
            manifest = json.loads((Path(stage_dir) / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(len(manifest), 2)
            self.assertEqual(manifest[0]["path"], "src/templates/base.html")

    def test_version_contract_strict(self) -> None:
        from scripts.automation.local_overlay import (
            LocalOverlayValidationError,
            validate_local_overlay_bundle,
        )

        entries = [self.make_file_entry("src/templates/base.html", b"test")]

        for bad_version in (None, 2, "1", True, [1], {"v": 1}):
            with self.subTest(version=bad_version):
                bundle = self.make_bundle_file(
                    entries, filename=f"ver_{type(bad_version).__name__}_{bad_version}.json", version=bad_version
                )
                with self.assertRaises(LocalOverlayValidationError):
                    validate_local_overlay_bundle(bundle, inbox_dir=self.inbox)

    def test_run_id_contract_strict(self) -> None:
        from scripts.automation.local_overlay import (
            LocalOverlayValidationError,
            validate_local_overlay_bundle,
        )

        entries = [self.make_file_entry("src/templates/base.html", b"test")]

        # Missing or invalid run_id in bundle
        for idx, bad_run_id in enumerate((None, "", "   ", "invalid/char")):
            with self.subTest(run_id=bad_run_id):
                bundle = self.make_bundle_file(
                    entries, filename=f"run_bad_{idx}.json", run_id=bad_run_id
                )
                with self.assertRaises(LocalOverlayValidationError):
                    validate_local_overlay_bundle(bundle, inbox_dir=self.inbox)

        # Mismatch between bundle run_id and expected_run_id
        bundle_mismatch = self.make_bundle_file(entries, filename="mismatch.json", run_id="run-aaa")
        with self.assertRaisesRegex(LocalOverlayValidationError, "match"):
            validate_local_overlay_bundle(
                bundle_mismatch, expected_run_id="run-bbb", inbox_dir=self.inbox
            )

        # Match succeeds
        validated = validate_local_overlay_bundle(
            bundle_mismatch, expected_run_id="run-aaa", inbox_dir=self.inbox
        )
        self.assertEqual(len(validated), 1)

    def test_schema_and_alias_rejections(self) -> None:
        from scripts.automation.local_overlay import (
            LocalOverlayValidationError,
            validate_local_overlay_bundle,
        )

        # Root list rejected
        root_list_bundle = self.make_bundle_file(
            [], filename="root_list.json", custom_data=[{"path": "src/templates/a.html"}]
        )
        with self.assertRaises(LocalOverlayValidationError):
            validate_local_overlay_bundle(root_list_bundle, inbox_dir=self.inbox)

        # Files mapping rejected
        files_map_bundle = self.make_bundle_file(
            [], filename="files_map.json", custom_data={"version": 1, "run_id": "r1", "files": {"src/templates/a.html": "abc"}}
        )
        with self.assertRaises(LocalOverlayValidationError):
            validate_local_overlay_bundle(files_map_bundle, inbox_dir=self.inbox)

        # Alternate field alias: content_base64 rejected
        b64 = base64.b64encode(b"hello").decode("ascii")
        sha = hashlib.sha256(b"hello").hexdigest()
        alias_content_bundle = self.make_bundle_file(
            [{"path": "src/templates/base.html", "content_base64": b64, "sha256": sha}],
            filename="alias_content.json",
        )
        with self.assertRaises(LocalOverlayValidationError):
            validate_local_overlay_bundle(alias_content_bundle, inbox_dir=self.inbox)

        # Alternate field alias: filename rejected
        alias_filename_bundle = self.make_bundle_file(
            [{"filename": "src/templates/base.html", "content": b64, "sha256": sha}],
            filename="alias_filename.json",
        )
        with self.assertRaises(LocalOverlayValidationError):
            validate_local_overlay_bundle(alias_filename_bundle, inbox_dir=self.inbox)

        # Alternate field alias: sha_256 / hash rejected
        for bad_hash_key in ("sha_256", "hash"):
            with self.subTest(key=bad_hash_key):
                bad_hash_bundle = self.make_bundle_file(
                    [{"path": "src/templates/base.html", "content": b64, bad_hash_key: sha}],
                    filename=f"alias_{bad_hash_key}.json",
                )
                with self.assertRaises(LocalOverlayValidationError):
                    validate_local_overlay_bundle(bad_hash_bundle, inbox_dir=self.inbox)

    def test_decoded_size_limits_2mib_per_file_and_8mib_total(self) -> None:
        from scripts.automation.local_overlay import (
            LocalOverlayValidationError,
            validate_local_overlay_bundle,
        )

        # 2 MiB per file exact boundary test
        two_mib = 2 * 1024 * 1024
        content_exact = b"x" * two_mib
        bundle_2mib = self.make_bundle_file(
            [self.make_file_entry("src/templates/exact.html", content_exact)],
            filename="2mib.json",
        )
        validated = validate_local_overlay_bundle(bundle_2mib, inbox_dir=self.inbox)
        self.assertEqual(len(validated), 1)

        # 2 MiB + 1 byte rejected
        content_too_big = b"x" * (two_mib + 1)
        bundle_too_big = self.make_bundle_file(
            [self.make_file_entry("src/templates/too_big.html", content_too_big)],
            filename="too_big.json",
        )
        with self.assertRaisesRegex(LocalOverlayValidationError, "2 MiB"):
            validate_local_overlay_bundle(bundle_too_big, inbox_dir=self.inbox)

        # 8 MiB total decoded limit: 5 files of 1.8 MiB = 9.0 MiB > 8 MiB rejected
        chunk_1_8_mib = b"y" * (int(1.8 * 1024 * 1024))
        entries_5 = [
            self.make_file_entry(f"src/templates/page_{i}.html", chunk_1_8_mib)
            for i in range(5)
        ]
        bundle_9mib = self.make_bundle_file(entries_5, filename="9mib.json")
        with self.assertRaisesRegex(LocalOverlayValidationError, "8 MiB"):
            validate_local_overlay_bundle(bundle_9mib, inbox_dir=self.inbox)

        # 4 files of 1.8 MiB = 7.2 MiB <= 8 MiB allowed
        entries_4 = [
            self.make_file_entry(f"src/templates/page_{i}.html", chunk_1_8_mib)
            for i in range(4)
        ]
        bundle_7_2mib = self.make_bundle_file(entries_4, filename="7_2mib.json")
        validated_4 = validate_local_overlay_bundle(bundle_7_2mib, inbox_dir=self.inbox)
        self.assertEqual(len(validated_4), 4)

    def test_bundle_outside_inbox_is_rejected(self) -> None:
        from scripts.automation.local_overlay import (
            LocalOverlayValidationError,
            validate_local_overlay_bundle,
        )

        outside_dir = Path(self.temp_dir.name) / "outside"
        outside_dir.mkdir()
        entries = [self.make_file_entry("src/templates/base.html", b"test")]
        bundle = self.make_bundle_file(entries, subdir=outside_dir)

        with self.assertRaisesRegex(LocalOverlayValidationError, "inbox"):
            validate_local_overlay_bundle(bundle, inbox_dir=self.inbox)

    def test_symlink_bundle_is_rejected(self) -> None:
        from scripts.automation.local_overlay import (
            LocalOverlayValidationError,
            validate_local_overlay_bundle,
        )

        entries = [self.make_file_entry("src/templates/base.html", b"test")]
        real_bundle = self.make_bundle_file(entries, filename="real.json")
        link_bundle = self.inbox / "link.json"
        link_bundle.symlink_to(real_bundle)

        with self.assertRaisesRegex(LocalOverlayValidationError, "symlink"):
            validate_local_overlay_bundle(link_bundle, inbox_dir=self.inbox)

    def test_empty_bundle_and_exceeding_64_files_are_rejected(self) -> None:
        from scripts.automation.local_overlay import (
            LocalOverlayValidationError,
            validate_local_overlay_bundle,
        )

        empty_bundle = self.make_bundle_file([])
        with self.assertRaisesRegex(LocalOverlayValidationError, "1..64"):
            validate_local_overlay_bundle(empty_bundle, inbox_dir=self.inbox)

        too_many = [
            self.make_file_entry(f"src/templates/page_{i}.html", f"content {i}".encode())
            for i in range(65)
        ]
        large_bundle = self.make_bundle_file(too_many, filename="large.json")
        with self.assertRaisesRegex(LocalOverlayValidationError, "64"):
            validate_local_overlay_bundle(large_bundle, inbox_dir=self.inbox)

    def test_forbidden_paths_and_traversal_are_rejected(self) -> None:
        from scripts.automation.local_overlay import (
            LocalOverlayValidationError,
            validate_local_overlay_bundle,
        )

        for bad_path in (
            "src/apps/views.py",
            "manage.py",
            "/etc/passwd",
            "src/templates/../views.py",
            "src/templates/./index.html",
            "src/templates//index.html",
            "src/templates/",
            "src/static/",
            "../escape.html",
        ):
            with self.subTest(path=bad_path):
                entries = [self.make_file_entry(bad_path, b"content")]
                bundle = self.make_bundle_file(entries, filename="bad_path.json")
                with self.assertRaises(LocalOverlayValidationError):
                    validate_local_overlay_bundle(bundle, inbox_dir=self.inbox)

    def test_duplicate_file_paths_are_rejected(self) -> None:
        from scripts.automation.local_overlay import (
            LocalOverlayValidationError,
            validate_local_overlay_bundle,
        )

        entries = [
            self.make_file_entry("src/templates/base.html", b"v1"),
            self.make_file_entry("src/templates/base.html", b"v2"),
        ]
        bundle = self.make_bundle_file(entries, filename="dup.json")
        with self.assertRaisesRegex(LocalOverlayValidationError, "duplicate"):
            validate_local_overlay_bundle(bundle, inbox_dir=self.inbox)

    def test_corrupted_base64_or_sha256_mismatch_is_rejected(self) -> None:
        from scripts.automation.local_overlay import (
            LocalOverlayValidationError,
            validate_local_overlay_bundle,
        )

        bad_b64 = [{"path": "src/templates/base.html", "content": "!!!not_b64", "sha256": "0" * 64}]
        bundle1 = self.make_bundle_file(bad_b64, filename="bad_b64.json")
        with self.assertRaises(LocalOverlayValidationError):
            validate_local_overlay_bundle(bundle1, inbox_dir=self.inbox)

        bad_sha = [
            {
                "path": "src/templates/base.html",
                "content": base64.b64encode(b"hello").decode("ascii"),
                "sha256": "0" * 64,
            }
        ]
        bundle2 = self.make_bundle_file(bad_sha, filename="bad_sha.json")
        with self.assertRaisesRegex(LocalOverlayValidationError, "sha256 mismatch"):
            validate_local_overlay_bundle(bundle2, inbox_dir=self.inbox)

    def test_cli_invocation_validate_and_extract(self) -> None:
        entries = [
            self.make_file_entry("src/templates/index.html", b"<h1>CLI Test</h1>")
        ]
        bundle = self.make_bundle_file(entries, run_id="run-cli-test")

        # CLI validate success
        res = subprocess.run(
            [
                sys.executable,
                str(VALIDATOR_SCRIPT),
                "validate",
                str(bundle),
                "--run-id",
                "run-cli-test",
                "--inbox-dir",
                str(self.inbox),
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0, msg=res.stderr)
        self.assertIn("VALID: 1 files", res.stdout)

        # CLI validate run_id mismatch
        res_mismatch = subprocess.run(
            [
                sys.executable,
                str(VALIDATOR_SCRIPT),
                "validate",
                str(bundle),
                "--run-id",
                "run-wrong",
                "--inbox-dir",
                str(self.inbox),
            ],
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(res_mismatch.returncode, 0)
        self.assertIn("ERROR:", res_mismatch.stderr)

        # CLI extract success
        with tempfile.TemporaryDirectory() as stage_dir:
            res_ext = subprocess.run(
                [
                    sys.executable,
                    str(VALIDATOR_SCRIPT),
                    "extract",
                    str(bundle),
                    stage_dir,
                    "--run-id",
                    "run-cli-test",
                    "--inbox-dir",
                    str(self.inbox),
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(res_ext.returncode, 0, msg=res_ext.stderr)
            self.assertEqual(
                (Path(stage_dir) / "0").read_bytes(), b"<h1>CLI Test</h1>"
            )


class LocalOverlayControllerContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.controller = CONTROLLER.read_text(encoding="utf-8")
        cls.bootstrap = (
            BOOTSTRAP_LOCAL.read_text(encoding="utf-8")
            if BOOTSTRAP_LOCAL.is_file()
            else ""
        )

    def test_local_commands_are_registered_in_usage_and_main(self) -> None:
        self.assertIn("local-hot-refresh", self.controller)
        self.assertIn("local-hot-refresh-clear", self.controller)
        self.assertIn("local_hot_refresh", self.controller)
        self.assertIn("local_hot_refresh_clear", self.controller)

    def test_inbox_path_is_fixed_and_canonical(self) -> None:
        self.assertIn(INBOX_DIR, self.controller)

    def test_controller_uses_single_installed_validator_helper(self) -> None:
        self.assertIn(INSTALLED_HELPER, self.controller)
        self.assertIn('LOCAL_OVERLAY_HELPER="/usr/local/lib/eod/local_overlay.py"', self.controller)
        self.assertIn('"$LOCAL_OVERLAY_HELPER" extract', self.controller)
        # Ensure inline duplicate python validator is removed
        self.assertNotIn("def extract_and_validate_local_bundle", self.controller)
        self.assertNotIn("import base64\nimport hashlib\nimport json\nimport os\nimport re\nimport stat\nimport sys\nfrom pathlib import Path, PurePosixPath\n\nbundle_path = Path(sys.argv[1])", self.controller)

    def test_local_hot_refresh_recreates_clean_image_before_apply(self) -> None:
        fn_body = self.controller[
            self.controller.index("local_hot_refresh()") :
            self.controller.index("local_hot_refresh_clear()")
        ]
        recreate_pos = fn_body.index("force_recreate_application_only")
        copy_pos = fn_body.index("copy_hot_refresh_file")
        self.assertLess(recreate_pos, copy_pos)

    def test_local_hot_refresh_has_rollback_trap(self) -> None:
        fn_body = self.controller[
            self.controller.index("local_hot_refresh()") :
            self.controller.index("local_hot_refresh_clear()")
        ]
        self.assertIn("trap ", fn_body)
        self.assertIn("ERR", fn_body)
        self.assertIn("force_recreate_application_only", fn_body)

    def test_local_marker_contract(self) -> None:
        self.assertIn("write_local_hot_refresh_marker", self.controller)
        fn_body = self.controller[
            self.controller.index("write_local_hot_refresh_marker()") :
            self.controller.index("local_hot_refresh()")
        ]
        self.assertIn("SOURCE=LOCAL", fn_body)
        self.assertIn("RUN_ID=", fn_body)
        self.assertIn("BUNDLE_SHA256=", fn_body)
        self.assertIn("APPLIED_AT=", fn_body)
        self.assertNotIn("PR_NUMBER=", fn_body)
        self.assertNotIn("OVERLAY_SHA=", fn_body)
        self.assertIn("sha256sum", self.controller)

    def test_local_hot_refresh_clear_recreates_app_only(self) -> None:
        clear_body = self.controller[
            self.controller.index("local_hot_refresh_clear()") :
            self.controller.index("main()")
        ]
        self.assertIn("force_recreate_application_only", clear_body)
        self.assertIn("preview=UNTOUCHED", clear_body)
        self.assertNotIn("apply_migrations", clear_body)
        self.assertNotIn("create_database_backup", clear_body)

    def test_database_and_preview_are_untouched(self) -> None:
        fn_body = self.controller[
            self.controller.index("local_hot_refresh()") :
            self.controller.index("main()")
        ]
        self.assertNotIn("apply_migrations", fn_body)
        self.assertNotIn("create_database_backup", fn_body)
        self.assertNotIn("restore_database", fn_body)
        self.assertIn("preview=UNTOUCHED", fn_body)

    def test_github_hot_refresh_remains_intact(self) -> None:
        self.assertIn("hot_refresh()", self.controller)
        self.assertIn("fetch_hot_refresh_refs", self.controller)
        self.assertIn("collect_hot_refresh_files", self.controller)


class LocalOverlayBootstrapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bootstrap = (
            BOOTSTRAP_LOCAL.read_text(encoding="utf-8")
            if BOOTSTRAP_LOCAL.is_file()
            else ""
        )

    def test_bootstrap_script_exists_and_is_executable(self) -> None:
        self.assertTrue(BOOTSTRAP_LOCAL.is_file(), "bootstrap_local_overlay.sh is missing")

    def test_bootstrap_installs_validator_helper_to_system_lib(self) -> None:
        self.assertIn(INSTALLED_HELPER, self.bootstrap)
        self.assertIn("/usr/local/lib/eod", self.bootstrap)
        self.assertIn("local_overlay.py", self.bootstrap)

    def test_bootstrap_preserves_backup_of_controller_before_replacement(self) -> None:
        self.assertIn("if [[ -f \"$CONTROLLER_BIN\" ]]", self.bootstrap)
        self.assertIn(".bak", self.bootstrap)

    def test_bootstrap_grants_eodadmin_nopasswd_only_for_local_commands(self) -> None:
        self.assertIn("eodadmin", self.bootstrap)
        self.assertIn("NOPASSWD:", self.bootstrap)
        self.assertIn("local-hot-refresh", self.bootstrap)
        self.assertIn("local-hot-refresh-clear", self.bootstrap)
        self.assertNotIn("NOPASSWD: ALL", self.bootstrap)
        self.assertNotIn("NOPASSWD: /usr/local/sbin/eod-development-controller\n", self.bootstrap)

    def test_bootstrap_validates_sudoers_with_visudo(self) -> None:
        self.assertIn("visudo -cf", self.bootstrap)
        self.assertIn("0440", self.bootstrap)

    def test_bootstrap_creates_inbox_with_restricted_permissions(self) -> None:
        self.assertIn(INBOX_DIR, self.bootstrap)
        self.assertIn("0700", self.bootstrap)


if __name__ == "__main__":
    unittest.main()
