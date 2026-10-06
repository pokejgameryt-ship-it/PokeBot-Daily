# Despliegue en host gratuito (PC local + failover)

El bot soporta **dos instancias simultáneas** con sistema de **lease de líder en
Firebase**: solo la instancia líder se conecta a Discord y ejecuta los loops
(diaria 10:00, quiz semanal, recordatorios, reset de rachas). Si la PC se apaga,
el host toma el control en **≤90 segundos**. Si el host cae, la PC lo recupera.

## 1. Empaquetar

```powershell
python build_deploy.py
```

Genera `deploy/pokebot-deploy.zip` **sin secretos** (verifica el mensaje `[OK]`).

## 2. Crear la cuenta en el host

Candidatos recomendados (gratis, sin tarjeta):

1. **Quaxly Host** — 512 MB RAM, hasta 3 bots, sin renovación periódica (primera opción)
2. **bot-hosting.net** — 256 MB RAM, renovación manual cada 4 días (respaldo)

Crea el bot/plan, elige **Python 3.10+**, sube el zip por el panel y extráelo
en la raíz del plan.

## 3. Variables de entorno (panel del host)

Copia `.env.example` a `.env` y rellena, o configúralas como env vars del plan:

| Variable | Valor |
|---|---|
| `POKEBOT_TOKEN` | token del bot (Discord Developer Portal → Bot) |
| `INSTANCE_ID` | identificador único, ej. `quaxly-1` |
| `FIREBASE_SERVICE_ACCOUNT` | contenido JSON completo del archivo de service account **en una línea** |
| `ENABLE_WEB_SERVER` | `0` |

Opcionales (si no están, esas rutas de verificación se deshabilitan solas):
`TWITCH_CLIENT_ID`, `TWITCH_CLIENT_SECRET`, `GOOGLE_CLIENT_ID`,
`GOOGLE_CLIENT_SECRET`, `YOUTUBE_API_KEY`.

> **Riesgo aceptado:** el JSON de Firebase y el token van a un host de terceros.
> Si prefieres, crea una segunda cuenta de servicio Firebase con permisos
> solo-escritura limitados para el bot.

## 4. Arranque

- **Comando de inicio:** `python main.py`
- **Dependencias:** `pip install -r requirements.txt` (el panel suele hacerlo solo)

En los logs verás:

- `Otra instancia es líder; reintentando en 30s` → la PC manda (estado normal)
- `Conectando como líder (quaxly-1)` → el host ha tomado el control (PC apagada)

## 5. Degradaciones conocidas en el host

| Función | En PC local | En host gratuito |
|---|---|---|
| Trivia, quiz, rachas, retos, comandos | ✅ | ✅ |
| Verificación Twitch / Google OAuth | ✅ | ✅ |
| Verificación YouTube por screenshot (OCR) | ✅ Tesseract | ❌ sin Tesseract (se oculta/deshabilita con aviso) |
| Backup de Firebase | ✅ tarea diaria 04:00 | ✅ (se hace desde la PC) |

## 6. Failover — roles y cómo probarlo

**Roles (prioridades):** el **host es SIEMPRE la prioridad** — prioridad 0,
que es el default, así que **no hay que configurar nada en el host**. La PC
es el respaldo: `LEADER_PRIORITY=1` en el `.env` de la PC.

- Host líder (estado normal) → la PC espera: `Otra instancia es líder...`
- Host cae/apagado → la PC toma el mando en ≤90s.
- La PC es líder y el host (re)arranca → el host se anuncia en standby y la
  PC **cede sola en ≤30s** (`Cediendo el liderazgo a instancia prioritaria`),
  sin intervención manual.

### Probarlo

1. Con todo funcionando: la PC loguea `Otra instancia es líder; reintentando...`
2. En el panel: **Stop** → en ≤90s la PC loguea `Conectando como líder (...)`.
3. En el panel: **Start** → en ≤90s la PC cede y el host recupera el mando;
   la PC vuelve a `Otra instancia es líder...`.

## 7. Mantenimiento

- **Renovación:** Quaxly Host no la pide; en bot-hosting.net renueva cada 4 días.
- **Backups:** `backups/` locales + `python backup_firebase.py --test`.
- **Restaurar:** `python backup_firebase.py --restore backups\firebase_XXX.json`.

## 8. Quaxly Host (FeatherPanel) — pasos exactos

El panel **no da consola hasta que el servidor está online**, así que el
clonado va dentro del propio comando de arranque (no necesitas terminal).

### 8.1 Sube los 3 ficheros de secretos (la pestaña Files funciona offline)

- `.env` → variables varias (Twitch/Google, etc.)
- `.token` → token del bot (POKEBOT_TOKEN)
- `firebase-service-account.json` → credenciales Firebase

(Alternative: SFTP en `node10.quaxly.com:25258` con tu usuario/contraseña del panel.)

### 8.2 Settings → Startup → Startup Command

Pega **esta línea entera** (reemplaza la actual):

```bash
export PYTHONPATH=/home/container/.local/lib/python3.13/site-packages${PYTHONPATH:+:$PYTHONPATH}; if [ ! -f /home/container/app.py ]; then rm -rf /home/container/.bootstrap; git clone https://github.com/pokejgameryt-ship-it/PokeBot-Daily.git /home/container/.bootstrap && cp -a /home/container/.bootstrap/. /home/container/ && rm -rf /home/container/.bootstrap; fi; if [ -d /home/container/.git ] && [ "${AUTO_UPDATE}" = "1" ]; then git -C /home/container pull --ff-only; fi; if [ ! -z "${PY_PACKAGES}" ]; then pip install -U --prefix /home/container/.local ${PY_PACKAGES}; fi; if [ -f /home/container/requirements.txt ]; then pip install -U --prefix /home/container/.local -r /home/container/requirements.txt; fi; /usr/local/bin/python /home/container/app.py
```

En variables del mismo apartado pon:
- `AUTO_UPDATE` = `1` (git pull en cada arranque = updates sin subir nada)
- `INSTANCE_ID` opcional (p. ej. `quaxly-1`) para los logs
- **NO** pongas `LEADER_PRIORITY`: en el host debe ser 0 (principal). La PC
  es la respaldo con `LEADER_PRIORITY=1` en su `.env`.

### 8.3 Start

Primer arranque tarda (clone + `pip install`); después verás en consola
`Otra instancia es líder; reintentando en 30s` (correcto con la PC encendida).
Apaga la PC y en ≤90s aparece `Conectando como líder (...)`.

Python del contenedor: 3.13 · Tesseract no existe (OCR se deshabilita solo;
el resto funciona igual).
