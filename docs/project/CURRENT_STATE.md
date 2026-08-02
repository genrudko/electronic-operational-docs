# ЭОД — текущее состояние

**Дата factual check:** 02.08.2026

**Единственный владелец:** accepted main baseline, active work item/issue/PR/branch
и runtime state.

```text
repository: genrudko/electronic-operational-docs
accepted main baseline: main / 6e5171776cd6bc02fcbc45eb9532a6a0e58e15f0
active work item: PERSONNEL-AUTHORITY-001
active issue: #42
active PR: #43 / OPEN / DRAFT / NOT MERGED
active branch: feature/personnel-authority-001
runtime impact: FULL_DEVELOPMENT REBUILD PENDING IDENTITY CANDIDATE
preview: UNTOUCHED
```

`MASTER-DATA-ALIGNMENT-001` принят и merged commit
`b644048f1ec17e19e03c2e4fb538fc0cfc1f5feb`.

`NORMATIVE-EVIDENCE-001` принят и merged commit
`6e5171776cd6bc02fcbc45eb9532a6a0e58e15f0`.

`PERSONNEL-AUTHORITY-001` выполняется в issue #42 и Draft PR #43. Проверенные
этапы:

```text
PURE CONTRACT HEAD: 0200a2be6dfc5e948eb27dbed77d9e2aa39c0d4d / 5 workflows SUCCESS
PERSISTENCE HEAD: 4c65f3ab1d6631fa661c9ffba94443620a30e71a / 5 workflows SUCCESS
MATRIX HEAD: 60460f1d213e5a5afb080402a8efff16feec0af7 / 5 workflows SUCCESS
MANAGEMENT HEAD: d141313ac6e56fc442f08683a510e52df484564c / 5 workflows SUCCESS
REPAIR IMPLEMENTATION HEAD: 41bb2c1ba99decedf19fbc22dd2f25eed187dd2d / 5 workflows SUCCESS / 664 TESTS OK
DEPLOYED REPAIR HEAD: 9b7ede3a78997ebdbe7d68b750f024857369d4ea / DEVELOPMENT DEPLOYED / USER REJECTED VISUALLY
```

Trusted controller run `30733195542` deployed exact head
`9b7ede3a78997ebdbe7d68b750f024857369d4ea` to development with 664 VPS tests,
health-check and exact live SHA match. Preview remained `UNTOUCHED`.

После пользовательской проверки repair candidate принят не был. Фактические
причины следующего acceptance repair:

- current `Inter` declaration did not load a font asset and therefore normally
  fell back to the platform font;
- department pictograms mixed visual metaphors and decorative colored tiles;
- Direction A had no canonical icon grammar, symbol catalogue or typography
  scale, so feature CSS could improvise while formally remaining inside the
  high-level contract;
- personnel categories, entity icons, action icons and state markers were not
  separated into distinct semantic channels.

В текущий identity candidate включены:

- canonical Onest Variable interface font with a real pinned font face;
- EOD Outline 24 local SVG sprite based on one 24 px / 2 px round-stroke
  geometry;
- shared icon placement layer for shell, controls, module cards and dense trees;
- bare neutral department glyphs in the organization tree instead of colored
  decorative tiles;
- canonical mapping for navigation, journals, personnel, departments,
  equipment, ODU/RDU/CUS/DC and future modules;
- explicit rule that АТП/ОП/ОРП/РП, qualification, voltage and lifecycle remain
  text-first chips/markers rather than pictograms;
- canonical docs `ICONOGRAPHY_TYPOGRAPHY_CONTRACT_V1.md` and source tests;
- preserved source-bound document typography for registered OPJ/print forms.

Новые migrations отсутствуют. Product/domain models and lifecycle remain
untouched.

Новый exact head обязан пройти пять mandatory workflows, затем trusted
full-development rebuild and user visual acceptance. Until that proof the
previous deployed repair remains the live development state and the new runtime
impact is pending.

Merge, Ready for Review и preview write без отдельной команды пользователя
запрещены.

Release/module/capability/work-item planning state остаётся в
[`DEMO_RELEASE_PLAN.yaml`](DEMO_RELEASE_PLAN.yaml). Navigation без дублирования
volatile values остаётся в [`CURRENT_HANDOFF.md`](CURRENT_HANDOFF.md).
