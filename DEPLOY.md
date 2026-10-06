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

## 6. Failover — cómo probarlo

1. Con la PC encendida: en el panel del host aparece `Otra instancia es líder`.
2. Apaga la PC (o detén `PokeBot Daily`).
3. En ≤90s el host loguea `Conectando como líder` y el bot sigue activo.
4. Enciende la PC: espera a que caduque el lease del host (≤90s) y la PC
   recupera el control; el host se desconecta solo (`Lease de líder perdido`).

## 7. Mantenimiento

- **Renovación:** Quaxly Host no la pide; en bot-hosting.net renueva cada 4 días.
- **Backups:** `backups/` locales + `python backup_firebase.py --test`.
- **Restaurar:** `python backup_firebase.py --restore backups\firebase_XXX.json`.

## 8. Quaxly Host (FeatherPanel) — pasos exactos

El panel arranca con `python /home/container/app.py` y el repo **ya incluye
`app.py`**, así que no hay que cambiar el comando de arranque.

1. **Clona el código** en la consola del panel:

   ```bash
   cd /home/container
   git clone https://github.com/pokejgameryt-ship-it/PokeBot-Daily.git tmp
   mv tmp/* tmp/.[!.]* . 2>/dev/null; rm -rf tmp
   ls -la   # debe aparecer app.py, main.py, requirements.txt...
   ```

2. **Sube 3 ficheros** (nunca están en git; los `git pull` futuros no los tocan):
   - `.env` → variables varias (Twitch/Google, etc.)
   - `.token` → token del bot (POKEBOT_TOKEN)
   - `firebase-service-account.json` → credenciales Firebase

3. **Variables del panel** (Startup → Variables):
   - `REQUIREMENTS_FILE` = `requirements.txt` (si no, no instala las deps)
   - `AUTO_UPDATE` = `1` (git pull en cada arranque = updates sin subir nada)

4. **Start.** Primer arranque: `pip install -r requirements.txt` corre solo.
   Con la PC encendida verás `Otra instancia es líder; reintentando en 30s`
   (correcto). Apaga la PC y en ≤90s verás `Conectando como líder (…)`.
   Recuerde: Python del contenedor es 3.13 y Tesseract no existe (OCR
   deshabilitado automáticamente, el resto funciona igual).
