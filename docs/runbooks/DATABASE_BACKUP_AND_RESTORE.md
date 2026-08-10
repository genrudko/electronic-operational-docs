# ЭОД — backup, restore и DR PostgreSQL

## 1. Правило

Любая разрушительная migration, import, data transform или deployment с data impact начинается с verified recovery point.

Backup считается пригодным для восстановления только после проверки как минимум:

- файл существует и имеет ненулевой размер;
- `pg_restore --list` читает PostgreSQL custom-format dump;
- SHA-256 рассчитан и проверен до restore;
- restore выполнен в явно идентифицированную clean/disposable target database;
- migrations/system check и применимые integrity/data checks после restore успешны;
- результат зафиксирован non-secret restore certificate, который проходит verifier.

Сам факт существования `.dump` не является доказательством DR-готовности.

Backups никогда не хранятся в Git. Локальный путь `/srv/eod/backups` допускается как staging/операционный cache, но **не** удовлетворяет off-host requirement сам по себе.

## 2. Canonical repository drill

Единственный repository entry point для доказательного backup/restore drill:

```bash
python scripts/backup_restore_drill.py run ...
python scripts/backup_restore_drill.py verify-certificate ...
```

Acceptance path выполняется workflow:

```text
.github/workflows/backup-restore-drill.yml
```

Он использует только disposable PostgreSQL target и не предназначен для destructive restore live Preview/pilot/production. Restore target должен пройти fail-closed identity guard, быть создан чистым и иметь отдельную database identity. Имена `eod`, `eod_preview`, `eod_development` и `postgres`, source database и неявно/неоднозначно заданные targets запрещены для acceptance drill.

Raw `.dump` является transport material: он удаляется после drill и никогда не публикуется GitHub artifact. Публиковаться могут только прошедшие verifier non-secret certificate и его checksum.

## 3. Что фиксируется для recovery point

Для значимого recovery point фиксируются без секретов:

- contour/source class;
- database identity;
- repository/ref identity, где применимо;
- creation timestamp в операционном журнале/evidence;
- dump size;
- SHA-256;
- PostgreSQL/`pg_dump`/`pg_restore` versions;
- restore verification result и дата последней проверки;
- restore certificate reference для verified recovery point.

Не фиксируются в certificate/evidence:

- database password или DSN с credentials;
- Django secret;
- tokens/private keys;
- raw dump bytes;
- sensitive production records.

## 4. Preview dump

```bash
cd /srv/eod/repository
STAMP="$(date +%Y%m%d_%H%M%S)"
DUMP="/srv/eod/backups/eod_preview_${STAMP}.dump"

sudo docker compose \
  --env-file /srv/eod/secrets/preview.env \
  -f compose.preview.yaml \
  exec -T db \
  pg_dump --format=custom --no-owner --no-acl \
  --username eod_preview eod_preview \
  | sudo tee "$DUMP" >/dev/null

sudo test -s "$DUMP"
sudo stat -c '%s %n' "$DUMP"
sudo sha256sum "$DUMP"
```

Password не выводится: database container получает его из external environment. После создания значимого recovery point требуется перенести его в утверждённое off-host хранилище по защищённому каналу; локальный файл на том же VPS не считается отдельной копией.

## 5. Development dump

Предпочтительно использовать automation внутри `reset_development_database.sh`. Для отдельного dump применяются development env/compose и exact database/user `eod_development`.

Development backups не заменяют pilot/production recovery points и не входят автоматически в production retention.

## 6. Checksum и structural readability

До restore обязательны обе проверки:

```bash
sudo test -s /srv/eod/backups/<dump>.dump
sudo sha256sum /srv/eod/backups/<dump>.dump
```

и:

```bash
pg_restore --list /srv/eod/backups/<dump>.dump >/dev/null
```

Ожидаемый SHA-256 должен происходить из trusted recovery-point metadata/evidence. Вычислить checksum повреждённого файла заново и объявить его новым expected checksum нельзя.

## 7. Restore principles

- restore только в явно выбранную target database;
- Preview/pilot/production dump не восстанавливается поверх live database без отдельного incident/DR decision;
- acceptance drill всегда использует disposable clean target;
- normal preview-to-development restore выполняется только safe reset path;
- `--no-owner`/`--no-acl` используются для отделения source ownership от target role model;
- checksum проверяется **до** destructive restore operation;
- после restore применяются migrations target branch только там, где это архитектурно применимо;
- database identity проверяется до и после restore;
- representative object counts и safe integrity checks сравниваются с source evidence;
- readiness проверяется на restored database, когда это возможно без искусственной архитектуры;
- wrong, ambiguous, existing/non-clean или live target обязан fail closed.

## 8. Restore development from dump

Предпочтительный путь:

```bash
cd /srv/eod/development
sudo bash scripts/reset_development_database.sh
```

Для ручного incident restore сначала остановить development app, затем использовать target development db container. Точная команда зависит от recovery point и schema state и должна быть сформирована в incident work item, а не копироваться вслепую.

## 9. Post-restore verification

Обязательно, в зависимости от contour:

- `pg_restore --list` читает dump;
- file size non-zero;
- SHA-256 совпадает с expected recovery-point evidence;
- restore target identity подтверждена;
- clean target подтверждён до restore;
- PostgreSQL restore успешен;
- migrations success, если применимо;
- `python manage.py check`;
- database identity;
- representative object counts до/после;
- доступные safe domain/integrity checks;
- application readiness against restored database;
- live source contour остаётся неизменённым при disposable drill;
- non-secret restore certificate проходит independent verifier/checksum verification.

HTTP/UI проверки добавляются для pilot/production incident recovery только когда сервис реально поднят на восстановленной БД; CI drill не создаёт искусственную web-runtime архитектуру ради одного evidence point.

## 10. DR service objectives

Для текущего single-product PostgreSQL deployment приняты **target/SLO**, а не уже доказанные production guarantees:

```text
RPO target: <= 24 hours
RTO target: <= 4 hours
```

### RPO

Для pilot/production recovery point создаётся не реже одного раза в 24 часа. Дополнительно recovery point создаётся перед high-risk migration/data transform/release с data impact.

Backup interval не может быть больше заявленного RPO. Если фактическое расписание или off-host delivery не обеспечивает <=24 часа, RPO считается **не достигнутым**.

### RTO

Четырёхчасовой RTO начинается с момента подтверждения необходимости recovery и включает не только `pg_restore`, но и:

1. обнаружение/оценку инцидента и решение о восстановлении;
2. выбор последнего допустимого verified recovery point;
3. получение off-host copy;
4. provisioning/очистку target environment;
5. checksum/readability verification;
6. restore PostgreSQL;
7. migrations/system/integrity/readiness checks;
8. controlled возврат сервиса и operator verification.

Measured CI restore/drill duration является инженерным evidence работоспособности механизма, **не** доказательством production RTO. Production RTO может считаться доказанным только после pilot/production-like operational rehearsal.

## 11. Retention contract

Для pilot/production действует минимальная политика хранения:

```text
daily recovery points:   14 days
weekly recovery points:   8 weeks
monthly recovery points: 12 months
```

Требования:

- минимум **2 verified recovery points разных времён создания** должны быть доступны одновременно;
- минимум один verified recovery point должен укладываться в текущий RPO target;
- последний verified recovery point нельзя удалять до появления и проверки более нового;
- retention cleanup не имеет права удалять recovery point, если после удаления останется меньше двух verified points;
- failed/unverified backup не заменяет verified point и не разрешает удаление предшественника;
- legal/regulatory hold, если появится, имеет приоритет над обычным retention cleanup.

Эта repository policy определяет требование. Реальное enforcement lifecycle rules конкретного object storage должно быть проверено отдельно в pilot operations и не объявляется PASSED данным CI drill.

## 12. Off-host и failure-domain requirement

Pilot/production обязаны иметь минимум одну копию recovery point **вне VPS/host, где работает PostgreSQL**. Потеря application/database host не должна уничтожать все backups одновременно.

Допустимый backend выбирается deployment/operations решением (например, object storage или отдельное backup storage), но должен обеспечивать:

- отдельный failure domain;
- подтверждаемую загрузку и чтение backup;
- versioning/retention capability или эквивалентную защиту от ошибочного удаления;
- encryption at rest;
- authenticated encrypted transport;
- auditability операций доступа/удаления, насколько это поддерживает выбранная платформа.

`BACKUP-RESTORE-DRILL-001` не provision'ит реальный S3/object-storage account. Поэтому наличие off-host copy, production encryption и storage-side retention **deployment requirements**, а не PASSED evidence этого PR.

## 13. Encryption and transport

Для pilot/production:

- backup at rest хранится только на storage с включённым encryption at rest;
- передача на off-host storage выполняется только по TLS/SSH либо другому утверждённому authenticated encrypted channel;
- storage credentials, encryption keys/KMS identities и bucket/container locations не хранятся в Git;
- raw dump не передаётся через GitHub artifacts как способ backup storage;
- CI synthetic drill не использует production credentials/data.

Если encryption/off-host requirement нельзя доказать для выбранного deployment, соответствующий recovery point нельзя маркировать как production DR-compliant.

## 14. Access, restore and delete authority

Минимальное разделение полномочий:

- **Backup writer** — create/upload/list recovery points; без права массового удаления;
- **Restore operator** — read/download/restore approved recovery point; без retention-policy administration;
- **DR/storage administrator** — lifecycle/retention/delete administration по отдельному operational decision;
- **Incident/release owner** — разрешает destructive restore live target и фиксирует выбранный recovery point/target.

Удаление последнего verified recovery point запрещено независимо от роли. Production credentials выдаются по least privilege и хранятся вне Git.

## 15. Restore-verification cadence

Минимальная cadence:

- exact-head synthetic/disposable drill — при изменении canonical DR entry point, backup/restore workflow, PostgreSQL recovery tooling или DR runbook contract;
- перед pilot go-live — отдельный restore drill с выбранным pilot backup backend;
- после major PostgreSQL upgrade, смены backup backend, ключевой credential/encryption/storage policy или существенного migration mechanism — повторный drill;
- после начала pilot/production — минимум **1 restore verification в месяц** на изолированном target с off-host recovery point;
- каждый значимый incident recovery создаёт новый restore certificate/evidence.

Monthly off-host drill является будущим operational requirement и не считается выполненным synthetic GitHub Actions run.

## 16. Restore certificate

Machine-readable certificate должен содержать минимум:

- schema/version;
- source recovery-point class/identity без credentials;
- exact repository/ref identity, где применимо;
- dump SHA-256 и size;
- PostgreSQL/`pg_dump`/`pg_restore` versions;
- restore target class и non-secret database identity;
- target identity guard/clean-target result;
- checksum/readability result;
- measured restore duration;
- migrations/system/readiness result;
- representative counts/integrity result;
- RPO/RTO targets;
- measured total drill duration отдельно от RTO;
- cleanup result;
- overall PASS/FAIL.

Certificate verifier fail closed при schema drift, checksum mismatch, failed verification fields, invalid counts, попытке объявить CI duration production RTO или наличии запрещённых secret/raw fields.

## 17. Запрещено

- хранить raw dump в repository;
- публиковать raw dump GitHub artifact;
- восстанавливать на основании только похожего имени файла;
- смешивать Preview/development/pilot/production env;
- использовать restore без target identity check;
- восстанавливать в live/non-disposable target из acceptance drill;
- удалять последний verified recovery point;
- объявлять backup рабочим без restore verification;
- объявлять CI restore time доказанным production RTO;
- утверждать off-host/encryption/retention enforcement как PASSED без реального deployment evidence;
- подменять `MIGRATION-SAFETY-001` N-1/N/N-2 rehearsal или `RELEASE-ROLLBACK-001` этим backup/restore drill.
