# SBOM boundary specification

## Purpose

SBOM отвечает на вопрос **«из чего состоит принятый артефакт?»**. Она не
доказывает сама по себе, кто собрал артефакт, из какого commit он получен или
отсутствуют ли уязвимости. Эти доказательства принадлежат provenance и security
analysis.

## Canonical format

- format: SPDX 2.3 JSON;
- one canonical release SBOM per final OCI image digest;
- UTF-8 and normalized stable key/array ordering;
- mandatory `creationInfo.created` retained;
- deterministic canonical `documentNamespace`;
- SBOM file digest recorded in provenance;
- generator name/version/image digest recorded as creation information/material;
- no release SBOM is generated during the current architecture repair.

## Deterministic creationInfo.created

SPDX 2.3 requires `creationInfo.created`; the field is not removed to obtain
stable bytes.

Canonical rule:

1. build establishes accepted `SOURCE_DATE_EPOCH`;
2. workflow derives it from the exact source commit timestamp in Git metadata,
   unless another immutable epoch is explicitly accepted and recorded;
3. workflow verifies supplied `SOURCE_DATE_EPOCH` against that evidence;
4. normalizer renders exactly `YYYY-MM-DDTHH:MM:SSZ` in UTC;
5. runner wall-clock time, local timezone, fractional variability and current
   time APIs are prohibited inputs.

The validator fails under these rule IDs:

- `spdx-creation-info-created-required` — field missing;
- `spdx-created-build-epoch` — value not derived from accepted build epoch;
- `spdx-created-rfc3339-utc` — invalid/non-UTC canonical format.

## Deterministic documentNamespace

`documentNamespace` is a canonical absolute URI derived from:

```text
namespace contract version
+ final image sha256 digest
+ exact source commit
+ build-definition digest
```

The namespace must not contain a random UUID, runner identity or wall-clock
value. The SBOM digest itself is not an input because that would create a
circular hash. After normalization, provenance records both namespace and final
SBOM digest.

Required invariants:

- identical build evidence normalized twice produces byte-identical JSON;
- another image digest, exact source commit or build-definition digest produces
  another namespace;
- one namespace cannot be reused for a different final image/build identity.

The validator fails under:

- `spdx-document-namespace-deterministic`;
- `spdx-document-namespace-unique-subject`.

## Schema validation

The normalized document is validated before publication against a pinned,
checksum-verified official SPDX 2.3 JSON schema. Schema identity/digest is a
build material. A schema-invalid document fails `spdx-schema-valid` before
secret scanning, attestation or publication.

Validation order:

```text
normalize deterministic fields/order
→ validate deterministic timestamp and namespace
→ validate pinned SPDX 2.3 schema
→ validate image/package boundary
→ secret-hygiene scan and post-sanitization verification
→ record SBOM digest
→ provenance/attestation
→ publication
```

## Included boundary

The canonical image SBOM must include, where present and detectable:

1. final OCI image identity and digest;
2. operating-system distribution and installed OS packages;
3. Python interpreter/runtime identity;
4. installed Python runtime packages, including transitive packages;
5. application wheel/package and version;
6. package relationships (`DEPENDS_ON`, `CONTAINS`, or SPDX-equivalent);
7. package download/source identity and checksums where available;
8. licenses and package metadata where available without inventing missing data;
9. files intentionally copied as executable runtime components when represented
   as files rather than packages.

## Related provenance materials

These are mandatory evidence but are not falsely represented as software
packages:

- exact repository commit;
- `pyproject.toml` digest;
- `tooling`, `build`, `runtime`, `dev` and `browser` lock digests;
- generator image/bootstrap evidence digest;
- Dockerfile and relevant Compose/workflow digests;
- GitHub Action commit SHAs;
- base/service image digests;
- generated static-asset manifest and digest;
- migration set digest;
- build configuration/profile and build-definition digest;
- accepted build epoch;
- workflow run identity;
- final image/artifact digest.

## Browser/test SBOM

Browser-test tooling is not merged into the production runtime SBOM. A
pinned Playwright/browser image receives a separate test-tooling SBOM linked as
build material. Its packages/browsers are not claimed to be deployed in the EOD
runtime image.

## Database/proxy/service images

External runtime service images such as PostgreSQL or a future proxy are outside
the application image SBOM. Each requires a verified vendor SBOM for the exact
digest or a locally generated SBOM for that exact digest. Release evidence
contains a component-set manifest linking every service image and SBOM digest.

## Generated/static assets

`collectstatic` output is deployed content. A repository-owned normalized
manifest records:

```text
relative path
size
sha256
source category
```

The manifest is a provenance material and may be linked as an SPDX external
document/reference. External CDN content is prohibited unless inventory records
immutable identity and integrity evidence.

## Generation point and exact-head chain

SBOM is generated after final image construction and before deployment or
publication:

```text
build final image once
→ resolve final image digest
→ scan exact digest without rebuilding
→ normalize deterministic SPDX payload
→ schema and boundary validation
→ scan SBOM/artifact for credential-like content
→ record SBOM digest
→ create provenance/attestation
→ publish verified artifacts
```

A valid chain proves:

- checkout SHA equals event exact head;
- built image labels/materials contain that exact head;
- SBOM subject resolves to the same final image digest;
- deterministic timestamp/namespace inputs match provenance materials;
- no later rebuild occurs between SBOM generation and attestation.

## Completeness gates

Validation fails when:

- final image subject/digest is missing;
- mandatory `creationInfo.created` is absent or volatile;
- namespace is nondeterministic or reused for another build;
- document fails the pinned SPDX 2.3 schema;
- application package is absent;
- runtime-lock packages are absent;
- unexpected Python packages lack classification;
- OS inventory is empty for a normal non-`scratch` image;
- a runtime service image lacks linked SBOM evidence;
- static manifest is missing/stale;
- generator identity is absent;
- package relationships are absent;
- test-only packages enter production runtime;
- credential-like content appears.

## Sensitive-data exclusions

SBOM/provenance must not contain secret environment values, workflow tokens,
Django/PostgreSQL passwords, private registry credentials, connection strings
with secrets, private keys, raw logs, database content or user/domain data.
Names of standard packages, public registries, paths and non-secret keys are not
secret by themselves. Publication remains fail-closed after redaction and
`verify-sanitized` evidence.

## Known limitations

- scanner quality depends on package metadata support;
- correctly listed packages can still be vulnerable or malicious;
- registry availability and upstream build integrity remain external risks;
- vendor SBOM completeness may be unverifiable and must be stated as a bounded
  limitation;
- this contract does not claim byte-for-byte reproducible final OCI layers.
