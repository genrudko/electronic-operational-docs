# Fail-closed negative-test matrix

## Status vocabulary

- `INVENTORY-GATE` — implemented in this inventory/decision stage;
- `NEXT-IMPLEMENTATION` — mandatory in the next bounded implementation;
- `LATER-BOUNDARY` — requires a later release/security/deployment capability.

A planned row is not evidence that the gate already exists. The current repair
adds inventory regressions and future SPDX fixtures but does not generate a
release lock, SBOM, provenance or attestation.

| ID | Mutation / prohibited state | Expected fail-closed rule | Evidence checked | Stage |
|---|---|---|---|---|
| DP-N01 | Python dependency installed but absent from canonical direct intent/lock profile | `python-canonical-declaration` | tracked manifests + executable install lines | NEXT-IMPLEMENTATION |
| DP-N02 | `pyproject.toml` changed without affected lock regeneration | `declaration-lock-drift` | direct-intent digest + generated lock headers/content | NEXT-IMPLEMENTATION |
| DP-N03 | Direct version/range changed but lock/hashes unchanged | `version-lock-hash-coherence` | package constraints + exact graph + hashes | NEXT-IMPLEMENTATION |
| DP-N04 | Lock file manually edited/reordered/truncated | `exact-generated-lock` | deterministic regeneration + semantic parser | NEXT-IMPLEMENTATION |
| DP-N05 | Lock requirement lacks exact `==` version | `exact-lock-version` | parsed lock record | NEXT-IMPLEMENTATION |
| DP-N06 | Lock artifact lacks accepted SHA-256 hashes | `lock-integrity-hashes` | all downloadable distributions | NEXT-IMPLEMENTATION |
| DP-N07 | PEP 517 build isolation resolves an undeclared backend version | `locked-build-environment` | build lock + no-network/no-isolation evidence | NEXT-IMPLEMENTATION |
| DP-N08 | Runtime installs from ranges or unrestricted upgrade | `locked-runtime-install` | repository-wide executable source scan | NEXT-IMPLEMENTATION |
| DP-N09 | External Docker/Compose/workflow image uses tag or tagless name without digest | `immutable-image-digest` | parsed image reference and build ownership | NEXT-IMPLEMENTATION |
| DP-N10 | Image digest changed without readable version/registry metadata update | `image-digest-metadata-coherence` | image registry source + reference metadata | NEXT-IMPLEMENTATION |
| DP-N11 | Same logical image has conflicting owners/versions | `single-image-owner` | duplicate-owner graph | NEXT-IMPLEMENTATION |
| DP-N12 | External GitHub Action uses tag, branch or shortened SHA | `immutable-action-sha` | every external `uses:` | NEXT-IMPLEMENTATION |
| DP-N13 | Action SHA lacks readable release/version comment | `action-version-metadata` | workflow source line | NEXT-IMPLEMENTATION |
| DP-N14 | Reusable external workflow is mutable | `immutable-reusable-workflow` | job-level `uses:` | NEXT-IMPLEMENTATION |
| DP-N15 | `curl`/`wget` executes content without digest verification | `external-download-integrity` | executable source + canonical registry | NEXT-IMPLEMENTATION |
| DP-N16 | Network response piped directly to shell/Python | `no-pipe-to-interpreter` | executable command scan | NEXT-IMPLEMENTATION |
| DP-N17 | Browser binary not tied to exact Playwright profile | `browser-binary-provenance` | browser lock + image/revision digest | NEXT-IMPLEMENTATION |
| DP-N18 | JavaScript package contour appears without manifest/lock owner | `javascript-contour-owner` | tracked package/install files | NEXT-IMPLEMENTATION |
| DP-N19 | Inventory generated view manually altered | `inventory-generated-view-exact` | byte-for-byte regeneration | INVENTORY-GATE |
| DP-N20 | New applicable executable/config path omitted from discovery/digests | `inventory-source-completeness` | tracked applicable-path set + source digests | INVENTORY-GATE |
| DP-N21 | Temporary/post-merge coordination workflow remains tracked | `temporary-workflow-absent` | workflow filename/content scan | INVENTORY-GATE |
| DP-N22 | SBOM subject is not final built image digest | `sbom-subject-digest` | OCI digest + SPDX document | NEXT-IMPLEMENTATION |
| DP-N23 | Runtime lock package missing from final image SBOM | `sbom-runtime-completeness` | runtime graph ↔ SPDX packages/relationships | NEXT-IMPLEMENTATION |
| DP-N24 | Unexpected runtime package exists without classification | `sbom-unexpected-component` | image scan ↔ accepted graph | NEXT-IMPLEMENTATION |
| DP-N25 | Test/browser package silently enters production image | `sbom-scope-separation` | runtime vs dev/browser profiles | NEXT-IMPLEMENTATION |
| DP-N26 | Service image lacks exact-digest SBOM link | `sbom-service-boundary` | component-set manifest | NEXT-IMPLEMENTATION |
| DP-N27 | Generated static asset manifest absent/stale | `static-manifest-exact` | collectstatic output digests | NEXT-IMPLEMENTATION |
| DP-N28 | SBOM created for another commit/image | `sbom-exact-head-chain` | provenance materials/subject | NEXT-IMPLEMENTATION |
| DP-N29 | Provenance source is branch/tag or wrong exact head | `provenance-exact-head` | source commit + event SHA | NEXT-IMPLEMENTATION |
| DP-N30 | Provenance subject differs from published artifact | `provenance-subject-digest` | artifact/image digest | NEXT-IMPLEMENTATION |
| DP-N31 | Provenance omits lock/image/action/workflow material | `provenance-material-completeness` | inventory-driven material set | NEXT-IMPLEMENTATION |
| DP-N32 | Provenance/SBOM publication before secret-hygiene | `secret-scan-before-publication` | job dependency/output proof | NEXT-IMPLEMENTATION |
| DP-N33 | Artifact contains credential-like content | `artifact-secret-free` | scanner + post-redaction verification | NEXT-IMPLEMENTATION |
| DP-N34 | Sanitized artifact published without verification | `verified-sanitized-artifact-only` | secret-hygiene outputs | NEXT-IMPLEMENTATION |
| DP-N35 | Evidence/run IDs belong to different heads | `single-final-exact-head-evidence` | workflow run commit set | NEXT-IMPLEMENTATION |
| DP-N36 | Build leaves untracked/generated transport files | `clean-tree-after-build` | exact porcelain gate | INVENTORY-GATE / existing |
| DP-N37 | SBOM treated as proof of no vulnerabilities | `no-false-security-claim` | documentation/metadata claim scan | INVENTORY-GATE |
| DP-N38 | Published attestation cannot be verified | `attestation-verification` | verification command/result | LATER-BOUNDARY |
| DP-N39 | Architecture/platform differs from lock/image metadata | `platform-profile-coherence` | Python/platform/image metadata | NEXT-IMPLEMENTATION |
| DP-N40 | Emergency update bypasses locks/hashes/SBOM/acceptance | `emergency-update-controls` | emergency evidence package | NEXT-IMPLEMENTATION |
| DP-N41 | Mandatory `creationInfo.created` is missing | `spdx-creation-info-created-required` | parsed SPDX 2.3 JSON | NEXT-IMPLEMENTATION |
| DP-N42 | `creationInfo.created` comes from runner wall clock, not accepted epoch | `spdx-created-build-epoch` | SOURCE_DATE_EPOCH + exact source evidence | NEXT-IMPLEMENTATION |
| DP-N43 | `creationInfo.created` is non-UTC or malformed | `spdx-created-rfc3339-utc` | canonical RFC 3339 UTC parser | NEXT-IMPLEMENTATION |
| DP-N44 | `documentNamespace` contains random/volatile input or changes for identical evidence | `spdx-document-namespace-deterministic` | namespace derivation + repeated normalization | NEXT-IMPLEMENTATION |
| DP-N45 | Same namespace reused for another image/source/build definition | `spdx-document-namespace-unique-subject` | namespace ↔ immutable identity tuple | NEXT-IMPLEMENTATION |
| DP-N46 | Normalized SPDX document fails pinned official schema | `spdx-schema-valid` | pinned schema identity/digest + validation result | NEXT-IMPLEMENTATION |

## Implemented focused regressions in this repair

The focused suite verifies:

1. current repository contours and exact five-profile vocabulary;
2. mutable Action tag versus full commit SHA;
3. `image: postgres` is external mutable;
4. `image: postgres:18.4-bookworm` is external mutable;
5. `image: postgres@sha256:...` is external immutable;
6. service with `build:` plus `image: eod-development-app` is local output;
7. same short image name without `build:` remains external;
8. `pip install` and external `curl` in `deploy/automation/bootstrap.sh` are found;
9. `apt-get install` in shell outside `scripts/**` is found;
10. local HTTP health probe remains excluded;
11. future applicable executable path enters applicable-path set/source digests;
12. external-process Python operation outside `scripts/**` is found;
13. all source exclusions, if any, are exact and carry rationale;
14. generated inventory views remain byte-exact;
15. scanner has no file-wide Ruff exemption;
16. future SPDX fixture IDs/rule IDs are exact.

## Future SPDX fixtures

Machine-readable fixtures are stored at:

`tests/process/fixtures/dependency_provenance_negative_cases.json`

They define:

- `DP-SPDX-001` — missing `creationInfo.created`;
- `DP-SPDX-002` — volatile runner timestamp;
- `DP-SPDX-003` — incorrect timestamp format;
- `DP-SPDX-004` — nondeterministic namespace;
- `DP-SPDX-005` — namespace reused for another image/build;
- `DP-SPDX-006` — schema-invalid SPDX document.

All are explicitly `NEXT-IMPLEMENTATION`; their presence does not claim a
release SBOM validator exists in this repair.

## Fixture discipline

Each implementation fixture records:

```text
case id
single controlled mutation
expected rule id
expected/actual evidence in diagnostic
no network dependency unless explicitly testing network failure
```

String preference checks are insufficient. Validators must parse the applicable
manifest/reference and prove ownership, exactness and boundary coherence.
