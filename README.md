# PokéBot Daily

Bot de Discord para trivia Pokémon diaria, retos semanales y sistema de gamificación.

## Configuración

### 1. Crear Bot en Discord Developer Portal

1. Ve a https://discord.com/developers/applications
2. Click "New Application" → Nombre: "PokéBot Daily"
3. Ve a "Bot" → Click "Add Bot"
4. Copia el **Token** (lo guardarás como variable de entorno)
5. Activa "Message Content Intent" en Privileged Gateway Intents
6. Ve a "OAuth2" → "URL Generator"
7. Selecciona scopes: `bot`, `applications.commands`
8. Selecciona permisos: Send Messages, Use Slash Commands, Embed Links, Add Reactions, Manage Roles
9. Copia la URL generada y ábrela para invitar el bot a tu servidor

### 2. Variables de Entorno

Crea una variable de entorno llamada `POKEBOT_TOKEN` con tu token:

**Windows (PowerShell):**
```powershell
$env:POKEBOT_TOKEN="tu_token_aqui"
```

**Windows (CMD):**
```cmd
set POKEBOT_TOKEN=tu_token_aqui
```

**Linux/Mac:**
```bash
export POKEBOT_TOKEN="tu_token_aqui"
```

### 3. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 4. Ejecutar el Bot

```bash
python main.py
```

## Canales Requeridos

El bot busca automáticamente estos canales en tu servidor:

| Canal | Función |
|-------|---------|
| `#comandos` | Para trivias y comandos |
| `#retos-semanales` | Para retos y notificaciones |
| `#hall-of-fame` | Para logros y reconocimientos |
| `#bienvenida` | Para mensajes de bienvenida |

## Comandos

| Comando | Descripción |
|---------|-------------|
| `!trivia` | Trivia Pokémon del día |
| `!leaderboard` | Ranking de trivia |
| `!checkin` | Check-in diario (+5 puntos) |
| `!profile [@usuario]` | Perfil de estadísticas |
| `!top` | Top 10 miembros activos |
| `!reto` | Reto semanal activo |
| `!completar-reto` | Marcar reto completado |
| `!crear-reto [título] [desc] [puntos] [días]` | Crear reto (admin) |
| `!ayuda-pokebot` | Lista de comandos |

## Sistema de Puntos

| Acción | Puntos |
|--------|--------|
| Trivia correcta | +10 |
| Check-in diario | +5 |
| Reto completado | +50 |

## Sistema de Rangos

| Racha | Rol |
|-------|-----|
| 7 días | 🔥 Activo |
| 30 días | ⭐ Veterano |
| 100 días | 🏆 Leyenda |
