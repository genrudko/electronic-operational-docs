# Dependency/build inventory

> GENERATED VIEW из `scripts/dependency_provenance_inventory.py`. Ручное изменение отклоняется побайтной проверкой.

## Итог

- tracked files: `903`;
- inventory entries: `80`;
- floating inputs: `17`;
- immutable inputs: `62`;
- duplicate owner groups: `6`;
- conflicting owner groups: `0`;
- source files with dependency/build evidence: `20`;
- applicable executable/config sources: `69`;
- source completeness digests: `71`.

## Executable/config source completeness

- applicable paths: `69`;
- source kinds: `{'compose': 5, 'dockerfile': 3, 'github-workflow': 11, 'powershell': 3, 'python-operator': 38, 'shell': 8, 'shell-shebang': 1}`;
- uncovered paths: `NONE`;
- exact exclusions: `NONE`.

## Контуры

- Python: pyproject=`True`, requirements=NONE, locks=NONE, profiles=['tooling', 'build', 'runtime', 'dev', 'browser'], hashed lock=`False`.
- JavaScript: package/lock files=NONE; separate frontend contour=`False`.
- Browser: Playwright declared=`True`; binary install operations=NONE; integrity contract=`False`.
- Containers: Dockerfiles=['Dockerfile', 'deploy/automation/Dockerfile.development', 'supply-chain/Dockerfile.browser']; Compose=['compose.development.yaml', 'compose.preview.yaml', 'compose.production.yaml', 'compose.yaml', 'deploy/automation/compose.development.yaml'].
- GitHub Actions: workflows=`11`; temporary=NONE.
- External downloads: `0`; local runtime probes excluded=`True`.
- Static assets: tracked=`66`; external references=`1`.

## Totals by class

| Class | Count |
|---|---:|
| `container-image` | 11 |
| `container-output` | 1 |
| `external-asset` | 1 |
| `github-action` | 34 |
| `python-build` | 1 |
| `python-install` | 22 |
| `python-optional` | 3 |
| `python-runtime` | 6 |
| `python-transitive` | 1 |

## Inputs

| ID | Class | Path:line | Scope | Declaration | Immutable | Hash | Reproducibility | Risk | Proposed owner |
|---|---|---|---|---|---:|---|---|---|---|
| `INP-0001` | `container-image` | `.github/workflows/ci.yml:27` | ci | `postgres@sha256:882236b897e39051d2368c5ccc6cda944904723506b2dfc97f2a8f5bc9afa382` | yes | sha256-digest | immutable | LOW | canonical container-image registry/reference contract |
| `INP-0002` | `container-image` | `.github/workflows/dependency-provenance.yml:30` | ci | `postgres@sha256:882236b897e39051d2368c5ccc6cda944904723506b2dfc97f2a8f5bc9afa382` | yes | sha256-digest | immutable | LOW | canonical container-image registry/reference contract |
| `INP-0003` | `container-image` | `Dockerfile:1` | build | `python@sha256:67a1e1f215ccda113cfc024e8639049257e88f273898f595b61476d128d387e8` | yes | sha256-digest | immutable | LOW | canonical container-image registry/reference contract |
| `INP-0004` | `container-image` | `Dockerfile:12` | build | `python@sha256:67a1e1f215ccda113cfc024e8639049257e88f273898f595b61476d128d387e8` | yes | sha256-digest | immutable | LOW | canonical container-image registry/reference contract |
| `INP-0005` | `container-image` | `compose.development.yaml:5` | runtime/test | `postgres@sha256:882236b897e39051d2368c5ccc6cda944904723506b2dfc97f2a8f5bc9afa382` | yes | sha256-digest | immutable | LOW | canonical container-image registry/reference contract |
| `INP-0006` | `container-image` | `compose.preview.yaml:5` | runtime/test | `postgres@sha256:882236b897e39051d2368c5ccc6cda944904723506b2dfc97f2a8f5bc9afa382` | yes | sha256-digest | immutable | LOW | canonical container-image registry/reference contract |
| `INP-0007` | `container-image` | `compose.production.yaml:5` | runtime/test | `postgres@sha256:882236b897e39051d2368c5ccc6cda944904723506b2dfc97f2a8f5bc9afa382` | yes | sha256-digest | immutable | LOW | canonical container-image registry/reference contract |
| `INP-0008` | `container-image` | `compose.yaml:3` | runtime/test | `postgres@sha256:882236b897e39051d2368c5ccc6cda944904723506b2dfc97f2a8f5bc9afa382` | yes | sha256-digest | immutable | LOW | canonical container-image registry/reference contract |
| `INP-0009` | `container-image` | `deploy/automation/Dockerfile.development:1` | build | `python@sha256:67a1e1f215ccda113cfc024e8639049257e88f273898f595b61476d128d387e8` | yes | sha256-digest | immutable | LOW | canonical container-image registry/reference contract |
| `INP-0010` | `container-image` | `deploy/automation/compose.development.yaml:5` | runtime/test | `postgres@sha256:882236b897e39051d2368c5ccc6cda944904723506b2dfc97f2a8f5bc9afa382` | yes | sha256-digest | immutable | LOW | canonical container-image registry/reference contract |
| `INP-0011` | `container-image` | `supply-chain/Dockerfile.browser:1` | build | `mcr.microsoft.com/playwright/python@sha256:678457c4c323b981d8b4befc57b95366bb1bb6aa30057b1269f6b171e8d9975a` | yes | sha256-digest | immutable | LOW | canonical container-image registry/reference contract |
| `INP-0012` | `container-output` | `compose.development.yaml:26` | build-output | `eod-development-app` | no | absent | local-build-output | MEDIUM | final application image digest/build provenance |
| `INP-0013` | `external-asset` | `src/static/system/eod_typography.css:11` | browser/runtime | `https://cdn.jsdelivr.net/gh/simpals/onest@f18c06a14512e43a6191849278d6f07fdaf347d6/fonts/webfonts/Onest%5Bwght%5D.woff2` | yes | absent | immutable-url-no-integrity | MEDIUM | repository-managed asset or integrity-pinned registry |
| `INP-0014` | `github-action` | `.github/workflows/auto-001a-foundation-ci.yml:24` | ci/deployment | `actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803` | yes | commit-sha | immutable | LOW | each validated .github/workflows uses reference |
| `INP-0015` | `github-action` | `.github/workflows/auto-001a-foundation-ci.yml:39` | ci/deployment | `actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1` | yes | commit-sha | immutable | LOW | each validated .github/workflows uses reference |
| `INP-0016` | `github-action` | `.github/workflows/auto-001a-foundation-ci.yml:90` | ci/deployment | `actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a` | yes | commit-sha | immutable | LOW | each validated .github/workflows uses reference |
| `INP-0017` | `github-action` | `.github/workflows/auto-001b-controller-ci.yml:24` | ci/deployment | `actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803` | yes | commit-sha | immutable | LOW | each validated .github/workflows uses reference |
| `INP-0018` | `github-action` | `.github/workflows/auto-001b-controller-ci.yml:43` | ci/deployment | `actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1` | yes | commit-sha | immutable | LOW | each validated .github/workflows uses reference |
| `INP-0019` | `github-action` | `.github/workflows/auto-001b-controller-ci.yml:86` | ci/deployment | `actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a` | yes | commit-sha | immutable | LOW | each validated .github/workflows uses reference |
| `INP-0020` | `github-action` | `.github/workflows/ci.yml:58` | ci/deployment | `actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803` | yes | commit-sha | immutable | LOW | each validated .github/workflows uses reference |
| `INP-0021` | `github-action` | `.github/workflows/ci.yml:73` | ci/deployment | `actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1` | yes | commit-sha | immutable | LOW | each validated .github/workflows uses reference |
| `INP-0022` | `github-action` | `.github/workflows/ci.yml:236` | ci/deployment | `actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a` | yes | commit-sha | immutable | LOW | each validated .github/workflows uses reference |
| `INP-0023` | `github-action` | `.github/workflows/ci.yml:275` | ci/deployment | `actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803` | yes | commit-sha | immutable | LOW | each validated .github/workflows uses reference |
| `INP-0024` | `github-action` | `.github/workflows/ci.yml:375` | ci/deployment | `actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a` | yes | commit-sha | immutable | LOW | each validated .github/workflows uses reference |
| `INP-0025` | `github-action` | `.github/workflows/dependency-provenance.yml:61` | ci/deployment | `actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803` | yes | commit-sha | immutable | LOW | each validated .github/workflows uses reference |
| `INP-0026` | `github-action` | `.github/workflows/dependency-provenance.yml:81` | ci/deployment | `actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1` | yes | commit-sha | immutable | LOW | each validated .github/workflows uses reference |
| `INP-0027` | `github-action` | `.github/workflows/dependency-provenance.yml:384` | ci/deployment | `actions/attest@508db95dd578ae2727ebd6217d5ba78e4fbda05d` | yes | commit-sha | immutable | LOW | each validated .github/workflows uses reference |
| `INP-0028` | `github-action` | `.github/workflows/dependency-provenance.yml:498` | ci/deployment | `actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a` | yes | commit-sha | immutable | LOW | each validated .github/workflows uses reference |
| `INP-0029` | `github-action` | `.github/workflows/dependency-provenance.yml:508` | ci/deployment | `actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a` | yes | commit-sha | immutable | LOW | each validated .github/workflows uses reference |
| `INP-0030` | `github-action` | `.github/workflows/deployment-profile.yml:54` | ci/deployment | `actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803` | yes | commit-sha | immutable | LOW | each validated .github/workflows uses reference |
| `INP-0031` | `github-action` | `.github/workflows/deployment-profile.yml:207` | ci/deployment | `actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a` | yes | commit-sha | immutable | LOW | each validated .github/workflows uses reference |
| `INP-0032` | `github-action` | `.github/workflows/development-stack.yml:30` | ci/deployment | `actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803` | yes | commit-sha | immutable | LOW | each validated .github/workflows uses reference |
| `INP-0033` | `github-action` | `.github/workflows/development-stack.yml:144` | ci/deployment | `actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a` | yes | commit-sha | immutable | LOW | each validated .github/workflows uses reference |
| `INP-0034` | `github-action` | `.github/workflows/documentation-contract.yml:24` | ci/deployment | `actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803` | yes | commit-sha | immutable | LOW | each validated .github/workflows uses reference |
| `INP-0035` | `github-action` | `.github/workflows/documentation-contract.yml:40` | ci/deployment | `actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1` | yes | commit-sha | immutable | LOW | each validated .github/workflows uses reference |
| `INP-0036` | `github-action` | `.github/workflows/documentation-contract.yml:113` | ci/deployment | `actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a` | yes | commit-sha | immutable | LOW | each validated .github/workflows uses reference |
| `INP-0037` | `github-action` | `.github/workflows/eod-hot-refresh.yml:32` | ci/deployment | `actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803` | yes | commit-sha | immutable | LOW | each validated .github/workflows uses reference |
| `INP-0038` | `github-action` | `.github/workflows/eod-hot-refresh.yml:46` | ci/deployment | `actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1` | yes | commit-sha | immutable | LOW | each validated .github/workflows uses reference |
| `INP-0039` | `github-action` | `.github/workflows/eod-hot-refresh.yml:51` | ci/deployment | `actions/github-script@3a2844b7e9c422d3c10d287c895573f7108da1b3` | yes | commit-sha | immutable | LOW | each validated .github/workflows uses reference |
| `INP-0040` | `github-action` | `.github/workflows/eod-hot-refresh.yml:216` | ci/deployment | `actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a` | yes | commit-sha | immutable | LOW | each validated .github/workflows uses reference |
| `INP-0041` | `github-action` | `.github/workflows/secret-hygiene.yml:31` | ci/deployment | `actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803` | yes | commit-sha | immutable | LOW | each validated .github/workflows uses reference |
| `INP-0042` | `github-action` | `.github/workflows/secret-hygiene.yml:47` | ci/deployment | `actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1` | yes | commit-sha | immutable | LOW | each validated .github/workflows uses reference |
| `INP-0043` | `github-action` | `.github/workflows/vps-development.yml:33` | ci/deployment | `actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803` | yes | commit-sha | immutable | LOW | each validated .github/workflows uses reference |
| `INP-0044` | `github-action` | `.github/workflows/vps-development.yml:48` | ci/deployment | `actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1` | yes | commit-sha | immutable | LOW | each validated .github/workflows uses reference |
| `INP-0045` | `github-action` | `.github/workflows/vps-development.yml:53` | ci/deployment | `actions/github-script@3a2844b7e9c422d3c10d287c895573f7108da1b3` | yes | commit-sha | immutable | LOW | each validated .github/workflows uses reference |
| `INP-0046` | `github-action` | `.github/workflows/vps-development.yml:195` | ci/deployment | `actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803` | yes | commit-sha | immutable | LOW | each validated .github/workflows uses reference |
| `INP-0047` | `github-action` | `.github/workflows/vps-development.yml:273` | ci/deployment | `actions/github-script@3a2844b7e9c422d3c10d287c895573f7108da1b3` | yes | commit-sha | immutable | LOW | each validated .github/workflows uses reference |
| `INP-0048` | `python-build` | `pyproject.toml` | build | `setuptools>=75` | no | absent | floating-range | HIGH | pyproject.toml [build-system.requires] |
| `INP-0049` | `python-install` | `.github/workflows/auto-001a-foundation-ci.yml:47` | ci/build/runtime tooling | `python -m pip install --disable-pip-version-check --require-hashes -r requirements/locks/tooling.txt` | yes | inline-or-associated-evidence | integrity-evidenced | MEDIUM | canonical lock/download/image contract |
| `INP-0050` | `python-install` | `.github/workflows/auto-001a-foundation-ci.yml:48` | ci/build/runtime tooling | `python -m pip install --disable-pip-version-check --require-hashes -r requirements/locks/build.txt` | yes | inline-or-associated-evidence | integrity-evidenced | MEDIUM | canonical lock/download/image contract |
| `INP-0051` | `python-install` | `.github/workflows/auto-001a-foundation-ci.yml:49` | ci/build/runtime tooling | `python -m pip install --disable-pip-version-check --require-hashes -r requirements/locks/dev.txt` | yes | inline-or-associated-evidence | integrity-evidenced | MEDIUM | canonical lock/download/image contract |
| `INP-0052` | `python-install` | `.github/workflows/auto-001a-foundation-ci.yml:51` | ci/build/runtime tooling | `python -m pip install --disable-pip-version-check --no-deps dist/*.whl` | no | absent | not-proven | MEDIUM | canonical lock/download/image contract |
| `INP-0053` | `python-install` | `.github/workflows/ci.yml:89` | ci/build/runtime tooling | `python -m pip install --disable-pip-version-check --require-hashes -r requirements/locks/tooling.txt` | yes | inline-or-associated-evidence | integrity-evidenced | MEDIUM | canonical lock/download/image contract |
| `INP-0054` | `python-install` | `.github/workflows/ci.yml:90` | ci/build/runtime tooling | `python -m pip install --disable-pip-version-check --require-hashes -r requirements/locks/build.txt` | yes | inline-or-associated-evidence | integrity-evidenced | MEDIUM | canonical lock/download/image contract |
| `INP-0055` | `python-install` | `.github/workflows/ci.yml:91` | ci/build/runtime tooling | `python -m pip install --disable-pip-version-check --require-hashes -r requirements/locks/dev.txt` | yes | inline-or-associated-evidence | integrity-evidenced | MEDIUM | canonical lock/download/image contract |
| `INP-0056` | `python-install` | `.github/workflows/ci.yml:93` | ci/build/runtime tooling | `python -m pip install --disable-pip-version-check --no-deps dist/*.whl` | no | absent | not-proven | MEDIUM | canonical lock/download/image contract |
| `INP-0057` | `python-install` | `.github/workflows/dependency-provenance.yml:99` | ci/build/runtime tooling | `python -m pip install --disable-pip-version-check --require-hashes -r requirements/locks/tooling.txt` | yes | inline-or-associated-evidence | integrity-evidenced | MEDIUM | canonical lock/download/image contract |
| `INP-0058` | `python-install` | `.github/workflows/dependency-provenance.yml:100` | ci/build/runtime tooling | `python -m pip install --disable-pip-version-check --require-hashes -r requirements/locks/build.txt` | yes | inline-or-associated-evidence | integrity-evidenced | MEDIUM | canonical lock/download/image contract |
| `INP-0059` | `python-install` | `.github/workflows/dependency-provenance.yml:101` | ci/build/runtime tooling | `python -m pip install --disable-pip-version-check --require-hashes -r requirements/locks/dev.txt` | yes | inline-or-associated-evidence | integrity-evidenced | MEDIUM | canonical lock/download/image contract |
| `INP-0060` | `python-install` | `.github/workflows/dependency-provenance.yml:146` | ci/build/runtime tooling | `python -m pip install --disable-pip-version-check --no-deps dist/electronic_operational_docs-0.1.0-py3-none-any.whl` | no | absent | not-proven | MEDIUM | canonical lock/download/image contract |
| `INP-0061` | `python-install` | `.github/workflows/secret-hygiene.yml:63` | ci/build/runtime tooling | `python -m pip install --disable-pip-version-check --require-hashes -r requirements/locks/tooling.txt` | yes | inline-or-associated-evidence | integrity-evidenced | MEDIUM | canonical lock/download/image contract |
| `INP-0062` | `python-install` | `.github/workflows/secret-hygiene.yml:64` | ci/build/runtime tooling | `python -m pip install --disable-pip-version-check --require-hashes -r requirements/locks/build.txt` | yes | inline-or-associated-evidence | integrity-evidenced | MEDIUM | canonical lock/download/image contract |
| `INP-0063` | `python-install` | `.github/workflows/secret-hygiene.yml:65` | ci/build/runtime tooling | `python -m pip install --disable-pip-version-check --require-hashes -r requirements/locks/dev.txt` | yes | inline-or-associated-evidence | integrity-evidenced | MEDIUM | canonical lock/download/image contract |
| `INP-0064` | `python-install` | `.github/workflows/secret-hygiene.yml:67` | ci/build/runtime tooling | `python -m pip install --disable-pip-version-check --no-deps dist/*.whl` | no | absent | not-proven | MEDIUM | canonical lock/download/image contract |
| `INP-0065` | `python-install` | `Dockerfile:6` | ci/build/runtime tooling | `RUN python -m pip install --disable-pip-version-check --require-hashes \ -r requirements/locks/build.txt` | yes | inline-or-associated-evidence | integrity-evidenced | MEDIUM | canonical lock/download/image contract |
| `INP-0066` | `python-install` | `Dockerfile:17` | ci/build/runtime tooling | `RUN python -m pip install --disable-pip-version-check --require-hashes \ -r requirements/locks/runtime.txt` | yes | inline-or-associated-evidence | integrity-evidenced | MEDIUM | canonical lock/download/image contract |
| `INP-0067` | `python-install` | `Dockerfile:20` | ci/build/runtime tooling | `RUN mkdir -p /app/src \ && python -m pip install --disable-pip-version-check --no-deps --target /app/src /tmp/eod/*.whl \ && rm -rf /tmp/eod` | no | absent | not-proven | MEDIUM | canonical lock/download/image contract |
| `INP-0068` | `python-install` | `deploy/automation/Dockerfile.development:6` | ci/build/runtime tooling | `RUN python -m pip install --disable-pip-version-check --require-hashes \ -r requirements/locks/build.txt \ && python -m pip install --disable-pip-version-check --require-hashes \ -r requirements/locks/dev.txt` | yes | inline-or-associated-evidence | integrity-evidenced | MEDIUM | canonical lock/download/image contract |
| `INP-0069` | `python-install` | `deploy/automation/Dockerfile.development:12` | ci/build/runtime tooling | `RUN python -m build --wheel --no-isolation --outdir /tmp/eod-wheel \ && python -m pip install --disable-pip-version-check --no-deps /tmp/eod-wheel/*.whl \ && rm -rf /tmp/eod-wheel` | no | absent | not-proven | MEDIUM | canonical lock/download/image contract |
| `INP-0070` | `python-install` | `supply-chain/Dockerfile.browser:10` | ci/build/runtime tooling | `RUN python -m pip install --disable-pip-version-check --require-hashes \ -r /evidence/requirements/locks/browser.txt \ && python -m pip check` | yes | inline-or-associated-evidence | integrity-evidenced | MEDIUM | canonical lock/download/image contract |
| `INP-0071` | `python-optional` | `pyproject.toml` | dev | `coverage>=7.9,<8` | no | absent | floating-range | HIGH | pyproject.toml [project.optional-dependencies.dev] |
| `INP-0072` | `python-optional` | `pyproject.toml` | browser | `playwright>=1.54,<2` | no | absent | floating-range | HIGH | pyproject.toml [project.optional-dependencies.browser] |
| `INP-0073` | `python-optional` | `pyproject.toml` | dev | `ruff>=0.12,<1` | no | absent | floating-range | HIGH | pyproject.toml [project.optional-dependencies.dev] |
| `INP-0074` | `python-runtime` | `pyproject.toml` | runtime | `Django>=5.2,<5.3` | no | absent | floating-range | HIGH | pyproject.toml [project.dependencies] |
| `INP-0075` | `python-runtime` | `pyproject.toml` | runtime | `gunicorn>=26,<27` | no | absent | floating-range | HIGH | pyproject.toml [project.dependencies] |
| `INP-0076` | `python-runtime` | `pyproject.toml` | runtime | `openpyxl>=3.1,<4` | no | absent | floating-range | HIGH | pyproject.toml [project.dependencies] |
| `INP-0077` | `python-runtime` | `pyproject.toml` | runtime | `psycopg[binary]>=3.2,<4` | no | absent | floating-range | HIGH | pyproject.toml [project.dependencies] |
| `INP-0078` | `python-runtime` | `pyproject.toml` | runtime/build/test | `python` | no | not-applicable | partial-range-only | MEDIUM | pyproject.toml [project.requires-python] |
| `INP-0079` | `python-runtime` | `pyproject.toml` | runtime | `whitenoise>=6.12,<7` | no | absent | floating-range | HIGH | pyproject.toml [project.dependencies] |
| `INP-0080` | `python-transitive` | `pyproject.toml` | tooling/build/runtime/dev/browser | `pip dynamic resolver output` | no | absent | not-reproducible | CRITICAL | proposed generated hashed lock profiles |

## Duplicate owner groups

- `action:actions/checkout` — 12 repeated references in .github/workflows/auto-001a-foundation-ci.yml, .github/workflows/auto-001b-controller-ci.yml, .github/workflows/ci.yml, .github/workflows/dependency-provenance.yml, .github/workflows/deployment-profile.yml, .github/workflows/development-stack.yml, .github/workflows/documentation-contract.yml, .github/workflows/eod-hot-refresh.yml, .github/workflows/secret-hygiene.yml, .github/workflows/vps-development.yml.
- `action:actions/github-script` — 3 repeated references in .github/workflows/eod-hot-refresh.yml, .github/workflows/vps-development.yml.
- `action:actions/setup-python` — 8 repeated references in .github/workflows/auto-001a-foundation-ci.yml, .github/workflows/auto-001b-controller-ci.yml, .github/workflows/ci.yml, .github/workflows/dependency-provenance.yml, .github/workflows/documentation-contract.yml, .github/workflows/eod-hot-refresh.yml, .github/workflows/secret-hygiene.yml, .github/workflows/vps-development.yml.
- `action:actions/upload-artifact` — 10 repeated references in .github/workflows/auto-001a-foundation-ci.yml, .github/workflows/auto-001b-controller-ci.yml, .github/workflows/ci.yml, .github/workflows/dependency-provenance.yml, .github/workflows/deployment-profile.yml, .github/workflows/development-stack.yml, .github/workflows/documentation-contract.yml, .github/workflows/eod-hot-refresh.yml.
- `image:postgres` — 7 repeated references in .github/workflows/ci.yml, .github/workflows/dependency-provenance.yml, compose.development.yaml, compose.preview.yaml, compose.production.yaml, compose.yaml, deploy/automation/compose.development.yaml.
- `image:python` — 3 repeated references in Dockerfile, deploy/automation/Dockerfile.development.

## Ограничения

- Network registries are not queried; future tag movement is outside repository evidence.
- No accepted transitive Python lock exists; clean resolution is not reproducible.
- Hosted-runner software and Docker/BuildKit versions remain external inputs.
- SBOM and provenance are specified but not emitted in this inventory-only stage.
- An SBOM is an inventory and does not prove absence of vulnerabilities.
