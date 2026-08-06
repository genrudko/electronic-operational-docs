# Canonical dependency/lock/provenance contract

## 1. Ownership

| Information | Single owner |
|---|---|
| Direct Python intent and supported ranges | `pyproject.toml` |
| Exact resolved Python graphs and hashes | five generated lock profiles |
| Generator/bootstrap identity | supply-chain registry + bootstrap evidence |
| Lock generation logic | repository regeneration/validation scripts |
| Container image identity | validated image registry/references |
| GitHub Action identity | each validated workflow `uses:` |
| Final artifact identity | exact-head OCI/artifact digest |
| SBOM identity | deterministic SPDX namespace + SBOM digest |
| Provenance identity | in-toto/SLSA statement and attestation |

Generated files never become a second direct-intent owner. Direct requirements
change only in `pyproject.toml`; every affected projection is regenerated.

## 2. Exact profile set

```text
requirements/locks/tooling.txt
requirements/locks/build.txt
requirements/locks/runtime.txt
requirements/locks/dev.txt
requirements/locks/browser.txt
```

No fourth-profile/five-profile ambiguity is permitted. Every contract and check
uses exactly `tooling`, `build`, `runtime`, `dev`, `browser`.

All locks use normalized ordering, exact versions and `--hash=sha256:` records.
Headers record generator identity/version, canonical inputs, target Python minor,
OS/architecture profile and exact regeneration command. Headers contain no
wall-clock timestamp or machine path.

### Tooling

Exact `pip`, `pip-tools` and support packages used to compile all profiles.
Tooling cannot update itself implicitly.

### Build

Exact frontend/backend requirements used to build the wheel. Unrestricted PEP
517 build isolation/network resolution is prohibited.

### Runtime

Complete production graph. Final container installs this graph and an already
built application wheel without resolving `pyproject.toml` ranges.

### Development

Runtime plus `[dev]` tests/quality tooling. It is not production runtime.

### Browser

Runtime plus Python Playwright dependencies. Browser binary/image identity is a
separate immutable input. No `package.json` is introduced solely for Playwright.

## 3. Tooling bootstrap root of trust

The tooling lock is not self-authenticating. Root of trust is the accepted tuple:

```text
digest-pinned generator OCI image
exact Python minor and platform
exact bootstrap pip/pip-tools versions
checked-in exact bootstrap distribution hashes
bootstrap evidence record digest
exact accepted source commit
```

### First accepted tooling lock

Before `tooling.txt` is trusted:

1. owner accepts generator image digest and platform;
2. bootstrap distribution identities/hashes are independently verified and
   checked in;
3. bootstrap tooling installs with `--require-hashes`;
4. generator creates `tooling/build/runtime/dev/browser`;
5. semantic parser validates versions, hashes, profile ownership and platform;
6. second regeneration compares byte-for-byte;
7. clean environments install all applicable profiles;
8. generator identity and all five locks are accepted atomically.

The trust claim therefore starts at immutable external generator/bootstrap
evidence, not at the lock produced by that generator.

### Controlled generator upgrade

1. previous accepted generator reproduces previous locks byte-for-byte;
2. candidate gets a new image digest, exact versions and bootstrap hashes;
3. previous accepted validator checks candidate evidence and rejects policy
   weakening;
4. candidate regenerates all five locks;
5. semantic/byte comparisons, graph review and clean installs pass;
6. candidate identity and five locks are accepted atomically.

### Rollback

Rollback restores from the previous accepted commit:

- all five locks;
- generator image digest;
- bootstrap manifest/evidence digest;
- regeneration/validation contract.

The restored generator must reproduce restored locks byte-for-byte and pass
clean installs before rollback evidence is accepted.

## 4. Installation rules

Conceptual fail-closed sequence:

```text
install bootstrap tooling from checked exact hashes
python -m pip install --require-hashes -r requirements/locks/tooling.txt
python -m pip install --require-hashes -r requirements/locks/build.txt
build wheel without network/build-isolation drift
python -m pip install --require-hashes -r requirements/locks/runtime.txt
python -m pip install --no-deps dist/electronic_operational_docs-<version>.whl
python -m pip check
```

Mandatory invariants:

1. no unbounded `pip install --upgrade pip setuptools wheel`;
2. no dependency resolution during final image assembly;
3. no install from `pyproject.toml` alone in CI/runtime;
4. all downloaded distributions have accepted hashes;
5. exact profile/Python/platform metadata is recorded;
6. clean environment does not rely on preinstalled packages.

## 5. Drift and source-completeness contract

Permanent validation rejects:

- direct dependency outside `pyproject.toml`;
- lock generated from another intent digest;
- changed range without all affected projections;
- non-exact lock version or missing hash;
- manual reorder/edit/truncation;
- package in wrong profile;
- build range absent from build lock;
- dev/browser package in runtime without accepted reason;
- wrong Python/platform profile;
- install bypassing `--require-hashes`;
- new applicable executable/config path absent from inventory source set/digests.

Source discovery is directory-independent across workflows, Dockerfiles,
Compose, shell, deploy/operator Python and Makefile/task/build files. Arbitrary
Markdown/JSON documentation/generated views are not executable sources. Any
future exclusion names one exact path and rationale; no broad directory
exemption is allowed.

## 6. Container reference contract

Every external image record contains logical owner, source path/line,
registry/repository, readable version, SHA-256 digest, scope, platform and update
evidence.

Local output is recognized only by proved owner:

- service `build:`;
- tracked Dockerfile/build target relationship;
- exact canonical local-output registry entry.

A tagless short name is not local evidence. Identical short name without its own
build owner remains external.

Validation rejects tag/tagless external reference without digest, digest without
readable metadata, conflicting owner, architecture mismatch and implicit build
input outside inventory.

## 7. GitHub Actions and external downloads

External Action/reusable workflow form:

```yaml
uses: owner/action@<40-character-commit-sha> # readable accepted release
```

Tags, branches, shortened SHA and missing readable metadata fail closed. Local
actions are bound to exact-head checkout.

`curl`, `wget`, installers and browser downloads require immutable source,
expected digest, verification before execution/extraction, constrained
destination and provenance inclusion. Direct pipe-to-interpreter is prohibited.
Local HTTP health checks are not external downloads.

## 8. Deterministic SPDX identity contract

SPDX 2.3 JSON retains mandatory `creationInfo.created`, deterministically rendered
from verified accepted build epoch (`SOURCE_DATE_EPOCH`, normally exact source
commit timestamp) as `YYYY-MM-DDTHH:MM:SSZ`. Runner wall clock is prohibited.

`documentNamespace` is derived from namespace-contract version, final image
digest, exact source commit and build-definition digest. Identical evidence gives
byte-identical payload; another image/build gets another namespace. Official
SPDX schema is pinned by digest and validated before publication.

## 9. Regeneration procedure

```text
clean exact-head checkout
digest-pinned generator environment
bootstrap tooling from checked-in exact hashes
regenerate tooling/build/runtime/dev/browser
semantic validation
byte-for-byte comparison
clean installation proof
build final artifact from immutable inputs
deterministic SPDX normalization and schema validation
secret-hygiene before publication
exact-head in-toto/SLSA provenance
all workflows on one final exact head
explicit owner acceptance before merge
```

## 10. Emergency update

Emergency shortens review latency, not controls. It retains issue/branch/Draft PR,
exact intent change, deterministic five-profile regeneration, hashes, clean
install/build/test, SBOM/provenance regeneration, secret-hygiene, rollback
evidence and explicit merge authority. Bots may propose changes later but cannot
auto-merge or become a second dependency owner.
