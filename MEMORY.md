# MEMORY.md — PokeBot Daily

## Stack / Decisiones clave
- **Bot Discord en español** para el YouTuber PokeJgamer: trivia diaria (10:00 Europa/Madrid), quiz semanal V/F (lunes 10:00), rachas, retos, verificación Twitch/YouTube con roles.
- **Python 3.10 + discord.py 2.7**, datos en **Firebase Realtime Database** (sync `firebase_admin`, URL hardcodeada en `database.py`).
- **Ejecución actual**: local en Windows PC del usuario (prioridad BELOW_NORMAL, tarea programada "PokeBot Daily" al logon vía `bot_silent.vbs` → `pythonw main.py`). Oracle Cloud **fuera de servicio** (trial caducado).
- **Hosting objetivo**: PC local + host gratis (Quaxly o bot-hosting.net) con **sistema de líder en Firebase** (heartbeat `instances/{id}`, solo el líder ejecuta bucles/comandos) → failover sin trivia dobles.
- Web server (`web_server.py`, puerto 8080) **desactivada por defecto**; se activa con `ENABLE_WEB_SERVER=1`.
- `.env` se carga con `python-dotenv` desde `config.py` (override=False); token Discord en `.token`.
- OCR screenshot YouTube: Tesseract 5.4 local con `spa+eng`, ruta fija `C:\Program Files\Tesseract-OCR\` si no está en PATH (`verify.py`). **No disponible en contenedores** → degradación elegante.
- Canales restringidos: comandos en `1516733719191228416` salvo `enviar-verificacion`, `verificar-todos`, `pkquest` (canal `1405922298095206432`). Quiz semanal en `1519457892212801807`.

## Skills OpenCode aplicables (de 146 instaladas)
`always-on-memory`, `project-skill-scoping`, `security-vulnerability-scan`, `secrets-management-sops`, `python-pytest`, `code-refactoring-clean-code`, `github-actions-ci-cd`, `code-coverage-checker`, `conventional-commits`, `git-workflow-expert`, `cron-job-scheduler`, `db-backup-disaster-recovery`, `performance-profiling`, `readme-docs-generator`.
No aplicables: frontend/mobile/AI/infra (no hay web UI, ni LLM en runtime).

## Cambios recientes
- Carga de `.env` con dotenv + `.token` con ruta absoluta (`config.py`).
- Web server desactivada por defecto (`main.py` setup_hook).
- Tesseract instalado en Windows (spa+eng) + `pytesseract` pip; fallback de ruta en `verify.py`.
- Doble pasada OCR (normal + invertida) para dark mode de YouTube; keywords ampliadas.
- Tarea programada "PokeBot Daily" creada (reinicio 3× 1 min, sin límite tiempo).
- Fix imports: `random`/`MIEMBRO_ROLE_ID` faltantes en `main.py` catch-up.
- YouTube OAuth (scope youtube.readonly) **descartado** por verificación sensible de Google → screenshot OCR.
- **Fase 1 completada**: secretos rotados/quitados, .gitignore/.dockerignore actualizados, `on_command_error` global, 4 bucles protegidos con try/except, `on_ready` guard `is_running()`, `check_twitch_follow` fail-safe (None ≠ unfollowed), `!verificar-todos` fix YouTube, `tree.sync()` + filtro canal para slash.
- **Fase 2 completada**: `ruff` config (`pyproject.toml`), tests pytest (trivia generators + database logic + imports), GitHub Actions CI (lint → test → gitleaks), `requirements.txt` limpio (quitado psycopg2-binary).
- **Fase 3 completada**: TZ `zoneinfo("Europe/Madrid")` (main+trivia), ventanas retry 10:00-10:30 con flags antidesuplicado, `asyncio.to_thread` en loops FB, logging `RotatingFileHandler` (`logs/bot.log` 5MB×5) + `SecretFilter`, watchdog 5 min (`watchdog_task` reinicia loops caídos), fugas cerradas (`_active_views` cap 7, `TRIVIA_STORE` purga >26h, `wait_for` timeout 300s), **backup Firebase** (`backup_firebase.py` + tarea "PokeBot Backup" 04:00 diario, conserva 14, `--test`/`--restore`/`--list`), todos los `except:` bare → específicos (0 restantes).
- **Fase 4 completada**: `leader.py` — lease en Firebase (nodo `leader/`, TTL 90s, renew 30s con transacción atómica + fast-path de lectura); `_run_with_lease()` en `main.py` (solo la líder conecta a Discord); `lease_renew_task` cierra el bot si pierde el lease; gates `leader.is_leader()` en los 3 loops; `setup_hook` idempotente (re-login seguro); 8 tests `test_leader.py` (36 total); despliegue: `.env.example`, `build_deploy.py` (zip verificado sin secretos), `DEPLOY.md`.
- **README.md** actualizado (hosting, backup, arquitectura, 36 tests).
- **Bugs encontrados y corregidos en Fase 3/4**: quiz semanal roto — `send_quiz_question` no enviaba nada (código muerto con `interaction` indefinido, regresión previa) → restaurado `user.send(embed, view)`; `process_answer` defer OK; doble `remove_roles` eliminado; F821/F841/F401 de ruff limpios en `--select E9,F`.

## Estado de fases
- [x] Fase 0: MEMORY.md
- [x] Fase 1: fixes críticos 1-9
- [x] Fase 2: ruff + pytest + CI GitHub Actions + README
- [x] Fase 3: fiabilidad (TZ, retry 10:00-10:30, logs, watchdog, fugas, backup Firebase, bare excepts)
- [x] Fase 4: lease de líder + paquete de despliegue (leader.py, build_deploy.py, DEPLOY.md)
- [x] Fase 5: hardening de secretos + tests regresión quiz (39 tests)

## Estrategia de secretos (sin rotaciones futuras)
- Repo **público**; historial contenía: token bot ANTIGUO (muerto — seg2 distinto al actual, ya rotado antes) y OAuth secret de Discord (vigente pero **código muerto**: DISCORD_CLIENT_* eliminados de config.py en Fase 5).
- **Barrido de historial con `git filter-repo --replace-text`** (ambos valores → `***REMOVED***`) + force push → el repo público queda limpio; **el usuario NO necesita rotar nada**.
- Guardas futuras: hook local `.git/hooks/pre-commit` (escanea staged: tokens Discord, AIza, claves privadas, service_account, valores no-placeholder en vars secretas) + gitleaks en CI + `.env/.token/json` gitignored (nunca commiteados — verificado con `git log --all`).
- Redeploys sin re-teclear: `python build_deploy.py --with-secrets` → `deploy/pokebot-deploy-full.zip` lleva el `.env` dentro (nunca subirlo a sitio público); en paneles de hosting las env vars persisten → se teclean UNA vez.
- Verificación: `git log -S "<secreto>"` vacío tras barrido; CI gitleaks verde.

## Pendientes (acción del usuario)
1. **Desplegar en Quaxly Host** según `DEPLOY.md` (requiere su cuenta): `python build_deploy.py --with-secrets`, subir zip, comando `python main.py`.
2. Hacer **commit/push** — hecho en Fase 5 (ver `git log`).
3. Verificar en directo lunes 10:00 (retry window + catch-up) y probar failover apagando la PC.
4. (Opcional, bajo demanda) Rotar el OAuth secret de Discord en el portal si se sospecha que alguien lo copió del repo público antes del barrido — sin rotar, el riesgo es bajo (código no lo usa, redirect URIs registradas).