# PokeBot Daily

Discord bot para el canal de YouTube **PokeJgamer** (comandos en español).

## Características

- **Trivia diaria** a las 10:00 (hora España) — preguntas de Pokémon, 3 opciones, botones interactivos
- **Quiz semanal** (lunes 10:00) — 10 preguntas Verdadero/Falso, puntos por aciertos
- **Rachas y rachas rotas** — recordatorios a las 10:00, limpieza cada hora
- **Retos semanales** — comandos `!reto`, `!completar-reto`, ranking
- **Verificación de seguidores** — Twitch (OAuth) y YouTube (screenshot OCR + API key)
- **Rol "Miembro Verificado"** — asignación/eliminación automática
- **Catch-up al iniciar** — publica trivia/quiz perdidos mientras el PC estaba apagado
- **Persistencia en Firebase Realtime Database**

## Requisitos

- Python 3.10+
- Discord bot token
- Firebase Realtime Database (cuenta gratuita)
- Twitch App (Client ID/Secret) para verificación OAuth
- Google Cloud OAuth (Client ID/Secret) para YouTube (opcional, para flujo alternativo)
- Tesseract OCR 5.x con idiomas `spa` + `eng` (para verificación YouTube por screenshot)

## Instalación local (Windows)

```powershell
# 1. Clonar repo
git clone https://github.com/pokejgameryt-ship-it/PokeBot-Daily
cd PokeBot-Daily

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Instalar Tesseract OCR (necesario para verificación YouTube)
# Descargar instalador UB Mannheim: https://github.com/UB-Mannheim/tesseract/wiki
# Añadir idiomas spa+eng durante la instalación o descargar spa.traineddata a tessdata/

# 4. Configurar variables de entorno
# Copiar .env.example a .env y rellenar:
#   TWITCH_CLIENT_ID, TWITCH_CLIENT_SECRET, TWITCH_BROADCASTER_ID, TWITCH_BROADCASTER_LOGIN
#   GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
#   YOUTUBE_API_KEY
#   DISCORD_CLIENT_ID, DISCORD_CLIENT_SECRET
# Token Discord en archivo .token (o POKEBOT_TOKEN en .env)

# 5. Ejecutar
python main.py
# O en segundo plano: iniciar.bat / bot_silent.vbs

# 6. Arranque automático al iniciar sesión
# Ejecutar como admin:
powershell -ExecutionPolicy Bypass -File install_task.ps1
```

## Variables de entorno (.env)

| Variable | Descripción | Requerida |
|----------|-------------|-----------|
| `POKEBOT_TOKEN` | Token del bot Discord | Sí (o archivo `.token`) |
| `TWITCH_CLIENT_ID` | Twitch App Client ID | Para verificación Twitch |
| `TWITCH_CLIENT_SECRET` | Twitch App Secret | Para verificación Twitch |
| `TWITCH_BROADCASTER_ID` | ID del canal Twitch a seguir | Sí (default: `1134721153`) |
| `TWITCH_BROADCASTER_LOGIN` | Login del canal Twitch | Sí (default: `pokejgamer`) |
| `GOOGLE_CLIENT_ID` | Google OAuth Client ID | Para YouTube OAuth (opcional) |
| `GOOGLE_CLIENT_SECRET` | Google OAuth Secret | Para YouTube OAuth (opcional) |
| `YOUTUBE_API_KEY` | YouTube Data API v3 Key | Para `!verificar-todos` |
| `DISCORD_CLIENT_ID` | Discord App Client ID | Para OAuth (opcional) |
| `DISCORD_CLIENT_SECRET` | Discord App Secret | Para OAuth (opcional) |

## Comandos

| Comando | Canal | Descripción |
|---------|-------|-------------|
| `!trivia` | #comandos-pokebot | Responder trivia diaria |
| `!checkin` | #comandos-pokebot | Check-in diario para racha |
| `!ranking` | #comandos-pokebot | Top 10 global / semana |
| `!mis-puntos` | #comandos-pokebot | Tus puntos y racha |
| `!reto` | #comandos-pokebot | Ver reto activo |
| `!completar-reto` | #comandos-pokebot | Completar reto |
| `!enviar-verificacion` | Cualquier | Admin: envía embed de verificación |
| `!verificar-todos` | Cualquier | Admin: sincroniza seguidores |
| `!pkquest` | #pkquest | Crear pregunta de Pokéconcurso |
| `/trivia` | Slash | Responder trivia diaria (slash) |
| `/checkin` | Slash | Check-in (slash) |
| `/ranking` | Slash | Ranking (slash) |
| `/reto` | Slash | Ver reto (slash) |
| `/completar-reto` | Slash | Completar reto (slash) |
| `/profile` | Slash | Tu perfil (slash) |

## Hosting 24/7 gratis (sin tarjeta)

El bot funciona en local mientras tu PC esté encendida. Para que siga online cuando apagues el PC:

1. **Opción A: Quaxly Host** (recomendado)
   - 512 MB RAM compartida, 3 bots, sin renovación manual
   - Despliegue por panel, variables de entorno

2. **Opción B: bot-hosting.net**
   - 256 MB RAM, renovación manual cada 4 días

**Sistema de líder (failover)**: `leader.py` mantiene un **lease en Firebase**
(nodo `leader/`, TTL 90s, renovación cada 30s vía transacción atómica). Solo la
instancia líder se conecta a Discord y ejecuta los loops programados. Si la PC
se apaga, el host toma el control en **≤90s**; si el host cae, la PC lo
recupera. Sin trivia duplicadas.

Guía completa de despliegue: **[DEPLOY.md](DEPLOY.md)** (`python build_deploy.py`
genera el zip sin secretos).

⚠️ Limitación: Tesseract OCR no existe en contenedores → verificación YouTube
por screenshot solo en local; en el host se degrada elegantemente.

## Backup de Firebase

```bash
python backup_firebase.py            # backup a backups/ (conserva últimos 14)
python backup_firebase.py --test     # backup + verificación de integridad
python backup_firebase.py --list     # listar backups
python backup_firebase.py --restore backups/firebase_XXX.json  # restaurar
```

Tarea Windows **"PokeBot Backup"** ejecuta el backup diario a las 04:00
(salida en `logs/backup.log`).

## Arquitectura

```
main.py           → Entry point, loops, catch-up, prefix/slash commands
config.py         → Carga .env + .token, config centralizada
database.py       → Capa Firebase Realtime DB (sync)
leader.py         → Lease de líder en Firebase (failover PC <-> host)
trivia.py         → Cog: trivia diaria, quiz semanal, views
verify.py         → Cog: verificación Twitch/YouTube, OCR, loops
reto.py           → Cog: retos semanales, perfil
essentials_trivia.py → 20 generadores de preguntas desde datos Essentials
backup_firebase.py   → Backup/restore/integridad de Firebase
build_deploy.py   → Empaqueta zip de despliegue sin secretos
web_server.py     → aiohttp (páginas legales, /health) — desactivada por defecto
```

## Testing y CI

```bash
# Tests (36)
python -m pytest tests/ -v

# Lint (errores críticos)
ruff check . --select E9,F

# CI: GitHub Actions (lint → test → secret scan)
```

## Licencia

MIT — uso libre para proyectos de fans de PokeJgamer.