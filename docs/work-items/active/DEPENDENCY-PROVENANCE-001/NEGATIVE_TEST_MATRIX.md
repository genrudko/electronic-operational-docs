# Fail-closed negative-test matrix

## Status vocabulary

- `INVENTORY-GATE` — implemented in this inventory/decision stage;
- `NEXT-IMPLEMENTATION` — mandatory implementation in the next bounded work;
- `LATER-BOUNDARY` — requires release/security/deployment capability not yet
  present, but contract is fixed here.

A planned row is not evidence that the gate already exists.

| ID | Mutation / prohibited state | Expected fail-closed rule | Evidence checked | Stage |
|---|---|---|---|---|
| DP-N01 | Python dependency installed but absent from canonical direct intent/lock profile | `python-canonical-declaration` | tracked manifests + executable install lines | NEXT-IMPLEMENTATION |
| DP-N02 | `pyproject.toml` changed without affected lock regeneration | `declaration-lock-drift` | direct-intent digest + generated lock headers/content | NEXT-IMPLEMENTATION |
| DP-N03 | Direct version/range changed but lock/hashes unchanged | `version-lock-hash-coherence` | package constraints + exact graph + hashes | NEXT-IMPLEMENTATION |
| DP-N04 | Lock file manually edited/reordered/truncated | `exact-generated-lock` | deterministic regeneration + semantic parser | NEXT-IMPLEMENTATION |
| DP-N05 | Lock requirement lacks exact `==` version | `exact-lock-version` | parsed lock record | NEXT-IMPLEMENTATION |
| DP-N06 | Lock artifact lacks accepted SHA-256 hashes | `lock-integrity-hashes` | all downloadable distributions | NEXT-IMPLEMENTATION |
| DP-N07 | PEP 517 build isolation resolves an undeclared build backend version | `locked-build-environment` | build lock + no-network/no-isolation evidence | NEXT-IMPLEMENTATION |
| DP-N08 | Runtime image installs from `pyproject.toml` ranges or runs unrestricted upgrade | `locked-runtime-install` | Dockerfile/workflow command scan | NEXT-IMPLEMENTATION |
| DP-N09 | Docker/Compose/workflow image uses tag only | `immutable-image-digest` | parsed image reference | NEXT-IMPLEMENTATION |
| DP-N10 | Image digest changed without readable version/registry metadata update | `image-digest-metadata-coherence` | image registry source + reference comment | NEXT-IMPLEMENTATION |
| DP-N11 | Same logical image has conflicting owners/versions | `single-image-owner` | duplicate-owner graph | NEXT-IMPLEMENTATION |
| DP-N12 | External GitHub Action uses tag, branch or shortened SHA | `immutable-action-sha` | every external `uses:` | NEXT-IMPLEMENTATION |
| DP-N13 | Action SHA lacks readable release/version comment | `action-version-metadata` | workflow source line | NEXT-IMPLEMENTATION |
| DP-N14 | Reusable external workflow is mutable | `immutable-reusable-workflow` | job-level `uses:` | NEXT-IMPLEMENTATION |
| DP-N15 | `curl`/`wget`/installer executes content without digest verification | `external-download-integrity` | executable source + canonical download registry | NEXT-IMPLEMENTATION |
| DP-N16 | Network response piped directly to shell/Python | `no-pipe-to-interpreter` | executable command scan | NEXT-IMPLEMENTATION |
| DP-N17 | Browser binary revision/download not tied to exact Playwright profile | `browser-binary-provenance` | browser lock + image/revision digest | NEXT-IMPLEMENTATION |
| DP-N18 | A JavaScript package contour appears without manifest/lock owner | `javascript-contour-owner` | tracked package/install files | NEXT-IMPLEMENTATION |
| DP-N19 | Inventory generated view manually altered | `inventory-generated-view-exact` | byte-for-byte regeneration | INVENTORY-GATE |
| DP-N20 | New dependency/build source path is omitted from inventory scanner | `inventory-source-completeness` | tracked-file scan and source digests | INVENTORY-GATE |
| DP-N21 | Temporary/post-merge coordination workflow remains tracked | `temporary-workflow-absent` | `.github/workflows/**` filename/content scan | INVENTORY-GATE |
| DP-N22 | SBOM subject is not final built image digest | `sbom-subject-digest` | OCI digest + SPDX document | NEXT-IMPLEMENTATION |
| DP-N23 | Runtime lock package missing from final image SBOM | `sbom-runtime-completeness` | lock graph ↔ SPDX packages/relationships | NEXT-IMPLEMENTATION |
| DP-N24 | Unexpected runtime package exists without classification | `sbom-unexpected-component` | image scan ↔ accepted graph | NEXT-IMPLEMENTATION |
| DP-N25 | Test-only/browser package silently enters production image | `sbom-scope-separation` | runtime vs dev/browser profiles | NEXT-IMPLEMENTATION |
| DP-N26 | Service image lacks exact-digest SBOM link | `sbom-service-boundary` | component-set manifest | NEXT-IMPLEMENTATION |
| DP-N27 | Generated static asset manifest is absent/stale | `static-manifest-exact` | collectstatic output digests | NEXT-IMPLEMENTATION |
| DP-N28 | SBOM created for another commit/image | `sbom-exact-head-chain` | provenance materials/subject | NEXT-IMPLEMENTATION |
| DP-N29 | Provenance source is a branch/tag or wrong exact head | `provenance-exact-head` | full source commit + workflow event SHA | NEXT-IMPLEMENTATION |
| DP-N30 | Provenance subject differs from published artifact | `provenance-subject-digest` | artifact/image digest | NEXT-IMPLEMENTATION |
| DP-N31 | Provenance omits applicable lock/image/action/workflow material | `provenance-material-completeness` | inventory-driven material set | NEXT-IMPLEMENTATION |
| DP-N32 | Provenance/SBOM publication happens before secret-hygiene | `secret-scan-before-publication` | job dependency/output proof | NEXT-IMPLEMENTATION |
| DP-N33 | Artifact contains credential-like content | `artifact-secret-free` | scanner + post-redaction verification | NEXT-IMPLEMENTATION |
| DP-N34 | Sanitized artifact is published without verification | `verified-sanitized-artifact-only` | existing secret-hygiene outputs | NEXT-IMPLEMENTATION |
| DP-N35 | Evidence/run IDs belong to different final heads | `single-final-exact-head-evidence` | workflow run commit SHA set | NEXT-IMPLEMENTATION |
| DP-N36 | Build leaves untracked/generated transport files in Git tree | `clean-tree-after-build` | exact porcelain gate | INVENTORY-GATE / existing |
| DP-N37 | SBOM is treated as proof of no vulnerabilities | `no-false-security-claim` | documentation/metadata claim scan | INVENTORY-GATE |
| DP-N38 | Published attestation cannot be verified | `attestation-verification` | verification command/result | LATER-BOUNDARY |
| DP-N39 | Architecture/platform differs from lock/image metadata | `platform-profile-coherence` | Python/platform/image metadata | NEXT-IMPLEMENTATION |
| DP-N40 | Emergency update bypasses locks, hashes, SBOM or owner acceptance | `emergency-update-controls` | emergency evidence package | NEXT-IMPLEMENTATION |

## Focused tests in this stage

The focused inventory suite verifies:

1. current repository inventory generation is deterministic;
2. Python/JavaScript/browser contours are classified from tracked facts;
3. mutable tag vs immutable digest classification;
4. mutable Action tag vs full commit SHA classification;
5. generated JSON/Markdown drift is rejected;
6. temporary workflow inventory is empty;
7. the inherited SECRET-HYGIENE GitHub evidence fixture matches accepted state.

## Required implementation fixture pattern

The next step must use isolated positive/negative fixtures. Each negative case
records:

```text
case id
single controlled mutation
expected rule id
expected/actual evidence in diagnostic
no network dependency unless explicitly testing network failure
```

A test that merely searches for a preferred string is insufficient. Validators
must parse the applicable manifest/reference and prove ownership, exactness and
boundary coherence.
