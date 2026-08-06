# Next implementation plan

## Preconditions

- architecture decision accepted by product owner;
- this inventory remains exact on accepted head;
- no package/version update is mixed into mechanical locking unless required to
  resolve an explicitly documented incompatibility;
- same issue/branch/PR policy is used for the implementation work item selected
  by canonical coordination state;
- Preview/VPS remain untouched unless a later delivery scope explicitly permits
  them.

## Phase 1 — canonical metadata and generator

1. Add a small machine-readable supply-chain registry for:
   - Python lock profiles/platform;
   - external container images and readable versions;
   - GitHub Actions and readable releases;
   - external downloads/browser inputs;
   - SBOM/provenance generator identities.
2. Add a pinned `tooling` bootstrap profile.
3. Add a repository regeneration/check script using `pip-tools`.
4. Keep all direct intent in `pyproject.toml`; no duplicated direct requirement
   lists.
5. Add deterministic headers and byte-for-byte regeneration checks.

Acceptance:

- no network-resolved generator version;
- clean check mode produces zero diff;
- malformed/manual lock changes fail with named rule IDs.

## Phase 2 — Python lock profiles

1. Generate `build`, `runtime`, `dev` and `browser` locks for Python 3.13 and the
   accepted Linux architecture profile.
2. Preserve current accepted dependency ranges/versions as far as resolver and
   available artifacts permit; do not perform opportunistic upgrades.
3. Include SHA-256 hashes for every permitted distribution.
4. Prove clean-environment installation with `--require-hashes`.
5. Build the application wheel from the locked build environment without
   unrestricted PEP 517 resolution.
6. Verify installed graph using `pip check` and an exact package snapshot.

Acceptance:

- two clean runs resolve/install the same package/version/hash set;
- runtime image contains no dev/browser-only packages;
- all current application tests remain green.

## Phase 3 — consume locks everywhere

1. Replace unrestricted Dockerfile `pip install --upgrade` and `pip install .`
   resolution with locked build/runtime stages.
2. Update CI installation to consume exact dev/runtime profiles.
3. Update browser gates to consume browser profile and pinned browser
   image/revision.
4. Scan workflows/scripts for bypass installs and fail closed.
5. Keep local developer procedure documented and explicit.

Acceptance:

- no executable install bypass remains;
- container build works with dependency network disabled after immutable inputs
  are fetched/cached;
- no product/domain/runtime behavior change beyond dependency determinism.

## Phase 4 — immutable container images

1. Resolve current accepted human-readable tags to registry digests.
2. Record registry source, platform and verification timestamp as evidence, not
   as mutable identity.
3. Pin Dockerfile, Compose and workflow service images by digest with readable
   comments/metadata.
4. Add duplicate-owner and digest/metadata coherence validators.
5. Validate target architecture explicitly.

Acceptance:

- tag-only reference fixture fails;
- changed digest without metadata fails;
- all images pull/build by exact digest.

## Phase 5 — immutable GitHub Actions

1. Resolve every current Action/reusable workflow ref to a full commit SHA.
2. Preserve readable release comments.
3. Add parser-based workflow validator for step-level and job-level `uses:`.
4. Detect shell downloads and route them through the external-download registry.
5. Keep least-privilege permissions and exact-head checkout semantics.

Acceptance:

- no mutable external `uses:` remains;
- tag/branch/short-SHA negative fixtures fail;
- existing workflows execute on one exact head.

## Phase 6 — deterministic static/build outputs

1. Build wheel and collectstatic output in controlled environment.
2. Generate normalized static manifest with path/size/SHA-256.
3. Record wheel/static manifest digests as provenance materials.
4. Reject tracked build output/temporary transport files unless explicitly
   canonical.

Acceptance:

- repeated build has identical dependency/static manifests;
- unexpected generated file fails the boundary gate;
- clean tree remains exact after tests/build cleanup.

## Phase 7 — SBOM

1. Pin SBOM generator identity/digest.
2. Build final OCI image once and resolve final digest.
3. Generate SPDX 2.3 JSON from that exact digest.
4. Normalize stable fields/order and validate schema/boundary.
5. Compare runtime lock against Python components and relationships.
6. Generate/link service-image SBOMs for exact digests.
7. Secret-scan candidate SBOM and artifact before publication.

Acceptance:

- subject digest equals final image;
- required runtime/OS/application components are present;
- test-only packages and credentials are absent;
- SBOM is explicitly not presented as vulnerability proof.

## Phase 8 — exact-head provenance and attestation

1. Generate in-toto/SLSA statement from verified workflow outputs.
2. Include all inventory-driven immutable materials.
3. Add bounded least-privilege attestation job/action pinned by SHA.
4. Verify the attestation against subject digest and repository identity.
5. Publish only after secret-hygiene outputs prove safe content.

Acceptance:

- another-head fixture fails;
- subject/material omission fixture fails;
- published attestation verifies independently;
- all run IDs refer to one final exact head.

## Phase 9 — operator procedures

Document and test:

- ordinary dependency change;
- emergency vulnerability update;
- container/action digest refresh;
- lock regeneration and review;
- SBOM/provenance verification;
- rollback to prior lock/image/artifact set;
- registry/tool outage limitations.

The owner-facing procedure uses a small number of deterministic commands and
explains what changed in plain language.

## Required final validation profile

```text
focused dependency/provenance unit and negative tests
Documentation Contract
Secret Hygiene current/history/artifact gates
Ruff / compileall / Django check
migration check (no migration expected)
full PostgreSQL suite
container development and preview smoke as applicable
SBOM/provenance verification
clean tree
no temporary workflow files
all applicable workflows on one final exact head
```

## Stop conditions

- no Ready for Review or merge without explicit product-owner instruction;
- no mass dependency upgrade hidden in lock adoption;
- no new frontend package manager unless factual frontend build need is first
  accepted;
- no VPS/Preview deployment during dependency implementation unless separately
  authorized;
- any resolver-forced version change is isolated, explained and reviewed rather
  than silently accepted.
