# ЭОД — переключение active development branch

## Назначение

Безопасно переключить `/srv/eod/development` на новую GitHub branch без изменения preview.

## Preconditions

```bash
cd /srv/eod/development
git status --short --branch
```

Worktree должен быть clean. Development branch не должна быть `main`.

## Проверка refspec

Checkout INFRA-003 первоначально мог быть создан с `--single-branch`. Чтобы видеть все remote branches:

```bash
cd /srv/eod/development

git config remote.origin.fetch \
  '+refs/heads/*:refs/remotes/origin/*'

git fetch --prune origin
```

## Переключение на существующую remote branch

```bash
cd /srv/eod/development

git fetch --prune origin

git switch <branch> 2>/dev/null || \
git switch --track origin/<branch>

git pull --ff-only

git status --short --branch
git rev-parse HEAD
```

Пример:

```bash
git switch docs/001-project-operating-system 2>/dev/null || \
git switch --track origin/docs/001-project-operating-system
```

## После переключения

### Source/docs-only change

```bash
sudo bash scripts/development_stack.sh refresh
sudo bash scripts/development_stack.sh check
sudo bash scripts/development_stack.sh test
sudo bash scripts/development_stack.sh status
```

### Dependency/container change

```bash
sudo bash scripts/development_stack.sh rebuild
sudo bash scripts/development_stack.sh check
sudo bash scripts/development_stack.sh test
sudo bash scripts/development_stack.sh status
```

### Schema/data change

По плану work item выполнить migrations или reset development database.

## Проверка guard

`development_stack.sh` обязан отказаться запускаться из `main`. Если branch unexpectedly `main`, не обходить guard.

## После merge work item

Development checkout не переводится на `main`. Создаётся/выбирается следующая non-main branch от нового accepted baseline и выполняется переключение по этому runbook.

## Ошибки

### `fatal: invalid reference: origin/<branch>`

Причина обычно в single-branch fetch refspec. Выполнить секцию «Проверка refspec».

### Local changes

Не выполнять `reset --hard` без анализа. Сначала установить происхождение изменений. Tracked code на VPS не должен редактироваться вручную.

### Branch diverged

Не выполнять merge/rebase на VPS. История исправляется в GitHub branch, после чего VPS получает fast-forward state.

## Запрещено

- switch development to `main`;
- force reset, скрывающий неизвестные изменения;
- commit/push from VPS;
- изменять `/srv/eod/repository`;
- переключать branch во время пользовательской приёмки без фиксации нового head.