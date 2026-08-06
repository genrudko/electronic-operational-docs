# SBOM boundary specification

## Purpose

SBOM отвечает на вопрос **«из чего состоит принятый артефакт?»**. Она не
отвечает сама по себе на вопросы «кто его собрал?», «из какого commit?» и «нет
ли в нём уязвимостей?». Эти вопросы относятся соответственно к provenance и
security analysis.

## Canonical format

- format: SPDX 2.3 JSON;
- one canonical release SBOM per final OCI image digest;
- UTF-8, normalized stable ordering, no volatile timestamp in the byte-compared
  canonical payload;
- SBOM file digest recorded in provenance;
- generator name/version/image digest recorded as creation information/material.

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
9. files intentionally copied as executable runtime components when the scanner
   represents them as files rather than packages.

## Related but not falsely represented as packages

The following are mandatory provenance/material evidence but are not all SBOM
packages:

- exact repository commit;
- `pyproject.toml` and lock-file digests;
- Dockerfile and relevant Compose/workflow digests;
- GitHub Action commit SHAs;
- base/service image digests;
- generated static-asset manifest and digest;
- migration set digest;
- build configuration/profile;
- workflow run identity;
- final image/artifact digest.

## Browser/test SBOM

Browser-test tooling is not silently merged into the production runtime SBOM.
If a digest-pinned Playwright/browser image is used, it receives a separate
**test-tooling SBOM** linked as a build material. Its packages/browsers are not
claimed to be deployed in the final EOD runtime image.

## Database/proxy/service images

External runtime service images such as PostgreSQL or a future proxy are not
inside the application image SBOM. They require one of:

- vendor/provided SBOM linked to the exact digest and verified; or
- locally generated image SBOM for that exact digest.

Deployment/release evidence contains a component-set manifest linking the app
image plus every service image digest and SBOM digest.

## Generated/static assets

`collectstatic` output is part of the deployed application content. A
repository-owned manifest records for every generated file:

```text
relative path
size
sha256
source category
```

The manifest itself is a provenance material and may be attached as an SPDX
external document/reference. External CDN content is prohibited unless the
inventory records immutable identity and integrity evidence.

## Generation point

SBOM is generated **after** final image construction and **before** publication
or deployment:

```text
build final image
→ resolve final image digest
→ scan exact digest without rebuilding
→ normalize and validate SBOM
→ scan SBOM/artifact for credential-like content
→ record SBOM digest
→ create provenance/attestation
→ publish verified artifacts
```

Generating from the source tree or from a different local environment does not
satisfy the release boundary.

## Exact-head linkage

The SBOM payload/filename must not rely on a human-entered SHA. Provenance
records the SBOM digest and subject image digest, and the build workflow proves:

- checkout SHA equals event exact head;
- built image labels/materials contain that exact head;
- SBOM subject resolves to the same final image digest;
- no later rebuild occurs between SBOM generation and attestation.

A validator rejects SBOM evidence where commit/image/SBOM digests do not form
one closed chain.

## Completeness gates

At minimum, validation fails when:

- final image subject/digest is missing;
- application package is absent;
- Python runtime dependencies expected from the runtime lock are absent;
- unexpected installed Python packages are present without classification;
- OS package inventory is empty for a non-`scratch`/non-distroless image;
- a declared runtime service image lacks linked SBOM evidence;
- generated-static manifest is missing or refers to another build;
- SBOM generator identity is absent;
- package relationships are absent;
- test-only packages are silently included in production runtime;
- credentials, tokens, connection strings or private keys appear in artifact.

## Sensitive-data exclusions

SBOM/provenance must not contain:

- environment variable values;
- `GITHUB_TOKEN` or other workflow credentials;
- Django/PostgreSQL/demo passwords;
- private registry credentials;
- internal connection strings with secrets;
- private keys/certificates;
- raw logs, database content or user/domain data;
- source file contents unrelated to package identification.

Names of standard packages, public registries, repository paths and non-secret
configuration keys are not secret by themselves. Redaction is followed by the
existing `verify-sanitized`/artifact-content gate; publication is fail-closed.

## Known limitations

- SBOM quality depends on scanner support and package metadata.
- A package may be vulnerable even when correctly listed.
- A package may be malicious without a known advisory.
- Registry availability, upstream build integrity and future digest availability
  remain external dependencies.
- Proprietary/vendor SBOM completeness may be unverifiable; this is recorded as
  a limitation, not silently treated as complete.
