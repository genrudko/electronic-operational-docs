# DEPENDENCY-PROVENANCE-001 — execution log

## Coordination checkpoint — 2026-08-06

```text
issue: #57 / OPEN
Draft PR: #58 / OPEN / DRAFT / NOT MERGED
branch: supply-chain/dependency-provenance-001
accepted dependency: SECRET-HYGIENE-001
accepted dependency merge: 95b8dd6017745886f110f052ea0950b3d48173d8
SAFE-CONTINUATION: 3/8 accepted / NOT ACHIEVED
runtime impact at start: NONE
```

Delivery-boundary evidence: no Preview, development VPS or production runtime
operation was performed by this work item. Volatile project state remains owned
only by `docs/project/CURRENT_STATE.md`.

Canonical post-merge state has been generated and validated before implementation:

```text
Demo release / industrialization state contract: OK
modules: 27
work-item status projections: 60
industrialization work items: 30
PILOT-READY mandatory core: 21
secret-hygiene tracked scan: PASS
allowlist entries: 0
```

## Initial factual inventory boundary

The implementation must inventory evidence before selecting or introducing tooling.
The inventory is split into five non-overlapping classes:

1. Python application, build, development and test dependencies.
2. JavaScript/browser/build dependencies, only where they actually exist.
3. Container base images, service images and system packages.
4. GitHub Actions and reusable workflow/action references.
5. Generated artifacts, external downloads, SBOM and provenance outputs.

Each finding must record:

- repository path;
- current declaration/reference;
- mutable or immutable status;
- existing lock/hash/digest evidence;
- runtime/build/test scope;
- proposed canonical owner;
- required negative gate;
- any bounded residual risk.

## Guardrails

- No second package manager or duplicate lock owner without demonstrated need.
- No dependency upgrade merely to obtain a newer version.
- No automatic merge or uncontrolled update bot.
- No product/domain model, migration, data or UX change.
- No VPS or Preview change during inventory.
- No claim that SBOM generation alone proves vulnerability absence.
- Ready for Review and merge require separate owner acceptance.

## Inventory and decision completion — 2026-08-06

The repository-wide deterministic scan completed with this accepted inventory
shape:

```text
tracked files: 871
inventory entries: 55
floating inputs: 38
immutable inputs: 16
duplicate owner groups: 6
conflicting owner groups: 3
source files with dependency/build evidence: 16
separate JavaScript dependency contour: ABSENT
external executable downloads: 0
post-merge temporary workflow files: 0
```

The full records are stored in four deterministic JSON shards. The manifest
contains their path, entry count, ID range and SHA-256 checksum. The generated
Markdown report is a byte-checked owner-oriented view of the same scan.

The selected architecture is:

1. `pyproject.toml` remains the only readable owner of direct Python intent.
2. `pip-tools` is the recommended generator for deterministic, hash-locked
   runtime, development and browser profiles; it does not become a second
   dependency owner.
3. No JavaScript package manager is introduced because the repository has no
   independent frontend dependency contour.
4. External OCI images must move to digest references with readable version
   comments in the implementation stage.
5. GitHub Actions must move to full commit SHA references with readable version
   comments in the implementation stage.
6. The final OCI image is the primary CycloneDX JSON SBOM boundary; source and
   build provenance remain separate evidence.
7. Provenance must link the exact repository head, lock digests, workflow
   identity, final image digest and SBOM digest.
8. Secret-hygiene verification must complete before any SBOM, provenance or
   diagnostic artifact is published.
9. All declaration/lock/hash/digest/provenance drift checks are fail-closed.

Focused validation added in this stage covers mutable and immutable Action
references, image tags versus digests, local image outputs, local health probes,
full generated-view equality and repository contour facts. The existing project
state, release-plan compatibility, module projection and industrialization
execution regressions remain part of the same Documentation Contract run.

## Stage stop

This work item is ready for substantive owner review of the architecture decision.
The PR remains open and Draft. No dependency version migration, mass Action/image
pinning, lock generation, SBOM publication, deployment, Ready for Review or merge
has been performed.

The next implementation step, only after owner acceptance, is a bounded migration
that generates the hashed Python lock profiles first, validates clean-environment
installation, then pins Actions/images and introduces exact-head SBOM/provenance
publication gates.
