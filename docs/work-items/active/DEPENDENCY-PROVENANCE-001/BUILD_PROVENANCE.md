# Build provenance specification

## Canonical statement

Build provenance is an in-toto Statement v1 using a SLSA Provenance v1
predicate. It is generated from workflow outputs, not manually written.

```text
subject.name: final EOD image/artifact
subject.digest.sha256: final immutable digest
predicate.buildDefinition.externalParameters: accepted non-secret build profile
predicate.buildDefinition.resolvedDependencies: immutable materials
predicate.runDetails.builder: GitHub workflow identity
predicate.runDetails.metadata: run identity and reproducibility metadata
```

## Exact-head invariant

The workflow establishes one exact head before any dependency installation:

1. expected SHA comes from `github.event.pull_request.head.sha` or accepted
   release/event SHA;
2. `actions/checkout` checks out that exact SHA with persisted credentials off;
3. `git rev-parse HEAD` must equal expected SHA;
4. dirty/untracked files are rejected before build;
5. all provenance subjects/materials are produced in that same job/workflow
   chain or passed by verified digests;
6. no rebuild is allowed after the subject digest is recorded.

The provenance source material uses the full 40-character commit and repository
URI. Branch names, PR numbers and human-entered report text are supplementary,
not identity.

## Required materials

- repository exact commit;
- workflow file path and SHA-256 digest as executed at exact head;
- `pyproject.toml` digest;
- every applicable lock-profile digest;
- lock generator/tooling identity and digest;
- Dockerfile and relevant Compose/build-config digests;
- all base/build/service image digests;
- all external GitHub Action commit SHAs;
- browser-test image/revision digest when applicable;
- generated-static manifest digest;
- source/build wheel digest;
- final OCI image digest;
- canonical SBOM digest;
- non-secret build parameters affecting output;
- runner OS/architecture and builder identity.

Mutable tags may be recorded as annotations for humans but never replace resolved
digests.

## Build outputs

A release/build evidence set is valid only when it forms this closed graph:

```text
exact repository commit
+ immutable lock/tool/action/image materials
→ wheel digest
→ final OCI image digest
→ SPDX SBOM digest
→ in-toto/SLSA provenance subject/material graph
→ verified attestation/publication
```

CI diagnostics, test logs and screenshots are evidence artifacts but are not the
release subject unless separately checksummed and declared.

## Credentials and sensitive values

Provenance may contain **parameter names** and non-secret profile identifiers,
but never secret values. The following are replaced by an explicit marker such
as `REDACTED_INPUT` or omitted according to schema:

- workflow secret values;
- authentication tokens;
- passwords and connection strings;
- private registry credentials;
- private keys/certificates;
- runtime domain/user data;
- raw environment dumps.

The existing secret-hygiene scanner runs on repository and candidate artifacts.
Sanitization is followed by verification; an unverified or partly redacted
artifact is not published.

## Permissions

The inventory stage changes no permissions. The implementation stage uses least
privilege:

- default `contents: read`;
- `id-token: write` and `attestations: write` only in the bounded attestation
  job when required;
- package write permission only when publishing an accepted image;
- no checkout credential persistence;
- no secrets passed to untrusted fork code or third-party actions.

Every external Action used for attestation/SBOM is pinned by commit SHA and
included as a material/dependency.

## Validation

Fail closed when:

- expected SHA and checked-out SHA differ;
- source commit is missing/short/mutable;
- provenance subject digest differs from built/published artifact;
- SBOM digest or subject differs;
- a resolved dependency uses a tag/branch without digest/SHA;
- workflow digest does not match exact-head workflow source;
- lock digest is absent or does not match checked-in canonical lock;
- provenance is generated before secret-hygiene completion;
- provenance contains credential-like content;
- subject is rebuilt after statement generation;
- materials omit an applicable runtime/build input;
- attestation verification fails;
- artifact or evidence comes from another workflow head.

## Reproducibility claim

The contract distinguishes:

- **input reproducibility** — all declared inputs are immutable and attributable;
- **dependency reproducibility** — exact graph/hashes install successfully;
- **build repeatability** — same inputs can build a functionally equivalent
  artifact;
- **byte-for-byte reproducibility** — only claimed after two independent builds
  prove identical digests.

This work item does not claim byte-for-byte reproducibility. Timestamps,
archive ordering, Python wheel metadata, filesystem layers and BuildKit metadata
must be normalized and independently tested before such a claim.

## Outside-repository limitations

- availability and retention of registry objects;
- integrity of upstream publisher build processes;
- GitHub-hosted runner platform internals;
- external DNS/network and registry authentication;
- vendor SBOM accuracy;
- organization-level repository/Actions settings.

These limitations are recorded in provenance/known limitations and addressed by
future security, deployment and release work items; they are not silently
presented as repository guarantees.
