# DEPENDENCY-PROVENANCE-001 — execution log

## Coordination checkpoint — 2026-08-06

```text
issue: #57 / OPEN
Draft PR: #58 / OPEN / DRAFT / NOT MERGED
branch: supply-chain/dependency-provenance-001
accepted dependency: SECRET-HYGIENE-001
accepted dependency merge: 95b8dd6017745886f110f052ea0950b3d48173d8
SAFE-CONTINUATION: 3/8 accepted / NOT ACHIEVED
runtime impact: NONE
Preview: UNTOUCHED
```

No Preview, development VPS or production runtime operation was performed.
Volatile project state remains owned only by `docs/project/CURRENT_STATE.md`.

## Guardrails

- No second package manager or duplicate direct-intent owner.
- No dependency upgrade, production lock generation or broad pinning.
- No Action/image migration.
- No release SBOM/provenance generation or publication.
- No external SaaS.
- No product/domain/model/migration/data/UX change.
- No Ready for Review or merge without separate owner instruction.

## Initial inventory/architecture-decision stage

The initial deterministic inventory recorded:

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
```

The product owner accepted the principal architecture but required a bounded
repair of source completeness, local image classification, deterministic SPDX
identity, tooling bootstrap trust and Ruff compliance.

## Bounded architecture repair — 2026-08-06

### Repository-wide executable/config discovery

Discovery is no longer restricted to executable files under `scripts/**`. It
now classifies tracked applicable sources independently of directory:

- GitHub workflows;
- Dockerfiles;
- Compose files;
- `**/*.sh` and `**/*.bash`;
- applicable PowerShell scripts;
- extensionless shell entrypoints by shebang;
- Makefile/task/build files when present;
- deploy/operator/build Python sources selected by deploy path,
  executable/shebang evidence, operator/build filename or parsed external-process
  call.

Arbitrary documentation and generated JSON/Markdown files are not treated as
executable sources. The exact exclusion registry is empty. Any future exclusion
must name one exact path and rationale; directory-wide exemptions are prohibited.
The generated inventory records the complete applicable-path set and SHA-256
source digests, so a new applicable tracked path cannot remain outside inventory
silently.

Repaired inventory facts:

```text
tracked files: 873
inventory entries: 55
floating inputs: 38
immutable inputs: 16
duplicate owner groups: 6
conflicting owner groups: 3
source files with dependency/build evidence: 16
applicable executable/config sources: 53
source completeness digests: 55
uncovered applicable paths: 0
exact source exclusions: 0
external executable downloads: 0
post-merge temporary workflow files: 0
```

The expanded discovery did not add a real dependency/build input to the current
repository. It did expose and then reject one parser false positive: a shell
availability loop merely mentioned `curl`; download classification now requires
an actual `curl`/`wget` invocation. Local HTTP health probes remain excluded.

### Local image ownership

A short/tagless image name is no longer local by syntax. Classification requires
proved build ownership:

- Compose service contains `build:`;
- image is linked to a tracked Dockerfile/build target; or
- image is declared in an exact canonical local-output registry.

Therefore:

```text
image: postgres                         -> external mutable input
image: postgres:18.4-bookworm           -> external mutable input
image: postgres@sha256:<64 hex>          -> external immutable input
build: + image: eod-development-app     -> local build output
same short name without build evidence  -> external input
```

The current `eod-development-app` remains the single local output because its
Compose service contains `build:`.

### Deterministic SPDX 2.3 contract

SPDX 2.3 JSON remains canonical. Mandatory `creationInfo.created` is retained
and deterministically derived from verified accepted build epoch, normally
`SOURCE_DATE_EPOCH` equal to the exact source commit timestamp. Runner wall clock
is prohibited. Canonical rendering is UTC `YYYY-MM-DDTHH:MM:SSZ`.

`documentNamespace` is deterministically derived from:

```text
namespace-contract version
+ final image SHA-256 digest
+ exact source commit
+ build-definition digest
```

Random UUID, runner identity and wall-clock time are prohibited. The SBOM digest
is deliberately not a namespace input, avoiding circular identity. Repeated
normalization of identical evidence must be byte-identical; another image/source
or build definition must receive another namespace. A pinned official SPDX 2.3
schema is validated before secret scan, attestation or publication.

Future fail-closed fixtures are recorded for missing/volatile/malformed created
timestamp, nondeterministic/reused namespace and schema-invalid SPDX. No release
SBOM was generated in this repair.

### Five lock profiles and non-circular tooling root

The exact profile set is aligned everywhere:

```text
tooling
build
runtime
dev
browser
```

The tooling lock is not trusted because it generated itself. Bootstrap root of
trust is the accepted tuple of digest-pinned generator OCI environment, exact
Python/platform, exact bootstrap `pip`/`pip-tools` versions, independently
verified checked-in distribution SHA-256 hashes, bootstrap evidence digest and
exact accepted source commit.

First acceptance sequence:

```text
digest-pinned generator environment
→ bootstrap tooling from checked-in exact hashes
→ regenerate tooling/build/runtime/dev/browser
→ semantic validation
→ byte-for-byte comparison
→ clean installation proof
→ atomic acceptance of generator identity and all five locks
```

A controlled generator upgrade first proves the previous generator reproduces
the accepted baseline, validates candidate bootstrap evidence, regenerates all
five candidate locks and accepts generator identity plus locks atomically.
Rollback restores the prior five locks, generator digest, bootstrap evidence and
regeneration contract, then reproves byte-identical output and clean install.

### Ruff contract

The file-wide Ruff exemption
`"scripts/dependency_provenance_inventory.py" = ["E501"]` was removed. Scanner
code is formatted to the ordinary repository Ruff contract. No replacement
broad lint exemption was introduced.

## Focused repair evidence

The focused suite covers:

1. deploy-path `pip install` discovery;
2. `apt-get install` in shell outside `scripts/**`;
3. external `curl` in bootstrap/operator source;
4. local health-probe exclusion;
5. future applicable-path inclusion and source digest;
6. applicable Python subprocess discovery outside `scripts/**`;
7. tagless/tagged/digest/local-build image classification;
8. non-inheritance of local classification by identical short name;
9. exact five-profile vocabulary;
10. future deterministic SPDX fixture/rule IDs;
11. absence of the scanner file-wide Ruff exemption;
12. byte-exact generated inventory views.

## Architecture preserved

- `pyproject.toml` is the sole direct Python intent owner;
- Python installation remains `pip`;
- `pip-tools` is a generator, not another package manager owner;
- npm/yarn/pnpm are not introduced;
- external OCI images are future digest-pinned inputs;
- external GitHub Actions are future full-SHA inputs;
- canonical SBOM remains SPDX 2.3 JSON;
- provenance remains in-toto Statement v1 + SLSA Provenance v1;
- secret-hygiene precedes publication;
- no external SaaS is introduced.

## Stage stop

This repair stops again at substantive product-owner acceptance of the
architecture decision. PR #58 remains OPEN / DRAFT / NOT MERGED. No production
locks, dependency migration, image/Action migration, release SBOM, provenance,
attestation, deployment, Ready for Review or merge has been performed.
