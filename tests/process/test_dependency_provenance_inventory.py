from __future__ import annotations

import json
import subprocess
import tempfile
import tomllib
import unittest
from pathlib import Path

from scripts.dependency_provenance_inventory import (
    ROOT,
    TrackedFile,
    build_inventory,
    discover_executable_sources,
    scan_actions,
    scan_images,
    scan_operations,
    tracked_file_records,
)
from scripts.dependency_provenance_views import validation_errors

FIXTURES = (
    ROOT
    / "tests/process/fixtures/dependency_provenance_negative_cases.json"
)


class DependencyProvenanceInventoryTests(unittest.TestCase):
    def init_repo(self, root: Path) -> None:
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)

    def track_all(self, root: Path) -> None:
        subprocess.run(["git", "add", "."], cwd=root, check=True)

    def write_minimal_pyproject(self, root: Path) -> None:
        (root / "pyproject.toml").write_text(
            "[build-system]\n"
            'requires = ["setuptools>=75"]\n'
            'build-backend = "setuptools.build_meta"\n\n'
            "[project]\n"
            'name = "fixture"\n'
            'version = "0.0.0"\n'
            'requires-python = ">=3.13,<3.14"\n'
            "dependencies = []\n",
            encoding="utf-8",
        )

    def test_current_repository_contours_are_fact_based(self) -> None:
        inventory = build_inventory(ROOT)
        contours = inventory["contours"]
        totals = inventory["totals"]

        self.assertTrue(contours["python"]["pyproject_present"])
        self.assertEqual(
            contours["python"]["accepted_profiles"],
            ["tooling", "build", "runtime", "dev", "browser"],
        )
        self.assertFalse(
            contours["javascript"]["separate_frontend_dependency_contour"]
        )
        self.assertEqual(contours["javascript"]["package_or_lock_files"], [])
        self.assertGreater(totals["floating_inputs"], 0)
        self.assertGreater(totals["inventory_entries"], 0)
        self.assertGreater(totals["applicable_executable_sources"], 0)
        self.assertEqual(
            contours["github_actions"]["temporary_workflow_files"],
            [],
        )
        self.assertTrue(
            contours["external_downloads"]["local_runtime_probes_excluded"]
        )
        self.assertEqual(
            contours["executable_sources"]["uncovered_paths"],
            [],
        )
        self.assertTrue(
            all(
                item["path"] and item["rationale"]
                for item in contours["executable_sources"]["exact_exclusions"]
            )
        )

    def test_mutable_action_tag_is_not_immutable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / ".github/workflows/test.yml"
            path.parent.mkdir(parents=True)
            path.write_text(
                "steps:\n  - uses: actions/checkout@v6\n",
                encoding="utf-8",
            )
            entries = scan_actions(root, [".github/workflows/test.yml"])

        self.assertEqual(len(entries), 1)
        self.assertFalse(entries[0]["immutable"])
        self.assertEqual(
            entries[0]["current_reproducibility"],
            "mutable-tag-or-branch",
        )

    def test_full_action_commit_sha_is_immutable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / ".github/workflows/test.yml"
            path.parent.mkdir(parents=True)
            path.write_text(
                "steps:\n"
                "  - uses: actions/checkout@"
                "d23441a48e516b6c34aea4fa41551a30e30af803 # v6\n",
                encoding="utf-8",
            )
            entries = scan_actions(root, [".github/workflows/test.yml"])

        self.assertEqual(len(entries), 1)
        self.assertTrue(entries[0]["immutable"])
        self.assertEqual(entries[0]["hash_coverage"], "commit-sha")
        self.assertEqual(entries[0]["evidence"], "v6")

    def test_image_classification_requires_local_build_evidence(self) -> None:
        digest = "a" * 64
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            compose = root / "compose.test.yaml"
            compose.write_text(
                "services:\n"
                "  tagless_external:\n"
                "    image: postgres\n"
                "  tagged_external:\n"
                "    image: postgres:18.4-bookworm\n"
                "  immutable_external:\n"
                f"    image: postgres@sha256:{digest}\n"
                "  local:\n"
                "    image: eod-development-app\n"
                "    build:\n"
                "      context: .\n"
                "  same_name_without_build:\n"
                "    image: eod-development-app\n",
                encoding="utf-8",
            )
            entries = scan_images(root, ["compose.test.yaml"])

        self.assertEqual(len(entries), 5)
        by_line = {item["line"]: item for item in entries}
        self.assertEqual(by_line[3]["class"], "container-image")
        self.assertFalse(by_line[3]["immutable"])
        self.assertEqual(by_line[5]["class"], "container-image")
        self.assertFalse(by_line[5]["immutable"])
        self.assertEqual(by_line[7]["class"], "container-image")
        self.assertTrue(by_line[7]["immutable"])
        local_name_entries = [
            item
            for item in entries
            if item["declaration"] == "eod-development-app"
        ]
        self.assertEqual(
            sorted(item["class"] for item in local_name_entries),
            ["container-image", "container-output"],
        )
        local_output = next(
            item
            for item in local_name_entries
            if item["class"] == "container-output"
        )
        inherited_name = next(
            item
            for item in local_name_entries
            if item["class"] == "container-image"
        )
        self.assertIn("tracked build", local_output["evidence"])
        self.assertFalse(inherited_name["immutable"])

    def test_repository_wide_operation_discovery(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.init_repo(root)
            self.write_minimal_pyproject(root)
            deploy = root / "deploy/automation/bootstrap.sh"
            outside = root / "operator/install.bash"
            probe = root / "ops/health.sh"
            deploy.parent.mkdir(parents=True)
            outside.parent.mkdir(parents=True)
            probe.parent.mkdir(parents=True)
            deploy.write_text(
                "python -m pip install bootstrap-tool\n"
                "curl --fail https://downloads.example.test/tool.bin\n",
                encoding="utf-8",
            )
            outside.write_text(
                "apt-get install -y ca-certificates\n",
                encoding="utf-8",
            )
            probe.write_text(
                "curl --fail http://127.0.0.1:8000/_health/\n",
                encoding="utf-8",
            )
            self.track_all(root)
            records = tracked_file_records(root)
            paths = [item.path for item in records]
            sources = discover_executable_sources(root, records)
            entries = scan_operations(root, paths, sources)

        source_paths = {item.path for item in sources}
        self.assertIn("deploy/automation/bootstrap.sh", source_paths)
        self.assertIn("operator/install.bash", source_paths)
        self.assertIn("ops/health.sh", source_paths)
        evidence = {(item["class"], item["path"]) for item in entries}
        self.assertIn(
            ("python-install", "deploy/automation/bootstrap.sh"),
            evidence,
        )
        self.assertIn(
            ("external-download", "deploy/automation/bootstrap.sh"),
            evidence,
        )
        self.assertIn(
            ("system-package-install", "operator/install.bash"),
            evidence,
        )
        self.assertNotIn(
            ("external-download", "ops/health.sh"),
            evidence,
        )

    def test_new_applicable_path_is_digested_by_inventory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.init_repo(root)
            self.write_minimal_pyproject(root)
            script = root / "future/location/operator.sh"
            script.parent.mkdir(parents=True)
            script.write_text("echo inventory-completeness\n", encoding="utf-8")
            self.track_all(root)
            inventory = build_inventory(root)

        executable = inventory["contours"]["executable_sources"]
        self.assertIn("future/location/operator.sh", executable["applicable_paths"])
        self.assertIn("future/location/operator.sh", inventory["source_digests"])
        self.assertEqual(executable["uncovered_paths"], [])

    def test_python_subprocess_install_is_discovered_outside_scripts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "tools/bootstrap.py"
            path.parent.mkdir(parents=True)
            path.write_text(
                "import subprocess\n"
                "subprocess.run(\n"
                "    [\"python\", \"-m\", \"pip\", \"install\", \"demo\"],\n"
                "    check=True,\n"
                ")\n",
                encoding="utf-8",
            )
            records = [TrackedFile("tools/bootstrap.py")]
            sources = discover_executable_sources(root, records)
            entries = scan_operations(root, ["tools/bootstrap.py"], sources)

        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["class"], "python-install")
        self.assertEqual(entries[0]["path"], "tools/bootstrap.py")

    def test_spdx_future_negative_fixtures_are_named(self) -> None:
        payload = json.loads(FIXTURES.read_text(encoding="utf-8"))
        cases = {item["id"]: item for item in payload["cases"]}
        expected = {
            "DP-SPDX-001": "spdx-creation-info-created-required",
            "DP-SPDX-002": "spdx-created-build-epoch",
            "DP-SPDX-003": "spdx-created-rfc3339-utc",
            "DP-SPDX-004": "spdx-document-namespace-deterministic",
            "DP-SPDX-005": "spdx-document-namespace-unique-subject",
            "DP-SPDX-006": "spdx-schema-valid",
        }
        self.assertEqual(
            {case_id: cases[case_id]["expected_rule"] for case_id in expected},
            expected,
        )
        self.assertTrue(
            all(
                cases[case_id]["stage"] == "NEXT-IMPLEMENTATION"
                for case_id in expected
            )
        )

    def test_scanner_has_no_file_wide_ruff_exemption(self) -> None:
        pyproject = tomllib.loads(
            (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        )
        ignores = pyproject["tool"]["ruff"]["lint"].get("per-file-ignores", {})
        self.assertNotIn("scripts/dependency_provenance_inventory.py", ignores)

    def test_generated_inventory_views_are_exact(self) -> None:
        self.assertEqual(validation_errors(ROOT), [])


if __name__ == "__main__":
    unittest.main()
