# 🤖 Guía en Español - Crear y Configurar PokéBot Daily

---

## FASE 1: CREAR LA APLICACIÓN EN DISCORD

### Paso 1.1: Entrar al Portal de Desarrolladores

1. Abre tu navegador
2. Ve a: **https://discord.com/developers/applications**
3. Inicia sesión con tu cuenta de Discord

### Paso 1.2: Crear la Aplicación

1. Click en el botón azul **"Nueva aplicación"** (esquina superior derecha)
2. En el campo **"NOMBRE"**, escribe: `PokéBot Daily`
3. Marca la casilla **"Acepto y reconozco..."**
4. Click en **"Crear"**

### Paso 1.3: Crear el Bot

1. En el menú de la izquierda, click en **"Bot"**
2. Click en el botón **"Añadir bot"**
3. Click en **"¡Sí, lo hago!"** para confirmar

### Paso 1.4: Configurar Permisos del Bot

En la sección **"Intenciones privilegiadas de puerta de enlace"**, activa:

1. ✅ **INTENCIÓN DE PRESENCIA** → ACTIVADA
2. ✅ **INTENCIÓN DE MIEMBROS DEL SERVIDOR** → ACTIVADA
3. ✅ **INTENCIÓN DE CONTENIDO DE MENSAJES** → ACTIVADA

> ⚠️ **IMPORTANTE**: Sin estas intenciones, el bot NO puede leer mensajes.

### Paso 1.5: Copiar el Token

1. En la sección **"TOKEN"**, click en **"Restablecer token"**
2. Click en **"¡Sí, lo hago!"**
3. Click en **"Copiar"** para copiar el token
4. **GUARDA ESTE TOKEN EN UN LUGAR SEGURO**
   - Ejemplo: pega en un archivo de texto temporal
   - **NUNCA lo compartas con nadie**

> 📝 Tu token se ve así: `MTExNjM0NTY3ODkwMTIzNDU2Nw.G12345.ABCDEF1234567890abcdef`

---

## FASE 2: INVITAR EL BOT A TU SERVIDOR

### Paso 2.1: Generar URL de Invitación

1. En el menú de la izquierda, click en **"OAuth2"**
2. Click en **"Generador de URL"**

### Paso 2.2: Seleccionar Ámbitos (Scopes)

En la sección **"ÁMBITOS"**, marca:

1. ✅ **bot**
2. ✅ **applications.commands**

### Paso 2.3: Seleccionar Permisos

En la sección **"PERMISOS DEL BOT"**, marca:

1. ✅ **Permisos generales:**
   - Ver canales
   - Administrar roles
   - Administrar mensajes

2. ✅ **Permisos de texto:**
   - Enviar mensajes
   - Enviar mensajes en hilos
   - Crear hilos públicos
   - Crear hilos privados
   - Insertar enlaces
   - Adjuntar archivos
   - Añadir reacciones
   - Usar emoji externo
   - Usar comandos de barra

3. ✅ **Permisos de voz:**
   - Conectar
   - Hablar

### Paso 2.4: Copiar y Abrir URL

1. Abajo aparece una URL larga
2. Click en **"Copiar"**
3. Pega la URL en una nueva pestaña del navegador
4. Selecciona tu servidor del menú desplegable
5. Click en **"Autorizar"**
6. Completa el CAPTCHA si aparece

---

## FASE 3: CONFIGURAR EL TOKEN EN TU ORDENADOR

### Paso 3.1: Abrir PowerShell

1. Click en el botón de Windows
2. Escribe **"PowerShell"**
3. Click en **"Windows PowerShell"**

### Paso 3.2: Configurar Token (Opción A - Temporal)

Copia y pega este comando (reemplaza `TU_TOKEN_AQUI` con tu token real):

```powershell
$env:POKEBOT_TOKEN="TU_TOKEN_AQUI"
```

> ⚠️ Este token durará solo mientras esté abierto PowerShell.

### Paso 3.3: Configurar Token (Opción B - Permanente)

Para que el token persista después de cerrar PowerShell:

```powershell
[System.Environment]::SetEnvironmentVariable("POKEBOT_TOKEN", "TU_TOKEN_AQUI", "User")
```

Después de ejecutar, **cierra y vuelve a abrir PowerShell** para que tome efecto.

### Paso 3.4: Verificar que el Token está Configurado

```powershell
echo $env:POKEBOT_TOKEN
```

Debe imprimir tu token. Si no aparece nada, vuelve al paso 3.2.

---

## FASE 4: INSTALAR DEPENDENCIAS

### Paso 4.1: Navegar a la Carpeta del Bot

```powershell
cd "C:\Users\jaume.JAUME\Desktop\PROYECTOS OPENCODE\DISCORD MEJORAS\PokeBot Daily"
```

### Paso 4.2: Verificar que Python está Instalado

```powershell
python --version
```

Debe mostrar algo como `Python 3.10.0` o superior.

> Si no funciona, instala Python desde: https://www.python.org/downloads/
> **IMPORTANTE**: Marca "Add Python to PATH" al instalar.

### Paso 4.3: Crear Entorno Virtual (Recomendado)

```powershell
python -m venv venv
```

### Paso 4.4: Activar Entorno Virtual

```powershell
.\venv\Scripts\Activate.pseshell
```

> Si da error de permisos, ejecuta primero:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

### Paso 4.5: Instalar Dependencias

```powershell
pip install -r requirements.txt
```

Espera a que termine la instalación. Deberías ver algo como:
```
Successfully installed discord.py-2.3.2
```

---

## FASE 5: EJECUTAR EL BOT

### Paso 5.1: Ejecutar

```powershell
python main.py
```

### Paso 5.2: Verificar que Funciona

Deberías ver en la consola:
```
✅ PokéBot Daily#1234 está online y listo para funcionar.
📊 Base de datos inicializada.
```

### Paso 5.3: Probar en Discord

1. Ve a tu servidor de Discord
2. Ve al canal `#comandos`
3. Escribe: `!trivia`
4. Debería aparecer una trivia Pokémon

---

## FASE 6: CONFIGURAR CANALES REQUERIDOS

El bot busca automáticamente estos canales. Si no existen, créalos:

### Paso 6.1: Canales Necesarios

| Canal | Categoría | Para qué |
|-------|-----------|----------|
| `#comandos` | CHATS | Trivias y comandos |
| `#retos-semanales` | PARTICIPACIÓN (o crea uno) | Retos semanales |
| `#hall-of-fame` | PARTICIPACIÓN (o crea uno) | Logros y reconocimientos |
| `#bienvenida` | NOTIFICACIONES | Mensajes de bienvenida |

### Paso 6.2: Crear Canal de Retos (si no existe)

1. Click derecho en **"PARTICIPACIÓN"** → **"Crear canal"**
2. Nombre: `retos-semanales`
3. Tipo: Texto
4. Click **"Crear canal"**

### Paso 6.3: Crear Canal Hall of Fame (si no existe)

1. Click derecho en **"PARTICIPACIÓN"** → **"Crear canal"**
2. Nombre: `hall-of-fame`
3. Tipo: Texto
4. Click **"Crear canal"**

---

## FASE 7: PROBAR TODOS LOS COMANDOS

### Prueba 1: Trivia

En `#comandos`:
```
!trivia
```
✅ Debería aparecer una pregunta con botones A, B, C

### Prueba 2: Check-in

```
!checkin
```
✅ Debería confirmar el check-in y dar puntos

### Prueba 3: Perfil

```
!profile
```
✅ Debería mostrar tus estadísticas

### Prueba 4: Leaderboard

```
!leaderboard
```
✅ Debería mostrar el ranking

### Prueba 5: Top

```
!top
```
✅ Debería mostrar los miembros más activos

### Prueba 6: Reto

```
!reto
```
✅ Debería mostrar el reto activo (o decir que no hay)

### Prueba 7: Ayuda

```
!ayuda-pokebot
```
✅ Debería mostrar la lista de comandos

---

## FASE 8: CREAR RETO DE EJEMPLO

Solo los admins pueden crear retos. En `#comandos`:

```
!crear-reto Shiny Hunter Encuentra un shiny Pokémon 50 7
```

Esto crea un reto:
- **Título:** Shiny Hunter
- **Descripción:** Encuentra un shiny Pokémon
- **Puntos:** 50
- **Duración:** 7 días

---

## 🔧 SOLUCIÓN DE PROBLEMAS

### Problema: "No se puede leer el token"

**Solución:**
```powershell
$env:POKEBOT_TOKEN="tu_token_aqui"
```

### Problema: "ModuleNotFoundError: No module named 'discord'"

**Solución:**
```powershell
pip install discord.py
```

### Problema: "ImproperlyConfigured: You must use..."

**Solución:** Activa las Intenciones Privilegiadas de Puerta de Enlace en el Portal de Desarrolladores (Paso 1.4)

### Problema: El bot no responde

**Soluciones:**
1. Verifica que el bot está encendido (consola abierta)
2. Verifica que estás en el canal correcto (`#comandos`)
3. Verifica que el prefijo es `!` (no `/`)
4. Verifica que "Intención de Contenido de Mensajes" está activa

### Problema: "Acceso denegado" al ejecutar scripts

**Solución:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Problema: El bot se desconecta

**Solución:** El bot se reconecta automáticamente. Si no lo hace, reinicia:
```powershell
python main.py
```

---

## 📋 COMANDOS RÁPIDOS PARA RECORDAR

| Comando | Qué hace |
|---------|----------|
| `!trivia` | Trivia del día |
| `!checkin` | Check-in diario (+5 puntos) |
| `!profile` | Tu perfil |
| `!top` | Top 10 miembros |
| `!leaderboard` | Ranking de trivia |
| `!reto` | Ver reto semanal |
| `!completar-reto` | Completar reto |
| `!crear-reto [t] [d] [p] [días]` | Crear reto (admin) |
| `!ayuda-pokebot` | Ayuda |

---

## ✅ CHECKLIST DE VERIFICACIÓN

- [ ] Portal de Desarrolladores: App creada
- [ ] Portal de Desarrolladores: Bot añadido
- [ ] Portal de Desarrolladores: 3 Intenciones Privilegiadas activadas
- [ ] Portal de Desarrolladores: Token copiado
- [ ] Bot invitado al servidor
- [ ] Token configurado en PowerShell
- [ ] Python instalado
- [ ] Dependencias instaladas (`pip install -r requirements.txt`)
- [ ] Bot ejecutándose (`python main.py`)
- [ ] Consola muestra "está online"
- [ ] `!trivia` funciona en Discord
- [ ] `!checkin` funciona
- [ ] `!profile` funciona
- [ ] Canales #comandos, #retos-semanales, #hall-of-fame existen

---

## 🆘 ¿NECESITAS AYUDA?

Si algo no funciona:

1. **Copia el error completo** de la consola
2. **Describe qué estabas haciendo** cuando falló
3. **Di qué paso** de esta guía estabas siguiendo
