# Build provenance specification

## Canonical statement

Build provenance is an in-toto Statement v1 using a SLSA Provenance v1
predicate. It is generated from verified workflow outputs, not manually written.

```text
subject.name: final EOD image/artifact
subject.digest.sha256: final immutable digest
predicate.buildDefinition.externalParameters: accepted non-secret build profile
predicate.buildDefinition.resolvedDependencies: immutable materials
predicate.runDetails.builder: GitHub workflow identity
predicate.runDetails.metadata: run identity and reproducibility metadata
```

## Exact-head invariant

1. expected SHA comes from PR head or accepted release/event SHA;
2. checkout uses that exact SHA with persisted credentials off;
3. `git rev-parse HEAD` equals expected SHA;
4. dirty/untracked files are rejected before build;
5. all subjects/materials stay in the same verified digest chain;
6. no rebuild occurs after subject digest is recorded.

Full commit and repository URI are identity. Branch, PR number and report text are
supplementary metadata.

## Required materials

- repository exact commit;
- workflow path and SHA-256 digest as executed;
- `pyproject.toml` digest;
- `requirements/locks/tooling.txt` digest;
- `requirements/locks/build.txt` digest;
- `requirements/locks/runtime.txt` digest;
- `requirements/locks/dev.txt` digest;
- `requirements/locks/browser.txt` digest;
- digest-pinned generator OCI identity;
- bootstrap manifest/evidence digest and exact tool versions;
- Dockerfile and relevant Compose/build-config digests;
- all base/build/service image digests;
- all external GitHub Action commit SHAs;
- browser-test image/revision digest when applicable;
- generated-static manifest digest;
- wheel digest;
- final OCI image digest;
- canonical SPDX 2.3 namespace and SBOM digest;
- accepted `SOURCE_DATE_EPOCH` and its exact source evidence;
- SPDX namespace-contract and build-definition digests;
- non-secret build parameters affecting output;
- runner OS/architecture and builder identity.

Mutable tags may be annotations but never replace resolved digests.

## Deterministic SBOM linkage

Provenance proves that:

- `creationInfo.created` was derived from verified accepted build epoch, not
  runner wall clock;
- normalized UTC value is canonical `YYYY-MM-DDTHH:MM:SSZ`;
- `documentNamespace` was derived from namespace-contract version, final image
  digest, exact source commit and build-definition digest;
- repeated normalization of identical evidence is byte-identical;
- another image/build cannot reuse the namespace;
- the pinned official SPDX 2.3 schema validated before publication;
- final SBOM digest belongs to that normalized payload.

The SBOM digest is not used to derive its own namespace; provenance closes that
link after normalization and avoids circular identity.

## Closed evidence graph

```text
exact repository commit
+ accepted generator/bootstrap evidence
+ tooling/build/runtime/dev/browser lock digests
+ immutable tool/action/image materials
+ accepted build epoch/build definition
→ wheel digest
→ final OCI image digest
→ deterministic SPDX namespace and SBOM digest
→ in-toto/SLSA subject/material graph
→ verified attestation/publication
```

## Credentials and publication order

Provenance may contain parameter names/profile identifiers, never secret values.
Tokens, passwords, secret connection strings, registry credentials, private
keys, runtime domain/user data and raw environment dumps are omitted or marked
according to schema without exposing values.

Publication order is fail-closed:

```text
exact-head and clean-tree proof
→ build/normalization/schema/boundary validation
→ repository and candidate-artifact secret scan
→ post-redaction verification
→ provenance generation
→ attestation verification
→ publication
```

## Permissions

The inventory repair changes no permissions. Future attestation uses default
`contents: read`; `id-token: write`/`attestations: write` only in a bounded job;
package write only when publishing an accepted image; no checkout credential
persistence; no secret exposure to untrusted code. Every external Action is full
commit SHA and provenance material.

## Fail-closed validation

Reject when expected/checked-out SHA differ; source is mutable/short; subject
mismatches artifact; any of five lock digests or bootstrap evidence is absent;
image/Action material is mutable; workflow digest differs; timestamp/namespace
is volatile, malformed or reused; schema validation fails; provenance precedes
secret-hygiene; credential-like content appears; subject is rebuilt; applicable
material is omitted; attestation verification fails; or evidence belongs to
another head.

## Reproducibility claim

The contract distinguishes immutable input identity, exact dependency graph,
functionally repeatable build and byte-for-byte reproducibility. This stage does
not claim byte-identical final wheels/OCI layers. That claim requires two
independent builds with identical digests after timestamp/archive/layer metadata
normalization.

## Outside-repository limitations

Registry retention/availability, upstream publisher build integrity,
GitHub-hosted runner internals, DNS/network/authentication, vendor SBOM accuracy
and organization-level settings remain external boundaries. They are recorded,
not presented as repository guarantees.
