# ADR — canonical dependency, SBOM and provenance architecture

## Status

`PROPOSED FOR PRODUCT-OWNER ACCEPTANCE`.

Этот ADR завершает inventory/decision-этап. Он не объявляет lock, digest pinning,
SBOM publication или attestation уже реализованными.

## Problem

Фактический проект использует стандартный Python packaging через
`pyproject.toml`, Docker/Compose и GitHub Actions. Прямой dependency intent
читаем, но транзитивное разрешение выполняется во время каждой установки.
Container images и Actions в текущем baseline заданы человекочитаемыми, но
mutable tags. Отдельного JavaScript package-management contour не обнаружено.

Нужно получить воспроизводимую supply-chain модель без второго владельца
зависимостей, без искусственного frontend toolchain и без внешнего SaaS.

## Decision

### 1. Python

- `pyproject.toml` остаётся **единственным владельцем читаемого direct intent**:
  runtime, development/test и browser extras, Python range и build backend.
- `pip-tools` (`pip-compile`) выбирается как **генератор**, а не второй package
  manager.
- Hash-locked files являются deterministic generated projections и вручную не
  редактируются.
- Планируемые lock profiles:
  - `build` — pinned installer/build tooling;
  - `runtime` — production/runtime graph;
  - `dev` — runtime + tests/quality tooling;
  - `browser` — runtime + Python Playwright contour.
- Installation использует `--require-hashes`; package installation из
  `pyproject.toml` без соответствующего lock в CI/container запрещается.
- Build isolation не может молча разрешать новый `setuptools`; build tooling
  сначала устанавливается из `build` lock, затем wheel строится без сетевого
  разрешения build dependencies.

### 2. JavaScript/browser/assets

- Отдельный npm/yarn/pnpm contour **не вводится**, пока в репозитории нет
  фактического JavaScript manifest/build graph.
- Python package `playwright` остаётся частью Python browser profile.
- Browser binaries считаются отдельным build/test input. Рекомендуемый сильный
  вариант — digest-pinned official browser-test image, согласованный с exact
  Playwright version. Download-on-run допустим только при доказанном browser
  revision, cache key, content digest и fail-closed verification.
- Внешние CSS/JS/font/icon resources должны быть repository-managed либо иметь
  immutable URL и integrity evidence. Generated static assets получают manifest
  с file digests и входят в provenance materials.

### 3. Containers

- Каждая внешняя image reference задаётся immutable digest.
- Читаемая версия сохраняется рядом как tag/comment, например концептуально:
  `image: vendor/name:18.4-bookworm@sha256:... # 18.4-bookworm`.
- Digest является исполняемым owner; comment/tag объясняет версию человеку.
- Final application image digest является deployment carrier identity.
- Build и runtime stages, если они будут разделены, имеют отдельные pinned base
  images и отражаются в provenance.

### 4. GitHub Actions

- Внешние `uses:` разрешаются только по 40-character commit SHA.
- Рядом обязателен readable release comment (`# v6`, `# v7` и т.п.).
- Local actions/reusable workflows разрешены только из exact-head checkout.
- Shell download не считается безопаснее `uses:` и проходит тот же integrity
  contract.

### 5. SBOM

- Канонический release SBOM: **SPDX 2.3 JSON** для final OCI image.
- Генератор: локально исполняемый/pinned open-source scanner (рекомендуется
  Syft в digest-pinned container) без внешнего SaaS.
- SBOM включает обнаруживаемые OS packages, Python packages, application
  package и их relationships.
- Repository source commit, lock digests, image digest и generated-asset
  manifest связываются через provenance; исходные файлы не маскируются под
  software packages.
- SBOM не является vulnerability scan и не доказывает отсутствие уязвимостей.

### 6. Build provenance

- Формат: in-toto Statement v1 с SLSA Provenance v1 predicate.
- Subject: final image/artifact digest.
- Materials: exact repository commit, workflow identity/digest, all lock files,
  Dockerfile/Compose inputs, pinned image/action identities, static manifest и
  SBOM digest.
- Preferred publication: GitHub artifact attestation after exact-head,
  secret-hygiene and artifact-content verification. Repository-owned statement
  остаётся проверяемой частью evidence и не зависит от UI.

### 7. Ordering

```text
exact-head checkout
→ canonical dependency validation
→ secret-hygiene scan
→ build from immutable inputs
→ runtime/static tests
→ SBOM generation
→ SBOM boundary validation
→ artifact/SBOM secret scan
→ provenance statement
→ attestation/publication
→ clean-tree verification
```

Publication до secret-hygiene verification запрещена.

## Options considered

| Option | Reproducibility | Hash support | Current-project fit | Owner burden | Vendor lock-in | External trust |
|---|---|---|---|---|---|---|
| `pip-tools` projections from `pyproject.toml` | High after implementation | Native pip hashes | Highest; keeps pip/setuptools | Moderate and familiar | Low | PyPI plus pinned tooling |
| `uv.lock` / uv installer | High | Strong lock/integrity model | Good technically, but introduces a new package manager/toolchain | Low after migration, higher migration cost | Moderate tool dependency | PyPI plus uv distribution |
| Poetry/PDM | High | Ecosystem-specific lock | Low; replaces existing packaging workflow | Higher conceptual burden | Moderate | Additional package-manager ecosystem |
| Hand-maintained pinned requirements | Superficially high | Possible | Compatible but unsafe operationally | High; drift-prone | Low | PyPI |

## Why `pip-tools`

Проще говоря: текущий проект уже говорит на языке `pip` и `pyproject.toml`.
`pip-tools` добавляет недостающий deterministic lock и hashes, но не заставляет
владельца системы осваивать второй способ установки и не переносит ownership из
`pyproject.toml`. Скорость `uv` привлекательна, но сейчас не компенсирует риск
смены package-management модели.

## Consequences

### Positive

- direct intent остаётся читаемым;
- transitive graph становится проверяемым;
- build/runtime/test profiles разделены без второго owner;
- Docker/Actions identity становится immutable;
- SBOM и provenance относятся к одному exact head и одному final artifact;
- решение не требует внешнего SaaS.

### Costs and limitations

- lock regeneration становится контролируемой процедурой, а не обычным
  `pip install`;
- Linux/architecture profile должен быть явно указан; новый platform требует
  отдельного доказанного lock/build profile;
- hosted-runner base environment остаётся внешней границей доверия, поэтому
  значимые tools переносятся в pinned containers или фиксируются как provenance
  inputs;
- availability registries и upstream compromise нельзя доказать одним lock;
- vulnerability status требует отдельного security pipeline.

## Rejected assumptions

- «Semver range достаточно для воспроизводимости» — неверно: transitive output
  меняется без изменения репозитория.
- «Tag с точной версией immutable» — неверно: registry tag может быть
  переназначен.
- «GitHub Action major tag безопасен, потому что официальный» — официальный
  owner не делает mutable ref immutable.
- «SBOM подтверждает безопасность» — SBOM только описывает состав.
