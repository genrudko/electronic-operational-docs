from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import dependency_provenance_contract as contract
from scripts import dependency_provenance_fixture_gates as fixture_gates
from scripts import secret_hygiene

ROOT = Path(__file__).resolve().parents[2]
FIXTURE_PATH = (
    ROOT
    / "tests/process/fixtures/dependency_provenance_contract_cases.json"
)
REGISTRY_PATH = ROOT / "supply-chain/registry.json"
WORKFLOW_PATH = ROOT / ".github/workflows/dependency-provenance.yml"
HASH = "a" * 64
OTHER_HASH = "b" * 64
COMMIT = "c" * 40
OTHER_COMMIT = "d" * 40
IMAGE_DIGEST = f"sha256:{HASH}"
OTHER_IMAGE_DIGEST = f"sha256:{OTHER_HASH}"
BUILD_DIGEST = f"sha256:{'e' * 64}"
EPOCH = "1700000000"


def registry() -> dict[str, object]:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def record(name: str, version: str = "1.0") -> contract.LockRecord:
    return contract.LockRecord(name, version, (HASH,))


def minimal_spdx(
    *,
    image_digest: str = IMAGE_DIGEST,
    source_commit: str = COMMIT,
    build_digest: str = BUILD_DIGEST,
    created: str | None = None,
    namespace: str | None = None,
    packages: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "spdxVersion": "SPDX-2.3",
        "dataLicense": "CC0-1.0",
        "SPDXID": "SPDXRef-DOCUMENT",
        "name": "fixture",
        "documentNamespace": namespace
        or contract.canonical_namespace(image_digest, source_commit, build_digest),
        "creationInfo": {
            "created": created or contract.epoch_timestamp(EPOCH),
            "creators": ["Tool: fixture"],
        },
        "packages": packages
        or [
            {
                "SPDXID": "SPDXRef-FinalImage",
                "name": "fixture-image",
                "downloadLocation": "NOASSERTION",
                "filesAnalyzed": False,
                "versionInfo": image_digest,
            }
        ],
        "documentDescribes": ["SPDXRef-FinalImage"],
        "relationships": [],
    }
    return payload


def provenance_payload(
    *,
    subject_digest: str = IMAGE_DIGEST,
    source_commit: str = COMMIT,
    include_source: bool = True,
    include_required: bool = True,
    statement_type: str = "https://in-toto.io/Statement/v1",
) -> dict[str, object]:
    materials: list[dict[str, object]] = []
    if include_required:
        required = [
            "supply-chain/registry.json",
            ".github/workflows/dependency-provenance.yml",
            "Dockerfile",
            *[
                f"requirements/locks/{profile}.txt"
                for profile in contract.LOCK_PROFILES
            ],
        ]
        materials.extend(
            {"uri": uri, "digest": {"sha256": HASH}} for uri in required
        )
    if include_source:
        materials.append(
            {
                "uri": (
                    "git+https://github.com/genrudko/"
                    f"electronic-operational-docs@{source_commit}"
                ),
                "digest": {"sha1": source_commit},
            }
        )
    return {
        "_type": statement_type,
        "subject": [
            {
                "name": "fixture",
                "digest": {"sha256": subject_digest.split(":", 1)[1]},
            }
        ],
        "predicateType": "https://slsa.dev/provenance/v1",
        "predicate": {
            "buildDefinition": {"resolvedDependencies": materials},
        },
    }


class DependencyProvenanceContractFixtureTests(unittest.TestCase):
    maxDiff = None

    def assert_rule(self, expected: str, function, *args, **kwargs) -> None:
        with self.assertRaises(contract.ContractViolation) as context:
            function(*args, **kwargs)
        self.assertEqual(context.exception.rule, expected)

    def temporary_lock(self, text: str) -> Path:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "fixture.txt"
        path.write_text(text, encoding="utf-8")
        return path

    def action_fixture(
        self,
        reference: str,
        comment: str,
        action_registry: dict[str, object],
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / ".github/workflows/fixture.yml"
            path.parent.mkdir(parents=True)
            path.write_text(
                f"steps:\n  - uses: {reference} # {comment}\n",
                encoding="utf-8",
            )
            with (
                mock.patch.object(contract, "ROOT", root),
                mock.patch.object(
                    contract,
                    "tracked_paths",
                    return_value=[".github/workflows/fixture.yml"],
                ),
            ):
                contract.validate_actions({"github_actions": action_registry})

    def trigger(self, rule: str) -> None:
        current_registry = registry()
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

        if rule == "python-canonical-declaration":
            contract.requirement_name("???")
        elif rule == "declaration-lock-drift":
            locks = {
                profile: {} for profile in contract.LOCK_PROFILES
            }
            with mock.patch.object(
                contract,
                "direct_intent",
                return_value={
                    "build": set(),
                    "runtime": {"missing"},
                    "dev": {"missing"},
                    "browser": {"missing"},
                },
            ):
                contract.validate_lock_intent(current_registry, locks)
        elif rule == "lock-integrity-hashes":
            contract.parse_lock(self.temporary_lock("demo==1.0\n"))
        elif rule == "exact-generated-lock":
            contract.parse_lock(
                self.temporary_lock(
                    f"demo==1.0 --hash=sha256:{HASH}\n"
                    f"demo==1.0 --hash=sha256:{HASH}\n"
                )
            )
        elif rule == "version-lock-hash-coherence":
            locks = {
                profile: {} for profile in contract.LOCK_PROFILES
            }
            locks["runtime"] = {"django": record("django", "0.0")}
            locks["dev"] = dict(locks["runtime"])
            locks["browser"] = {
                **locks["runtime"],
                "playwright": record(
                    "playwright",
                    current_registry["browser"]["package"]["version"],
                ),
            }
            with mock.patch.object(
                contract,
                "direct_intent",
                return_value={
                    "build": set(),
                    "runtime": set(),
                    "dev": set(),
                    "browser": set(),
                },
            ):
                contract.validate_lock_intent(current_registry, locks)
        elif rule == "deterministic-lock-header":
            contract.parse_lock(
                self.temporary_lock(
                    "# generated 2026-08-06\n"
                    f"demo==1.0 --hash=sha256:{HASH}\n"
                )
            )
        elif rule == "platform-profile-coherence":
            candidate = json.loads(json.dumps(current_registry))
            candidate["python"]["platform"] = "unexpected"
            contract.validate_registry(candidate)
        elif rule == "clean-hashed-install":
            fixture_gates.validate_clean_install_workflow(
                workflow.replace(" --without-pip", "")
            )
        elif rule == "locked-build-environment":
            fixture_gates.validate_build_workflow(
                workflow.replace(" --no-isolation", "")
            )
        elif rule == "locked-runtime-install":
            fixture_gates.validate_runtime_install_workflow(
                workflow.replace(" --no-deps", "")
            )
        elif rule == "immutable-image-digest":
            contract.validate_image_reference(
                "postgres:18.4-bookworm", "fixture", current_registry
            )
        elif rule == "immutable-action-sha":
            self.action_fixture(
                "actions/checkout@deadbeef",
                "v6.1.0",
                current_registry["github_actions"],
            )
        elif rule == "immutable-reusable-workflow":
            fixture_gates.validate_reusable_workflow_reference(
                "owner/repository/.github/workflows/reuse.yml@main"
            )
        elif rule == "action-version-metadata":
            self.action_fixture(
                "actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803",
                "wrong",
                current_registry["github_actions"],
            )
        elif rule == "image-digest-metadata-coherence":
            fake = {
                "external_images": {
                    "postgres": {
                        "digest": IMAGE_DIGEST,
                        "repository": "postgres",
                        "tag": "postgres:18.4-bookworm",
                    }
                }
            }
            contract.validate_image_reference(
                f"other@{IMAGE_DIGEST}", "fixture", fake
            )
        elif rule == "single-image-owner":
            contract.validate_image_reference(
                f"postgres@{OTHER_IMAGE_DIGEST}", "fixture", current_registry
            )
        elif rule == "single-action-owner":
            self.action_fixture(
                f"unknown/action@{'f' * 40}",
                "v1.0.0",
                current_registry["github_actions"],
            )
        elif rule == "external-download-integrity":
            contract.validate_one_command(
                "fixture.sh", 1, "curl https://example.test/tool.bin"
            )
        elif rule == "no-pipe-to-interpreter":
            contract.validate_one_command(
                "fixture.sh", 1, "curl https://example.test/tool.sh | sh"
            )
        elif rule == "external-asset-integrity":
            candidate = json.loads(json.dumps(current_registry))
            candidate["external_assets"]["onest_variable_woff2"]["sha256"] = HASH
            contract.validate_registry(candidate)
        elif rule == "javascript-contour-owner":
            fixture_gates.validate_javascript_contour(["ui/package.json"])
        elif rule == "browser-binary-provenance":
            candidate = json.loads(json.dumps(current_registry))
            candidate["browser"]["package"]["version"] = "0.0"
            contract.validate_registry(candidate)
        elif rule == "static-manifest-exact":
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory) / "staticfiles"
                root.mkdir()
                asset = root / "asset.css"
                asset.write_text("a", encoding="utf-8")
                manifest = Path(directory) / "manifest.json"
                contract.generate_static_manifest(root, manifest)
                asset.write_text("b", encoding="utf-8")
                contract.verify_static_manifest(root, manifest)
        elif rule == "spdx-schema-valid":
            contract.validate_spdx_schema({"spdxVersion": "SPDX-2.3"})
        elif rule == "sbom-runtime-completeness":
            payload = minimal_spdx()
            locks = {
                profile: {} for profile in contract.LOCK_PROFILES
            }
            locks["runtime"] = {"django": record("django")}
            with (
                mock.patch.object(contract, "load_locks", return_value=locks),
                mock.patch.object(contract, "validate_spdx_schema"),
            ):
                contract.validate_spdx(
                    payload,
                    IMAGE_DIGEST,
                    COMMIT,
                    BUILD_DIGEST,
                    EPOCH,
                    "runtime",
                )
        elif rule == "sbom-scope-separation":
            packages = [
                minimal_spdx()["packages"][0],
                {
                    "SPDXID": "SPDXRef-Ruff",
                    "name": "ruff",
                    "downloadLocation": "NOASSERTION",
                    "filesAnalyzed": False,
                    "externalRefs": [
                        {
                            "referenceCategory": "PACKAGE-MANAGER",
                            "referenceType": "purl",
                            "referenceLocator": "pkg:pypi/ruff@0.0",
                        }
                    ],
                },
            ]
            payload = minimal_spdx(packages=packages)
            locks = {
                profile: {} for profile in contract.LOCK_PROFILES
            }
            locks["dev"] = {"ruff": record("ruff")}
            with (
                mock.patch.object(contract, "load_locks", return_value=locks),
                mock.patch.object(contract, "validate_spdx_schema"),
            ):
                contract.validate_spdx(
                    payload,
                    IMAGE_DIGEST,
                    COMMIT,
                    BUILD_DIGEST,
                    EPOCH,
                    "runtime",
                )
        elif rule == "sbom-service-boundary":
            fixture_gates.validate_service_boundary(
                {
                    "components": [
                        {"role": "production"},
                        {"role": "browser-test"},
                    ]
                }
            )
        elif rule == "sbom-exact-head-chain":
            with tempfile.TemporaryDirectory() as directory:
                source = Path(directory) / "source.json"
                source.write_text("{}\n", encoding="utf-8")
                contract.normalize_spdx(
                    source,
                    Path(directory) / "output.json",
                    IMAGE_DIGEST,
                    "not-a-commit",
                    BUILD_DIGEST,
                    EPOCH,
                )
        elif rule == "provenance-exact-head":
            contract.validate_provenance(
                provenance_payload(source_commit=OTHER_COMMIT),
                IMAGE_DIGEST,
                COMMIT,
            )
        elif rule == "provenance-subject-digest":
            contract.validate_provenance(
                provenance_payload(subject_digest=OTHER_IMAGE_DIGEST),
                IMAGE_DIGEST,
                COMMIT,
            )
        elif rule == "provenance-material-completeness":
            contract.validate_provenance(
                provenance_payload(include_required=False),
                IMAGE_DIGEST,
                COMMIT,
            )
        elif rule == "single-final-exact-head-evidence":
            fixture_gates.validate_exact_head_workflow(
                workflow.replace("SOURCE_COMMIT", "SOURCE_REVISION")
            )
        elif rule == "secret-scan-before-publication":
            fixture_gates.validate_publication_order_workflow(
                "Upload verified exact-head evidence\n"
                "Verify wheel and evidence are credential-free before publication\n"
                "Build and verify artifact-content manifest\n"
            )
        elif rule == "artifact-secret-free":
            fixture_gates.validate_artifact_text(
                "artifact.json",
                "postgresql://operator:password@example.test/database",
            )
        elif rule == "verified-sanitized-artifact-only":
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                for name in (
                    "static-manifest.json",
                    "production.spdx.json",
                    "browser.spdx.json",
                    "postgres.spdx.json",
                    "component-set.json",
                    "provenance.intoto.json",
                ):
                    (root / name).write_text("{}\n", encoding="utf-8")
                (root / "publication-order.json").write_text(
                    json.dumps(
                        {
                            "completed": [
                                "secret-hygiene",
                                "publication-ready",
                            ]
                        }
                    ),
                    encoding="utf-8",
                )
                (root / "artifact-manifest.json").write_text(
                    '{"files": {}}\n', encoding="utf-8"
                )
                contract.verify_artifact_directory(root)
        elif rule == "malformed-truncated-lock-fixture":
            fixture_gates.validate_malformed_lock_fixture(
                self.temporary_lock("demo==1.0 \\\n")
            )
        elif rule == "clean-tree-residue":
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                subprocess.run(["git", "init", "-q"], cwd=root, check=True)
                (root / "residue.txt").write_text("x", encoding="utf-8")
                residue = secret_hygiene.clean_tree_residue(root)
                if residue:
                    raise contract.ContractViolation(
                        "clean-tree-residue", repr(residue)
                    )
        elif rule == "attestation-verification":
            contract.validate_provenance(
                provenance_payload(statement_type="invalid"),
                IMAGE_DIGEST,
                COMMIT,
            )
        elif rule == "tooling-bootstrap-root":
            candidate = json.loads(json.dumps(current_registry))
            candidate["generator"]["bootstrap_root"]["distributions"] = []
            contract.validate_registry(candidate)
        elif rule == "emergency-update-controls":
            fixture_gates.validate_emergency_update_workflow(
                workflow + "\ncontinue-on-error: true\n"
            )
        elif rule == "spdx-creation-info-created-required":
            payload = minimal_spdx()
            del payload["creationInfo"]["created"]
            self.validate_spdx_without_components(payload)
        elif rule == "spdx-created-build-epoch":
            payload = minimal_spdx(created="2020-01-01T00:00:00Z")
            self.validate_spdx_without_components(payload)
        elif rule == "spdx-created-rfc3339-utc":
            payload = minimal_spdx(created="2023-11-14T22:13:20+00:00")
            self.validate_spdx_without_components(payload)
        elif rule == "spdx-document-namespace-deterministic":
            payload = minimal_spdx(namespace="https://example.test/random")
            self.validate_spdx_without_components(payload)
        elif rule == "spdx-document-namespace-unique-subject":
            fixture_gates.validate_namespace_uniqueness(
                [
                    {
                        "documentNamespace": "https://example.test/same",
                        "imageDigest": IMAGE_DIGEST,
                        "sourceCommit": COMMIT,
                        "buildDefinitionDigest": BUILD_DIGEST,
                    },
                    {
                        "documentNamespace": "https://example.test/same",
                        "imageDigest": OTHER_IMAGE_DIGEST,
                        "sourceCommit": COMMIT,
                        "buildDefinitionDigest": BUILD_DIGEST,
                    },
                ]
            )
        else:
            self.fail(f"No fixture trigger for rule {rule}")

    def validate_spdx_without_components(self, payload: dict[str, object]) -> None:
        locks = {profile: {} for profile in contract.LOCK_PROFILES}
        with (
            mock.patch.object(contract, "load_locks", return_value=locks),
            mock.patch.object(contract, "validate_spdx_schema"),
        ):
            contract.validate_spdx(
                payload,
                IMAGE_DIGEST,
                COMMIT,
                BUILD_DIGEST,
                EPOCH,
                "runtime",
            )

    def test_all_negative_matrix_cases_fail_on_their_exact_rule(self) -> None:
        payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        cases = payload["cases"]
        self.assertEqual(len(cases), 46)
        self.assertEqual(len({item["id"] for item in cases}), 46)
        for item in cases:
            with self.subTest(case=item["id"], rule=item["expected_rule"]):
                self.assert_rule(item["expected_rule"], self.trigger, item["expected_rule"])

    def test_current_positive_workflow_policy(self) -> None:
        text = WORKFLOW_PATH.read_text(encoding="utf-8")
        contract.validate_buildx_workflow(text, registry())
        fixture_gates.validate_clean_install_workflow(text)
        fixture_gates.validate_build_workflow(text)
        fixture_gates.validate_runtime_install_workflow(text)
        fixture_gates.validate_exact_head_workflow(text)
        fixture_gates.validate_publication_order_workflow(text)
        fixture_gates.validate_emergency_update_workflow(text)
        fixture_gates.validate_javascript_contour([])

    def test_buildx_oci_exporter_fails_closed(self) -> None:
        text = WORKFLOW_PATH.read_text(encoding="utf-8")
        current_registry = registry()
        cases = (
            text.replace("--driver docker-container", "--driver docker"),
            text.replace(
                "moby/buildkit@sha256:"
                "2f5adac4ecd194d9f8c10b7b5d7bceb5186853db1b26e5abd3a657af0b7e26ec",
                "moby/buildkit:buildx-stable-1",
            ),
            text.replace("--builder eod-provenance \\\n", "", 1),
        )
        for candidate in cases:
            with self.subTest(candidate=candidate):
                with self.assertRaisesRegex(
                    contract.ContractViolation,
                    "rule=buildx-oci-exporter",
                ):
                    contract.validate_buildx_workflow(candidate, current_registry)

    def test_current_five_locks_are_semantic_and_hashed(self) -> None:
        locks = contract.load_locks()
        self.assertEqual(tuple(locks), contract.LOCK_PROFILES)
        self.assertTrue(all(locks[profile] for profile in contract.LOCK_PROFILES))
        self.assertTrue(
            all(
                record.hashes
                for records in locks.values()
                for record in records.values()
            )
        )

    def test_namespace_contract_is_stable_and_subject_unique(self) -> None:
        first = contract.canonical_namespace(
            IMAGE_DIGEST, COMMIT, BUILD_DIGEST
        )
        repeated = contract.canonical_namespace(
            IMAGE_DIGEST, COMMIT, BUILD_DIGEST
        )
        other = contract.canonical_namespace(
            OTHER_IMAGE_DIGEST, COMMIT, BUILD_DIGEST
        )
        self.assertEqual(first, repeated)
        self.assertNotEqual(first, other)
        fixture_gates.validate_namespace_uniqueness(
            [
                {
                    "documentNamespace": first,
                    "imageDigest": IMAGE_DIGEST,
                    "sourceCommit": COMMIT,
                    "buildDefinitionDigest": BUILD_DIGEST,
                },
                {
                    "documentNamespace": other,
                    "imageDigest": OTHER_IMAGE_DIGEST,
                    "sourceCommit": COMMIT,
                    "buildDefinitionDigest": BUILD_DIGEST,
                },
            ]
        )


if __name__ == "__main__":
    unittest.main()
