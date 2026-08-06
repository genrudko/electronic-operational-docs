# Dependency/build inventory

> GENERATED VIEW из `scripts/dependency_provenance_inventory.py`. Ручное изменение отклоняется побайтной проверкой.

## Итог

- tracked files: `871`;
- inventory entries: `55`;
- floating inputs: `38`;
- immutable inputs: `16`;
- duplicate owner groups: `6`;
- conflicting owner groups: `3`;
- source files with dependency/build evidence: `16`.

## Контуры

- Python: pyproject=`True`, requirements=NONE, locks=NONE, hashed lock=`False`.
- JavaScript: package/lock files=NONE; separate frontend contour=`False`.
- Browser: Playwright declared=`True`; binary install operations=NONE; integrity contract=`False`.
- Containers: Dockerfiles=['Dockerfile', 'deploy/automation/Dockerfile.development']; Compose=['compose.development.yaml', 'compose.preview.yaml', 'compose.yaml', 'deploy/automation/compose.development.yaml'].
- GitHub Actions: workflows=`9`; temporary=NONE.
- External downloads: `0`; local runtime probes excluded=`True`.
- Static assets: tracked=`66`; external references=`1`.

## Totals by class

| Class | Count |
|---|---:|
| `container-image` | 7 |
| `container-output` | 1 |
| `external-asset` | 1 |
| `github-action` | 27 |
| `python-build` | 1 |
| `python-install` | 8 |
| `python-optional` | 3 |
| `python-runtime` | 6 |
| `python-transitive` | 1 |

## Inputs

| ID | Class | Path:line | Scope | Declaration | Immutable | Hash | Reproducibility | Risk | Proposed owner |
|---|---|---|---|---|---:|---|---|---|---|
| `INP-0001` | `container-image` | `.github/workflows/ci.yml:27` | ci | `postgres:18.4-bookworm` | no | absent | mutable-tag | HIGH | canonical container-image registry/reference contract |
| `INP-0002` | `container-image` | `Dockerfile:1` | build | `python:3.13-slim-bookworm` | no | absent | mutable-tag | HIGH | canonical container-image registry/reference contract |
| `INP-0003` | `container-image` | `compose.development.yaml:5` | runtime/test | `postgres:18.4-bookworm` | no | absent | mutable-tag | HIGH | canonical container-image registry/reference contract |
| `INP-0004` | `container-image` | `compose.preview.yaml:5` | runtime/test | `postgres:18.4-bookworm` | no | absent | mutable-tag | HIGH | canonical container-image registry/reference contract |
| `INP-0005` | `container-image` | `compose.yaml:3` | runtime/test | `postgres:18.4-bookworm` | no | absent | mutable-tag | HIGH | canonical container-image registry/reference contract |
| `INP-0006` | `container-image` | `deploy/automation/Dockerfile.development:1` | build | `python:3.13-slim-bookworm` | no | absent | mutable-tag | HIGH | canonical container-image registry/reference contract |
| `INP-0007` | `container-image` | `deploy/automation/compose.development.yaml:5` | runtime/test | `postgres:18.4-bookworm` | no | absent | mutable-tag | HIGH | canonical container-image registry/reference contract |
| `INP-0008` | `container-output` | `compose.development.yaml:26` | build-output | `eod-development-app` | no | absent | local-build-output | MEDIUM | final application image digest/build provenance |
| `INP-0009` | `external-asset` | `src/static/system/eod_typography.css:11` | browser/runtime | `https://cdn.jsdelivr.net/gh/simpals/onest@f18c06a14512e43a6191849278d6f07fdaf347d6/fonts/webfonts/Onest%5Bwght%5D.woff2` | yes | absent | immutable-url-no-integrity | MEDIUM | repository-managed asset or integrity-pinned registry |
| `INP-0010` | `github-action` | `.github/workflows/auto-001a-foundation-ci.yml:24` | ci/deployment | `actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803` | yes | commit-sha | immutable | LOW | each validated .github/workflows uses reference |
| `INP-0011` | `github-action` | `.github/workflows/auto-001a-foundation-ci.yml:39` | ci/deployment | `actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1` | yes | commit-sha | immutable | LOW | each validated .github/workflows uses reference |
| `INP-0012` | `github-action` | `.github/workflows/auto-001a-foundation-ci.yml:86` | ci/deployment | `actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a` | yes | commit-sha | immutable | LOW | each validated .github/workflows uses reference |
| `INP-0013` | `github-action` | `.github/workflows/auto-001b-controller-ci.yml:24` | ci/deployment | `actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803` | yes | commit-sha | immutable | LOW | each validated .github/workflows uses reference |
| `INP-0014` | `github-action` | `.github/workflows/auto-001b-controller-ci.yml:43` | ci/deployment | `actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1` | yes | commit-sha | immutable | LOW | each validated .github/workflows uses reference |
| `INP-0015` | `github-action` | `.github/workflows/auto-001b-controller-ci.yml:86` | ci/deployment | `actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a` | yes | commit-sha | immutable | LOW | each validated .github/workflows uses reference |
| `INP-0016` | `github-action` | `.github/workflows/ci.yml:58` | ci/deployment | `actions/checkout@v6` | no | absent | mutable-tag-or-branch | HIGH | each validated .github/workflows uses reference |
| `INP-0017` | `github-action` | `.github/workflows/ci.yml:73` | ci/deployment | `actions/setup-python@v6` | no | absent | mutable-tag-or-branch | HIGH | each validated .github/workflows uses reference |
| `INP-0018` | `github-action` | `.github/workflows/ci.yml:233` | ci/deployment | `actions/upload-artifact@v7` | no | absent | mutable-tag-or-branch | HIGH | each validated .github/workflows uses reference |
| `INP-0019` | `github-action` | `.github/workflows/ci.yml:272` | ci/deployment | `actions/checkout@v6` | no | absent | mutable-tag-or-branch | HIGH | each validated .github/workflows uses reference |
| `INP-0020` | `github-action` | `.github/workflows/ci.yml:372` | ci/deployment | `actions/upload-artifact@v7` | no | absent | mutable-tag-or-branch | HIGH | each validated .github/workflows uses reference |
| `INP-0021` | `github-action` | `.github/workflows/development-stack.yml:30` | ci/deployment | `actions/checkout@v6` | no | absent | mutable-tag-or-branch | HIGH | each validated .github/workflows uses reference |
| `INP-0022` | `github-action` | `.github/workflows/development-stack.yml:144` | ci/deployment | `actions/upload-artifact@v7` | no | absent | mutable-tag-or-branch | HIGH | each validated .github/workflows uses reference |
| `INP-0023` | `github-action` | `.github/workflows/documentation-contract.yml:24` | ci/deployment | `actions/checkout@v6` | no | absent | mutable-tag-or-branch | HIGH | each validated .github/workflows uses reference |
| `INP-0024` | `github-action` | `.github/workflows/documentation-contract.yml:40` | ci/deployment | `actions/setup-python@v6` | no | absent | mutable-tag-or-branch | HIGH | each validated .github/workflows uses reference |
| `INP-0025` | `github-action` | `.github/workflows/documentation-contract.yml:113` | ci/deployment | `actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a` | yes | commit-sha | immutable | LOW | each validated .github/workflows uses reference |
| `INP-0026` | `github-action` | `.github/workflows/eod-hot-refresh.yml:32` | ci/deployment | `actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803` | yes | commit-sha | immutable | LOW | each validated .github/workflows uses reference |
| `INP-0027` | `github-action` | `.github/workflows/eod-hot-refresh.yml:46` | ci/deployment | `actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1` | yes | commit-sha | immutable | LOW | each validated .github/workflows uses reference |
| `INP-0028` | `github-action` | `.github/workflows/eod-hot-refresh.yml:51` | ci/deployment | `actions/github-script@3a2844b7e9c422d3c10d287c895573f7108da1b3` | yes | commit-sha | immutable | LOW | each validated .github/workflows uses reference |
| `INP-0029` | `github-action` | `.github/workflows/eod-hot-refresh.yml:216` | ci/deployment | `actions/upload-artifact@v7` | no | absent | mutable-tag-or-branch | HIGH | each validated .github/workflows uses reference |
| `INP-0030` | `github-action` | `.github/workflows/secret-hygiene.yml:31` | ci/deployment | `actions/checkout@v6` | no | absent | mutable-tag-or-branch | HIGH | each validated .github/workflows uses reference |
| `INP-0031` | `github-action` | `.github/workflows/secret-hygiene.yml:47` | ci/deployment | `actions/setup-python@v6` | no | absent | mutable-tag-or-branch | HIGH | each validated .github/workflows uses reference |
| `INP-0032` | `github-action` | `.github/workflows/vps-development.yml:33` | ci/deployment | `actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803` | yes | commit-sha | immutable | LOW | each validated .github/workflows uses reference |
| `INP-0033` | `github-action` | `.github/workflows/vps-development.yml:48` | ci/deployment | `actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1` | yes | commit-sha | immutable | LOW | each validated .github/workflows uses reference |
| `INP-0034` | `github-action` | `.github/workflows/vps-development.yml:53` | ci/deployment | `actions/github-script@3a2844b7e9c422d3c10d287c895573f7108da1b3` | yes | commit-sha | immutable | LOW | each validated .github/workflows uses reference |
| `INP-0035` | `github-action` | `.github/workflows/vps-development.yml:195` | ci/deployment | `actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803` | yes | commit-sha | immutable | LOW | each validated .github/workflows uses reference |
| `INP-0036` | `github-action` | `.github/workflows/vps-development.yml:273` | ci/deployment | `actions/github-script@3a2844b7e9c422d3c10d287c895573f7108da1b3` | yes | commit-sha | immutable | LOW | each validated .github/workflows uses reference |
| `INP-0037` | `python-build` | `pyproject.toml` | build | `setuptools>=75` | no | absent | floating-range | HIGH | pyproject.toml [build-system.requires] |
| `INP-0038` | `python-install` | `.github/workflows/auto-001a-foundation-ci.yml:47` | ci/build/runtime tooling | `python -m pip install --upgrade pip setuptools wheel` | no | absent | not-proven | MEDIUM | canonical lock/download/image contract |
| `INP-0039` | `python-install` | `.github/workflows/auto-001a-foundation-ci.yml:48` | ci/build/runtime tooling | `python -m pip install --editable ".[dev]"` | no | absent | not-proven | MEDIUM | canonical lock/download/image contract |
| `INP-0040` | `python-install` | `.github/workflows/ci.yml:89` | ci/build/runtime tooling | `python -m pip install --upgrade pip setuptools wheel` | no | absent | not-proven | MEDIUM | canonical lock/download/image contract |
| `INP-0041` | `python-install` | `.github/workflows/ci.yml:90` | ci/build/runtime tooling | `python -m pip install --editable ".[dev]"` | no | absent | not-proven | MEDIUM | canonical lock/download/image contract |
| `INP-0042` | `python-install` | `.github/workflows/secret-hygiene.yml:63` | ci/build/runtime tooling | `python -m pip install --upgrade pip setuptools wheel` | no | absent | not-proven | MEDIUM | canonical lock/download/image contract |
| `INP-0043` | `python-install` | `.github/workflows/secret-hygiene.yml:64` | ci/build/runtime tooling | `python -m pip install --editable ".[dev]"` | no | absent | not-proven | MEDIUM | canonical lock/download/image contract |
| `INP-0044` | `python-install` | `Dockerfile:18` | ci/build/runtime tooling | `RUN python -m pip install --upgrade pip setuptools wheel \ && python -m pip install . \ && chmod 0755 /app/scripts/container-entrypoint.sh \ && mkdir -p /app/staticfiles \ && chown -R eod:eod /app/staticfiles` | no | absent | not-proven | MEDIUM | canonical lock/download/image contract |
| `INP-0045` | `python-install` | `deploy/automation/Dockerfile.development:15` | ci/build/runtime tooling | `RUN python -m pip install --upgrade pip setuptools wheel \ && python -m pip install . \ && mkdir -p /app/staticfiles \ && chown -R eod:eod /app/staticfiles` | no | absent | not-proven | MEDIUM | canonical lock/download/image contract |
| `INP-0046` | `python-optional` | `pyproject.toml` | dev | `coverage>=7.9,<8` | no | absent | floating-range | HIGH | pyproject.toml [project.optional-dependencies.dev] |
| `INP-0047` | `python-optional` | `pyproject.toml` | browser | `playwright>=1.54,<2` | no | absent | floating-range | HIGH | pyproject.toml [project.optional-dependencies.browser] |
| `INP-0048` | `python-optional` | `pyproject.toml` | dev | `ruff>=0.12,<1` | no | absent | floating-range | HIGH | pyproject.toml [project.optional-dependencies.dev] |
| `INP-0049` | `python-runtime` | `pyproject.toml` | runtime | `Django>=5.2,<5.3` | no | absent | floating-range | HIGH | pyproject.toml [project.dependencies] |
| `INP-0050` | `python-runtime` | `pyproject.toml` | runtime | `gunicorn>=26,<27` | no | absent | floating-range | HIGH | pyproject.toml [project.dependencies] |
| `INP-0051` | `python-runtime` | `pyproject.toml` | runtime | `openpyxl>=3.1,<4` | no | absent | floating-range | HIGH | pyproject.toml [project.dependencies] |
| `INP-0052` | `python-runtime` | `pyproject.toml` | runtime | `psycopg[binary]>=3.2,<4` | no | absent | floating-range | HIGH | pyproject.toml [project.dependencies] |
| `INP-0053` | `python-runtime` | `pyproject.toml` | runtime/build/test | `python` | no | not-applicable | partial-range-only | MEDIUM | pyproject.toml [project.requires-python] |
| `INP-0054` | `python-runtime` | `pyproject.toml` | runtime | `whitenoise>=6.12,<7` | no | absent | floating-range | HIGH | pyproject.toml [project.dependencies] |
| `INP-0055` | `python-transitive` | `pyproject.toml` | runtime/dev/browser/build | `pip dynamic resolver output` | no | absent | not-reproducible | CRITICAL | proposed generated hashed lock profiles |

## Duplicate owner groups

- `action:actions/checkout` — 10 conflicting references in .github/workflows/auto-001a-foundation-ci.yml, .github/workflows/auto-001b-controller-ci.yml, .github/workflows/ci.yml, .github/workflows/development-stack.yml, .github/workflows/documentation-contract.yml, .github/workflows/eod-hot-refresh.yml, .github/workflows/secret-hygiene.yml, .github/workflows/vps-development.yml.
- `action:actions/github-script` — 3 repeated references in .github/workflows/eod-hot-refresh.yml, .github/workflows/vps-development.yml.
- `action:actions/setup-python` — 7 conflicting references in .github/workflows/auto-001a-foundation-ci.yml, .github/workflows/auto-001b-controller-ci.yml, .github/workflows/ci.yml, .github/workflows/documentation-contract.yml, .github/workflows/eod-hot-refresh.yml, .github/workflows/secret-hygiene.yml, .github/workflows/vps-development.yml.
- `action:actions/upload-artifact` — 7 conflicting references in .github/workflows/auto-001a-foundation-ci.yml, .github/workflows/auto-001b-controller-ci.yml, .github/workflows/ci.yml, .github/workflows/development-stack.yml, .github/workflows/documentation-contract.yml, .github/workflows/eod-hot-refresh.yml.
- `image:postgres:18.4-bookworm` — 5 repeated references in .github/workflows/ci.yml, compose.development.yaml, compose.preview.yaml, compose.yaml, deploy/automation/compose.development.yaml.
- `image:python:3.13-slim-bookworm` — 2 repeated references in Dockerfile, deploy/automation/Dockerfile.development.

## Ограничения

- Network registries are not queried; future tag movement is outside repository evidence.
- No accepted transitive Python lock exists; clean resolution is not reproducible.
- Hosted-runner software and Docker/BuildKit versions remain external inputs.
- SBOM and provenance are specified but not emitted in this inventory-only stage.
- An SBOM is an inventory and does not prove absence of vulnerabilities.
