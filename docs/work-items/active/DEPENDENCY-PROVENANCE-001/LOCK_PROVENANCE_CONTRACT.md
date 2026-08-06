# Canonical dependency/lock/provenance contract

## 1. Ownership

| Information | Single owner |
|---|---|
| Direct Python intent and supported ranges | `pyproject.toml` |
| Exact resolved Python graphs and hashes | generated lock profiles |
| Lock generation logic/tool versions | repository regeneration script + tooling lock |
| Container image identity | image registry file/validated Docker and Compose references |
| GitHub Action identity | each validated workflow `uses:` reference |
| Final artifact identity | OCI/artifact digest emitted by exact-head build |
| SBOM identity | SBOM digest linked to final artifact |
| Provenance identity | in-toto/SLSA statement and attestation |

Generated files never become a second intent owner. A direct dependency may be
added, removed or relaxed only in `pyproject.toml`; every affected lock projection
must then be regenerated.

## 2. Proposed lock profiles

```text
requirements/locks/tooling.txt
requirements/locks/build.txt
requirements/locks/runtime.txt
requirements/locks/dev.txt
requirements/locks/browser.txt
```

All files are generated with normalized ordering, exact versions and
`--hash=sha256:` records. Headers record:

- generator and exact generator version;
- canonical input path(s);
- target Python minor;
- target OS/architecture profile;
- exact regeneration command;
- no timestamp or machine-specific path.

### Tooling

Contains the pinned `pip`, `pip-tools` and supporting packages used to compile
other locks. Bootstrap installation uses hashes. Tooling cannot update itself
implicitly.

### Build

Contains exact build frontend/backend requirements needed to create the wheel.
The build process does not permit PEP 517 isolated environment to contact the
network and resolve a different `setuptools`.

### Runtime

Contains the complete transitive graph for the production application. Final
container installation uses this profile and the already-built application
wheel; it does not resolve `pyproject.toml` ranges.

### Development

Contains runtime plus `[dev]` tooling. It is the owner for CI Ruff/tests and
approved local development gates, not production runtime.

### Browser

Contains runtime plus Python Playwright dependencies. Browser binary/image
identity is separate and must be compatible with the exact Playwright package.
No `package.json` is created solely for Playwright.

## 3. Installation rules

Fail-closed commands conceptually follow:

```text
python -m pip install --require-hashes -r requirements/locks/tooling.txt
python -m pip install --require-hashes -r requirements/locks/build.txt
build wheel without network/build isolation drift
python -m pip install --require-hashes -r requirements/locks/runtime.txt
python -m pip install --no-deps dist/electronic_operational_docs-<version>.whl
python -m pip check
```

Implementation may refine command shape, but these invariants are mandatory:

1. no unbounded `pip install --upgrade pip setuptools wheel`;
2. no dependency resolution during final image assembly;
3. no install from `pyproject.toml` alone in CI/runtime;
4. all downloaded Python distributions covered by accepted hashes;
5. exact profile and Python/platform metadata recorded;
6. clean environment and no preinstalled-package reliance.

## 4. Drift contract

The permanent validator rejects:

- direct dependency present outside `pyproject.toml`;
- lock generated from different direct intent;
- changed direct version/range without all affected lock updates;
- lock line without exact version;
- missing/invalid hash;
- manually reordered, edited or partially regenerated lock;
- dependency appearing in wrong profile;
- build-system range not represented in the build profile;
- runtime graph containing dev-only/browser-only tools without an explicit
  accepted reason;
- lock generated for a different Python/platform profile;
- install command that bypasses `--require-hashes`.

The regeneration command runs in check mode in CI and compares generated files
byte-for-byte. Semantic validation also parses package/version/hash records so a
malformed file cannot pass merely by matching a stale checksum manifest.

## 5. Container reference contract

Every external image record contains:

```text
logical owner
source path and line
registry/repository
human-readable tag/version
sha256 digest
scope: build/runtime/test
architecture/platform
update evidence reference
```

Validation rejects:

- tag without digest;
- digest without readable version metadata;
- digest change without registry metadata update;
- same logical image owned by conflicting declarations;
- architecture mismatch;
- implicit pull of a build stage not represented in inventory.

## 6. GitHub Actions contract

Each external action/reusable workflow uses:

```yaml
uses: owner/action@<40-character-commit-sha> # vX.Y.Z or accepted readable release
```

Validation rejects tags, branches, shortened SHAs and omitted readable version
metadata. Local actions are bound to exact-head checkout and may not fetch
unverified executables.

## 7. External download contract

`curl`, `wget`, installers and browser downloads require all of:

- HTTPS or another explicitly accepted authenticated transport;
- immutable source/version;
- expected SHA-256 or stronger digest stored in canonical metadata;
- verification before execution/extraction;
- destination constrained to build workspace;
- license/source traceability where applicable;
- inventory/SBOM/provenance inclusion appropriate to the artifact.

Piping a network response directly to a shell/interpreter is prohibited.

## 8. Regeneration procedure

1. Start from clean exact `main` and a bounded issue/branch/Draft PR.
2. Change direct intent only in `pyproject.toml` or approved image/action metadata.
3. Build the digest-pinned lock-generation environment.
4. Regenerate every affected profile without manual edits.
5. Review direct and transitive diff; explain removals, additions and downgrades.
6. Verify hashes and clean-environment installation.
7. Build final artifact from immutable inputs.
8. Generate SBOM and compare boundary/completeness.
9. Run secret-hygiene before artifact publication.
10. Generate exact-head provenance and applicable attestations.
11. Run all applicable workflows on one exact head.
12. Obtain explicit owner acceptance before merge.

## 9. Emergency dependency update

Emergency does not mean uncontrolled. The expedited path may shorten review
latency, but it does not remove:

- issue/branch/Draft PR traceability;
- exact direct-intent change;
- deterministic lock regeneration;
- hashes;
- clean install/build/test;
- SBOM/provenance regeneration;
- secret-hygiene;
- rollback evidence;
- explicit merge authority.

The emergency record additionally states advisory/incident ID, affected
versions, chosen fixed version, residual risk, rollback point and follow-up
review deadline. Dependabot or another bot may propose a change later, but
cannot auto-merge or become a second dependency owner.
