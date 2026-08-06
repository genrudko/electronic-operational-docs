from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.dependency_provenance_inventory import (
    ROOT,
    build_inventory,
    scan_actions,
    scan_images,
    scan_operations,
)
from scripts.dependency_provenance_views import validation_errors


class DependencyProvenanceInventoryTests(unittest.TestCase):
    def test_current_repository_contours_are_fact_based(self) -> None:
        inventory = build_inventory(ROOT)
        contours = inventory["contours"]
        totals = inventory["totals"]

        self.assertTrue(contours["python"]["pyproject_present"])
        self.assertFalse(contours["javascript"]["separate_frontend_dependency_contour"])
        self.assertEqual(contours["javascript"]["package_or_lock_files"], [])
        self.assertGreater(totals["floating_inputs"], 0)
        self.assertGreater(totals["inventory_entries"], 0)
        self.assertEqual(contours["github_actions"]["temporary_workflow_files"], [])
        self.assertEqual(
            contours["external_downloads"]["download_operation_count"], 0
        )
        self.assertTrue(
            contours["external_downloads"]["local_runtime_probes_excluded"]
        )
        self.assertEqual(totals["by_class"].get("container-output"), 1)

    def test_mutable_action_tag_is_not_immutable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / ".github/workflows/test.yml"
            path.parent.mkdir(parents=True)
            path.write_text("steps:\n  - uses: actions/checkout@v6\n", encoding="utf-8")
            entries = scan_actions(root, [".github/workflows/test.yml"])

        self.assertEqual(len(entries), 1)
        self.assertFalse(entries[0]["immutable"])
        self.assertEqual(entries[0]["current_reproducibility"], "mutable-tag-or-branch")

    def test_full_action_commit_sha_is_immutable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / ".github/workflows/test.yml"
            path.parent.mkdir(parents=True)
            path.write_text(
                "steps:\n  - uses: actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803 # v6\n",
                encoding="utf-8",
            )
            entries = scan_actions(root, [".github/workflows/test.yml"])

        self.assertEqual(len(entries), 1)
        self.assertTrue(entries[0]["immutable"])
        self.assertEqual(entries[0]["hash_coverage"], "commit-sha")
        self.assertEqual(entries[0]["evidence"], "v6")

    def test_image_tag_digest_and_local_output_are_distinguished(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dockerfile = root / "Dockerfile"
            compose = root / "compose.test.yaml"
            dockerfile.write_text("FROM python:3.13-slim-bookworm\n", encoding="utf-8")
            compose.write_text(
                "services:\n"
                "  db:\n"
                "    image: postgres:18.4-bookworm@sha256:"
                + "a" * 64
                + "\n"
                "  app:\n"
                "    image: eod-development-app\n",
                encoding="utf-8",
            )
            entries = scan_images(root, ["Dockerfile", "compose.test.yaml"])

        self.assertEqual(len(entries), 3)
        by_declaration = {item["declaration"]: item for item in entries}
        self.assertFalse(by_declaration["python:3.13-slim-bookworm"]["immutable"])
        self.assertTrue(
            by_declaration[
                "postgres:18.4-bookworm@sha256:" + "a" * 64
            ]["immutable"]
        )
        self.assertEqual(
            by_declaration["eod-development-app"]["class"], "container-output"
        )

    def test_local_health_probe_is_not_external_download(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            script = root / "scripts/check.sh"
            script.parent.mkdir(parents=True)
            script.write_text(
                "curl --fail \\\n"
                "  http://127.0.0.1:8000/_health/\n"
                "curl --fail https://downloads.example.test/tool.bin\n",
                encoding="utf-8",
            )
            entries = scan_operations(root, ["scripts/check.sh"])

        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["class"], "external-download")
        self.assertIn("downloads.example.test", entries[0]["declaration"])

    def test_generated_inventory_views_are_exact(self) -> None:
        self.assertEqual(validation_errors(ROOT), [])


if __name__ == "__main__":
    unittest.main()
