# ЭОД — доступ через SSH tunnel

Applications слушают только VPS loopback. Tunnel делает выбранный remote port доступным на `127.0.0.1` клиента.

## Windows PowerShell — development

```powershell
ssh -N -T `
  -o ExitOnForwardFailure=yes `
  -o ServerAliveInterval=30 `
  -o ServerAliveCountMax=3 `
  -L 8766:127.0.0.1:8766 `
  -i "C:\Users\Gennadiy\.ssh\eod_contabo_ed25519" `
  eodadmin@5.181.177.72
```

Оставить PowerShell открытым. Browser:

```text
http://127.0.0.1:8766
```

## Windows PowerShell — preview

```powershell
ssh -N -T `
  -o ExitOnForwardFailure=yes `
  -o ServerAliveInterval=30 `
  -o ServerAliveCountMax=3 `
  -L 8765:127.0.0.1:8765 `
  -i "C:\Users\Gennadiy\.ssh\eod_contabo_ed25519" `
  eodadmin@5.181.177.72
```

Browser:

```text
http://127.0.0.1:8765
```

## Termux — development

```bash
ssh -N -T \
  -o ExitOnForwardFailure=yes \
  -o ServerAliveInterval=30 \
  -o ServerAliveCountMax=3 \
  -L 8766:127.0.0.1:8766 \
  -i ~/.ssh/eod_contabo_ed25519 \
  eodadmin@5.181.177.72
```

Android browser:

```text
http://127.0.0.1:8766
```

## Поведение

При успехе `ssh -N -T` обычно ничего не выводит и остаётся работать. Это нормально. Для обычной SSH shell открыть вторую terminal session.

## Проверка local port

Windows:

```powershell
Test-NetConnection 127.0.0.1 -Port 8766
```

Termux:

```bash
curl --fail --silent --show-error http://127.0.0.1:8766/_health/
```

## Demo accounts

```text
operator.demo   / EodDemo!2026
supervisor.demo / EodDemo!2026
```

## Типичные ошибки

### `Address already in use`

Local port занят другим tunnel/process. Закрыть старую session или выбрать другой local port, сохранив remote target:

```text
-L 18766:127.0.0.1:8766
```

Browser: `http://127.0.0.1:18766`.

### `Permission denied (publickey)`

Проверить path and permissions private key. Не копировать key content в чат.

### Browser не открывает страницу

Проверить:

1. tunnel session всё ещё работает;
2. VPS app healthy;
3. правильный local port;
4. URL использует `http`, не `https`;
5. local VPN/firewall не перехватывает loopback.

## Безопасность

- не добавлять `0.0.0.0` port publishing ради удобства;
- не публиковать приложение напрямую в Internet;
- не публиковать PostgreSQL;
- private key не хранить в repository;
- tunnel не меняет права приложения и не заменяет authentication.