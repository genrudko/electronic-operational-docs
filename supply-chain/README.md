# Canonical supply-chain boundary

This directory is the machine-verifiable root for `DEPENDENCY-PROVENANCE-001`.

- `registry.json` owns immutable generator, image, Action, browser, schema, SBOM-tool and external-asset identities.
- `schema/spdx-2.3.schema.json` is the pinned official SPDX 2.3 JSON schema identified by the registry.
- Python direct intent remains owned only by `pyproject.toml`.
- Generated lock projections are stored under `requirements/locks/` and must not be edited manually.
- Controlled regeneration is performed by `scripts/dependency_provenance_implementation.py`; verification and artifact generation are performed by `scripts/dependency_provenance_contract.py`.
- Publication is prohibited until schema/boundary checks and Secret Hygiene have completed successfully.

A generated commit is not accepted merely because it was produced by the generator. The repository validators, byte-exact regeneration, clean hashed installations and exact-head workflows provide the acceptance evidence.
