# Next implementation plan

## Preconditions

- repaired architecture decision accepted by product owner;
- inventory remains exact on accepted head;
- no package/version update is mixed into mechanical locking unless an
  explicitly documented incompatibility requires it;
- Preview/VPS remain untouched unless later scope explicitly permits them;
- implementation does not start during the current repair stage.

## Canonical profile set

Every implementation document, command and validator uses exactly:

```text
tooling
build
runtime
dev
browser
```

Canonical paths:

```text
requirements/locks/tooling.txt
requirements/locks/build.txt
requirements/locks/runtime.txt
requirements/locks/dev.txt
requirements/locks/browser.txt
```

## Phase 1 — bootstrap root and generator

1. Add a small machine-readable supply-chain registry for Python profiles and
   platform, generator/bootstrap evidence, images, Actions, downloads/browser
   inputs and SBOM/provenance tooling identities.
2. Select a digest-pinned generator OCI environment with exact Python minor and
   platform.
3. Check in a bootstrap manifest containing exact `pip`, `pip-tools` and support
   distribution identities plus independently verified SHA-256 hashes.
4. Record generator image digest, tool versions, bootstrap manifest digest and
   accepted source commit as bootstrap evidence.
5. Install bootstrap tooling with `--require-hashes` without trusting a
   candidate `tooling.txt`.
6. Generate all five profiles.
7. Perform semantic validation, byte-for-byte regeneration comparison and clean
   installation proof.

Mandatory sequence:

```text
digest-pinned generator environment
→ bootstrap tooling from checked-in exact hashes
→ regenerate tooling/build/runtime/dev/browser
→ semantic validation
→ byte-for-byte comparison
→ clean installation proof
```

First accepted tooling lock is accepted atomically with the external generator
identity and bootstrap evidence. It is not trusted because it generated itself.

Acceptance:

- no tag-only/network-resolved generator;
- bootstrap distributions have exact versions and hashes;
- five-profile set is exact;
- clean check mode produces zero diff;
- malformed/manual lock changes fail with named rule IDs.

## Controlled generator upgrade and rollback

Upgrade procedure:

1. previous accepted generator reproduces previous locks byte-for-byte;
2. candidate image digest/tool versions/bootstrap hashes are recorded;
3. previous accepted validator verifies candidate bootstrap evidence and policy;
4. candidate generator regenerates all five profiles;
5. full graph diff, semantic validation and clean installs pass;
6. generator identity and five locks are accepted atomically.

Rollback restores from the previous accepted commit the five locks, generator
image digest, bootstrap manifest/evidence and regeneration contract. The former
generator must reproduce the restored locks byte-for-byte and pass clean install.

## Phase 2 — Python lock profiles

1. Generate `tooling`, `build`, `runtime`, `dev` and `browser` for Python 3.13
   and accepted Linux architecture.
2. Preserve accepted dependency ranges/versions as far as resolver and available
   artifacts permit; no opportunistic upgrades.
3. Include SHA-256 hashes for every permitted distribution.
4. Prove clean installation with `--require-hashes`.
5. Build wheel from locked build environment without unrestricted PEP 517
   resolution.
6. Verify installed graph using `pip check` and exact package snapshot.

Acceptance:

- two clean runs produce identical package/version/hash sets;
- runtime image contains no dev/browser-only packages;
- all application tests remain green.

## Phase 3 — consume locks everywhere

1. Replace unrestricted Dockerfile/workflow installs with locked build/runtime
   stages.
2. CI uses exact dev/runtime profiles.
3. Browser gates use browser profile and pinned browser image/revision.
4. Repository-wide executable/config scanner rejects bypass installs in
   workflows, Docker/Compose, shell, deploy/operator Python and task/build files.
5. Local developer procedure remains explicit.

Acceptance:

- no executable install bypass remains;
- new applicable tracked path is included in source-completeness digests;
- no product/domain/runtime behavior change beyond dependency determinism.

## Phase 4 — immutable container images

1. Resolve accepted readable tags to registry digests.
2. Record registry source/platform and verification evidence.
3. Pin Dockerfile, Compose and workflow images by digest with readable metadata.
4. Validate duplicate-owner and digest/metadata coherence.
5. Distinguish local output only through service `build:`, tracked build target or
   exact canonical local-output registry.

Acceptance:

- `image: postgres` and tag-only fixtures fail immutable-input rule;
- digest reference is immutable;
- local build service is output;
- identical short name without build remains external;
- all images pull/build by exact digest.

## Phase 5 — immutable GitHub Actions and downloads

1. Resolve every external Action/reusable workflow to full commit SHA.
2. Preserve readable release comments.
3. Parse step-level and job-level `uses:`.
4. Route shell downloads through canonical download registry.
5. Preserve least-privilege and exact-head checkout semantics.

Acceptance:

- no mutable external `uses:` remains;
- tag/branch/short-SHA fixtures fail;
- local HTTP probes remain excluded from external-download inputs.

## Phase 6 — deterministic build outputs

1. Build wheel and collectstatic in controlled environment.
2. Generate normalized static manifest with path/size/SHA-256.
3. Record wheel/static digests as provenance materials.
4. Reject undeclared tracked build output/transport files.

Acceptance:

- repeated build has identical dependency/static manifests;
- unexpected generated file fails boundary gate;
- clean tree remains exact.

## Phase 7 — deterministic SPDX 2.3 JSON

1. Pin SBOM generator and official SPDX 2.3 schema identities/digests.
2. Build final OCI image once and resolve final digest.
3. Establish accepted `SOURCE_DATE_EPOCH` from exact source commit timestamp or
   another explicitly accepted immutable epoch.
4. Generate SPDX 2.3 JSON from exact image digest.
5. Preserve mandatory `creationInfo.created` and normalize it to
   `YYYY-MM-DDTHH:MM:SSZ` UTC; runner wall clock is prohibited.
6. Generate canonical `documentNamespace` from namespace-contract version, final
   image digest, exact source commit and build-definition digest.
7. Normalize stable ordering and prove repeated normalization byte-identical.
8. Validate pinned official schema before secret scan/publication.
9. Compare runtime lock with Python components/relationships and link service
   image SBOMs.
10. Secret-scan candidate SBOM/artifact before publication.

Acceptance:

- missing/volatile/malformed `creationInfo.created` fails;
- random or reused namespace fails;
- another image/build receives another namespace;
- schema-invalid SPDX fails before publication;
- subject digest equals final image;
- required components are present and test-only/secret content absent.

## Phase 8 — exact-head provenance and attestation

1. Generate in-toto Statement v1 with SLSA Provenance v1 predicate.
2. Include exact commit, workflow, all five locks, bootstrap/generator identity,
   images, Actions, build epoch, namespace, static manifest and SBOM digest.
3. Add bounded least-privilege attestation job pinned by SHA.
4. Verify subject digest and repository identity.
5. Publish only after schema, boundary and secret-hygiene outputs pass.

Acceptance:

- another-head fixture fails;
- subject/material omission fails;
- published attestation verifies independently;
- all run IDs refer to one final exact head.

## Phase 9 — operator procedures

Document and test ordinary change, emergency update, image/Action refresh,
regeneration/review, generator upgrade, rollback, SBOM/provenance verification
and registry/tool outage limitations.

## Required final validation profile

```text
focused dependency/provenance unit and negative tests
Documentation Contract
Secret Hygiene current/history/artifact gates
Ruff / compileall / Django check
migration check (no migration expected)
full PostgreSQL suite
container development/preview smoke only when applicable and authorized
SBOM/provenance verification after implementation
clean tree
no temporary workflow files
all applicable workflows on one final exact head
```

## Stop conditions

- no Ready for Review or merge without explicit owner instruction;
- no mass dependency update hidden in lock adoption;
- no frontend package manager without accepted factual need;
- no VPS/Preview deployment during this repair;
- no release lock, SBOM or provenance publication during this repair;
- resolver-forced version changes are isolated and explained.
