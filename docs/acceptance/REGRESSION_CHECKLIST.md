# ЭОД — regression checklist

Чек-лист применяется перед значимой пользовательской приёмкой и milestone release. Неприменимые пункты отмечаются `N/A` с объяснением.

## Environment

- [ ] exact branch and HEAD recorded;
- [ ] worktree clean;
- [ ] app and db healthy;
- [ ] correct database identity;
- [ ] health endpoint success;
- [ ] main page HTTP 200;
- [ ] presentation reset/data state recorded;
- [ ] preview remains healthy while development is tested.

## Authentication and organization

- [ ] `operator.demo` login;
- [ ] `supervisor.demo` login;
- [ ] logout and session expiration behavior;
- [ ] current organization/workplace correct;
- [ ] role-dependent actions differ as expected;
- [ ] no cross-organization data leakage.

## Navigation and UI

- [ ] Russian-only end-user UI;
- [ ] light/dark theme critical screens readable;
- [ ] density/text-size preferences do not break layout;
- [ ] navigation back/forward preserves expected state;
- [ ] no system codes/hashes in normal mode;
- [ ] validation messages visible and understandable;
- [ ] mobile/narrow viewport critical route usable.

## Equipment and personnel selection

- [ ] search works with Cyrillic case variations;
- [ ] pagination/filtering preserves selection;
- [ ] selected values belong to current organization/workplace;
- [ ] aliases do not replace canonical dispatch name incorrectly;
- [ ] ЩПТ/ШОТ equipment family behavior correct;
- [ ] employee/role labels are unambiguous.

## Document core

- [ ] create draft;
- [ ] create new version;
- [ ] registration assigns correct number;
- [ ] registered content immutable;
- [ ] canonical snapshot created;
- [ ] integrity status correct;
- [ ] legacy item not falsely signed;
- [ ] relations and audit visible;
- [ ] prohibited physical deletion blocked.

## Operational log

- [ ] chronology correct;
- [ ] event time differs from registration time where required;
- [ ] omitted/late entry represented explicitly;
- [ ] correction/annulment preserves original;
- [ ] caret starts at expected position;
- [ ] Ctrl+Left/Right/Home/End stay in current entry;
- [ ] PgUp/PgDown do not scroll whole page unexpectedly;
- [ ] equipment/document semantic link editable;
- [ ] copy/paste does not duplicate link icon;
- [ ] click outside editor does not jump page;
- [ ] search finds Cyrillic text independent of case;
- [ ] template/abbreviation behavior, if in scope.

## Structured forms

- [ ] manual arbitrary type creation absent;
- [ ] technical schema cannot create work records;
- [ ] source document/section/appendix visible;
- [ ] field order and required flags match source;
- [ ] empty additional rows ignored;
- [ ] multiple selection searchable and clickable;
- [ ] transition comment hint clear;
- [ ] invalid transition denied;
- [ ] history and source binding preserved.

## Cross-document relations

- [ ] operational record ↔ defect;
- [ ] application → disposition;
- [ ] work ↔ permit/disposition;
- [ ] switching document ↔ application/disposition/log;
- [ ] broken/deleted relation does not erase historical snapshot;
- [ ] timeline ordering correct where implemented.

## Data/import

- [ ] raw and normalized values retained;
- [ ] conflicts not silently resolved;
- [ ] repeated import behavior understood;
- [ ] publication separate from staging;
- [ ] six ambiguous workplace documentation rows remain controlled;
- [ ] real sensitive data absent.

## Infrastructure

- [ ] preview on `127.0.0.1:8765`;
- [ ] development on `127.0.0.1:8766`;
- [ ] PostgreSQL host ports unpublished;
- [ ] database names/users distinct;
- [ ] development reset does not change preview;
- [ ] SSH tunnel works;
- [ ] logs contain no secrets.

## Documentation

- [ ] README current;
- [ ] current state and handoff current;
- [ ] baseline SHA consistent;
- [ ] module map updated;
- [ ] open items updated;
- [ ] decision/acceptance history updated;
- [ ] internal links pass gate;
- [ ] PR evidence complete.

## Result

```text
exact head:
date:
contour:
data state:
passed:
failed:
N/A:
blocking defects:
follow-up:
user decision:
```