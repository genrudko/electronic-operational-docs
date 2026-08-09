# ADR — canonical dependency, SBOM and provenance architecture

## Status

`PROPOSED FOR PRODUCT-OWNER ACCEPTANCE AFTER BOUNDED REPAIR`.

Этот ADR завершает inventory/architecture-decision этап. Он не объявляет уже
реализованными production locks, digest migration, SBOM publication,
provenance publication или attestation.

## Problem

Фактический проект использует Python packaging через `pyproject.toml`, `pip`,
Docker/Compose и GitHub Actions. Прямой dependency intent читаем, но
транзитивное разрешение выполняется во время установки. Внешние container images
и часть Actions используют mutable refs. Отдельного JavaScript package-management
contour не обнаружено.

Архитектура должна дать воспроизводимый supply-chain contract без второго
владельца Python intent, без искусственного frontend toolchain, без внешнего
SaaS и без circular trust для lock generator.

## Decision

### 1. Python ownership and five projections

- `pyproject.toml` остаётся **единственным владельцем читаемого direct Python
  intent**: Python range, build backend, runtime, development/test и browser
  extras.
- Python installation сохраняет модель `pip`.
- `pip-tools` (`pip-compile`) используется как deterministic **generator**, а не
  второй package manager и не второй intent owner.
- Канонический список lock projections один во всех документах:

```text
requirements/locks/tooling.txt
requirements/locks/build.txt
requirements/locks/runtime.txt
requirements/locks/dev.txt
requirements/locks/browser.txt
```

- `tooling` — generator/bootstrap tooling;
- `build` — wheel build frontend/backend;
- `runtime` — production transitive graph;
- `dev` — runtime плюс tests/quality tooling;
- `browser` — runtime плюс Python Playwright contour.

Locks являются generated projections, содержат exact versions и SHA-256 hashes,
не редактируются вручную и устанавливаются с `--require-hashes`. Build isolation
не может молча разрешить другой `setuptools` или иной build dependency.

### 2. Non-circular tooling bootstrap root of trust

`tooling.txt` **не считается доверенным только потому, что он сгенерировал сам
себя**. Root of trust находится вне candidate tooling lock и состоит из
одновременно принятых evidence:

1. digest-pinned generator OCI environment;
2. exact Python minor/platform;
3. exact bootstrap `pip` and `pip-tools` versions;
4. checked-in bootstrap manifest с exact distribution identities и SHA-256
   hashes;
5. digest bootstrap evidence record и exact accepted source commit.

Первый accepted tooling lock создаётся так:

```text
owner-accepted generator image digest
+ independently verified bootstrap distribution hashes
→ install bootstrap tooling with --require-hashes
→ generate tooling/build/runtime/dev/browser
→ semantic validation
→ byte-for-byte regeneration comparison
→ clean installation proof
→ atomic owner acceptance of generator identity and all five locks
```

Таким образом первый tooling lock выводится из заранее принятого immutable
bootstrap evidence, а не из собственного содержимого.

Controlled generator upgrade:

1. прежний accepted generator воспроизводит прежние пять locks и подтверждает
   byte-identical baseline;
2. candidate generator получает новый image digest, exact tool versions и
   independently verified bootstrap hashes;
3. прежний accepted validator проверяет candidate bootstrap manifest, format,
   profile set и запрет ослабления hash policy;
4. candidate generator создаёт все пять candidate locks;
5. выполняются semantic validation, byte comparison, clean installs и review
   полного graph diff;
6. новый generator identity и пять locks принимаются атомарно.

Rollback восстанавливает из предыдущего accepted commit одновременно:

- прежние пять locks;
- прежний generator image digest;
- прежний bootstrap manifest/evidence digest;
- прежний regeneration contract.

После rollback прежний generator обязан снова получить byte-identical locks и
успешный clean-install proof.

### 3. JavaScript/browser/assets

- npm/yarn/pnpm **не вводятся**, пока нет фактического JavaScript manifest/build
  graph.
- Python package `playwright` остаётся в `browser` profile.
- Browser binaries являются отдельным immutable build/test input. Предпочтителен
  digest-pinned browser-test image, согласованный с exact Playwright version.
- External CSS/JS/font/icon resources должны быть repository-managed либо иметь
  immutable identity и integrity evidence.
- Generated static assets получают normalized path/size/SHA-256 manifest,
  связанный provenance.

### 4. Executable/config source completeness

Dependency/build operation discovery выполняется по всем tracked применимым
sources независимо от каталога:

- `.github/workflows/**/*.yml|yaml`;
- Dockerfiles;
- Compose files;
- `**/*.sh`, `**/*.bash`, применимые PowerShell scripts;
- Makefile/task/build files;
- extensionless shell entrypoints по shebang;
- deploy/operator/build Python sources по пути, executable/shebang, имени или
  фактическому external-process call.

Произвольные documentation и generated JSON/Markdown files не считаются
executable sources. Любое исключение допускается только как exact path с
rationale. Generated inventory хранит полный applicable-path set и digest
каждого source, поэтому новый применимый tracked path не может исчезнуть молча.

### 5. Containers and local-output ownership

- Каждая внешняя OCI image reference в implementation stage закрепляется
  immutable digest; readable tag/version сохраняется рядом.
- Tagless reference не является локальной по форме имени.
- `image: postgres`, `image: postgres:18.4-bookworm` — external mutable inputs
  без digest.
- `image: postgres@sha256:...` — external immutable input.
- Local build output признаётся только при доказанном owner: service `build:`,
  tracked Dockerfile/build target или exact canonical local-output registry.
- Одинаковое short name без собственного build evidence не наследует local
  classification от другого service.
- Final application image digest является deployment carrier identity.

### 6. GitHub Actions and downloads

- External `uses:` разрешаются только по full 40-character commit SHA.
- Рядом обязателен readable release comment.
- Local actions/reusable workflows привязаны к exact-head checkout.
- Shell downloads проходят тот же immutable source/digest contract.
- Network response нельзя pipe directly в shell/interpreter.
- Local HTTP health probe не классифицируется как external download.

### 7. Deterministic SPDX 2.3 JSON

Canonical release SBOM — **SPDX 2.3 JSON** для final OCI image digest.
Обязательное поле `creationInfo.created` сохраняется.

Deterministic timestamp contract:

- accepted build epoch задаётся `SOURCE_DATE_EPOCH`;
- workflow проверяет, что epoch равен exact source commit timestamp, полученному
  из Git metadata, либо другому явно принятому immutable build epoch;
- runner wall-clock time запрещён;
- JSON value нормализуется в UTC RFC 3339 form `YYYY-MM-DDTHH:MM:SSZ`;
- invalid/non-UTC/fractionally variable timestamp отклоняется.

Deterministic `documentNamespace` создаётся из immutable tuple:

```text
namespace contract version
+ final image sha256 digest
+ exact source commit
+ build-definition digest
```

Namespace является canonical absolute URI. Random UUID, runner identity и
wall-clock time запрещены. Один и тот же build evidence после повторной
normalization даёт byte-identical payload. Другой image digest, source commit
или build-definition digest обязан дать другой namespace. SBOM digest не входит
в namespace input, чтобы не создавать circular hash; provenance связывает уже
нормализованный namespace с final SBOM digest.

SPDX JSON проходит pinned official SPDX 2.3 schema validation **до** secret scan,
attestation и publication. Реальная release SBOM на этом repair-этапе не
генерируется.

Рекомендуемый generator остаётся локально исполняемым digest-pinned open-source
tool (например, Syft) без внешнего SaaS.

### 8. Build provenance

- Формат: in-toto Statement v1 + SLSA Provenance v1 predicate.
- Subject: final image/artifact digest.
- Materials: exact repository commit, workflow digest, all five lock digests,
  generator/bootstrap identity, Docker/Compose inputs, image/action identities,
  static manifest, SBOM digest and non-secret build parameters.
- Publication разрешена только после exact-head proof, schema/boundary checks,
  secret-hygiene и artifact-content verification.

### 9. Ordering

```text
exact-head checkout
→ source/inventory completeness
→ digest-pinned generator bootstrap from checked exact hashes
→ regenerate tooling/build/runtime/dev/browser
→ semantic and byte-for-byte lock validation
→ clean installation proof
→ secret-hygiene scan
→ build from immutable inputs
→ runtime/static tests
→ deterministic SPDX generation and schema validation
→ SBOM boundary validation
→ artifact/SBOM secret scan
→ in-toto/SLSA provenance
→ attestation/publication
→ clean-tree verification
```

## Preserved decisions

- `pyproject.toml` is sole direct Python intent owner;
- `pip-tools` is generator, not package manager owner;
- installation remains `pip`;
- no npm/yarn/pnpm contour;
- exactly five lock projections;
- external OCI digest pinning;
- full Action SHA pinning;
- SPDX 2.3 JSON;
- in-toto/SLSA provenance;
- secret-hygiene-before-publication;
- no external SaaS.

## Consequences and limitations

- lock regeneration becomes controlled supply-chain work;
- platform profile is explicit;
- hosted-runner internals remain an external boundary, so relevant tools are
  moved to pinned environments or recorded as provenance inputs;
- registry availability/upstream compromise are not solved by one lock;
- SBOM is inventory, not vulnerability proof;
- byte-for-byte build reproducibility is not claimed until independently proven.
