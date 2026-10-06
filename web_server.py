import os

from aiohttp import web

pending_codes = {}

PAGE_INDEX = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PokeJGamer</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Arial, sans-serif; background: #1a1a2e; color: #fff; min-height: 100vh; display: flex; align-items: center; justify-content: center; }
        .container { text-align: center; padding: 40px; }
        .logo { font-size: 80px; margin-bottom: 20px; }
        h1 { font-size: 2.5em; margin-bottom: 10px; }
        h1 span { color: #e94560; }
        p { font-size: 1.2em; color: #aaa; margin-bottom: 30px; }
        .links { display: flex; gap: 20px; justify-content: center; flex-wrap: wrap; }
        .links a { display: inline-block; padding: 12px 30px; border-radius: 8px; text-decoration: none; font-weight: bold; transition: transform 0.2s; }
        .links a:hover { transform: scale(1.05); }
        .yt { background: #e94560; color: #fff; }
        .tw { background: #9146FF; color: #fff; }
        .dc { background: #5865F2; color: #fff; }
        footer { margin-top: 40px; color: #555; font-size: 0.9em; }
        footer a { color: #888; }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">&#127918;</div>
        <h1>Poke<span>JGamer</span></h1>
        <p>Canal de Pokemon en YouTube y Twitch</p>
        <div class="links">
            <a href="https://youtube.com/@pokejgamer" class="yt">YouTube</a>
            <a href="https://twitch.tv/pokejgamer" class="tw">Twitch</a>
            <a href="https://discord.gg/pokejgamer" class="dc">Discord</a>
        </div>
        <footer>
            <a href="/privacy">Politica de Privacidad</a> &middot; <a href="/terms">Terminos de Servicio</a>
        </footer>
    </div>
</body>
</html>"""

PAGE_PRIVACY = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Politica de Privacidad - PokeJGamer</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Arial, sans-serif; background: #1a1a2e; color: #ddd; line-height: 1.8; }
        .container { max-width: 800px; margin: 0 auto; padding: 40px 20px; }
        h1 { color: #e94560; margin-bottom: 10px; }
        .date { color: #888; margin-bottom: 30px; }
        h2 { color: #fff; margin-top: 30px; margin-bottom: 10px; }
        p { margin-bottom: 15px; }
        ul { margin-left: 20px; margin-bottom: 15px; }
        a { color: #e94560; }
        .back { display: inline-block; margin-bottom: 20px; color: #888; text-decoration: none; }
        .back:hover { color: #e94560; }
    </style>
</head>
<body>
    <div class="container">
        <a href="/" class="back">&larr; Volver</a>
        <h1>Politica de Privacidad</h1>
        <p class="date">Ultima actualizacion: 25 de agosto de 2026</p>
        <h2>1. Informacion que recopilamos</h2>
        <p>Nuestro bot de Discord (PokeBot) recopila unicamente la informacion necesaria para su funcionamiento:</p>
        <ul>
            <li>ID de usuario de Discord</li>
            <li>Nombre de usuario de Discord</li>
            <li>Nombre de usuario de Twitch (si verificas tu cuenta)</li>
            <li>Estadisticas de trivia y puntuacion</li>
        </ul>
        <h2>2. Como usamos la informacion</h2>
        <p>Utilizamos esta informacion para:</p>
        <ul>
            <li>Gestionar la verificacion de seguidores en Twitch y YouTube</li>
            <li>Mantener el sistema de puntuacion y rachas de trivia</li>
            <li>Asignar roles en el servidor de Discord</li>
        </ul>
        <h2>3. Almacenamiento</h2>
        <p>Los datos se almacenan en Firebase Realtime Database. No se comparten con terceros.</p>
        <h2>4. OAuth</h2>
        <p>Al verificar tu cuenta con Twitch o YouTube, usamos OAuth para confirmar tu suscripcion/seguimiento. No almacenamos tokens de acceso despues de la verificacion.</p>
        <h2>5. Eliminacion de datos</h2>
        <p>Puedes solicitar la eliminacion de tus datos contactando al administrador del servidor de Discord.</p>
        <h2>6. Cambios en esta politica</h2>
        <p>Podemos actualizar esta politica periodicamente. Los cambios se publicaran en esta pagina.</p>
    </div>
</body>
</html>"""

PAGE_TERMS = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Terminos de Servicio - PokeJGamer</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Arial, sans-serif; background: #1a1a2e; color: #ddd; line-height: 1.8; }
        .container { max-width: 800px; margin: 0 auto; padding: 40px 20px; }
        h1 { color: #e94560; margin-bottom: 10px; }
        .date { color: #888; margin-bottom: 30px; }
        h2 { color: #fff; margin-top: 30px; margin-bottom: 10px; }
        p { margin-bottom: 15px; }
        ul { margin-left: 20px; margin-bottom: 15px; }
        a { color: #e94560; }
        .back { display: inline-block; margin-bottom: 20px; color: #888; text-decoration: none; }
        .back:hover { color: #e94560; }
    </style>
</head>
<body>
    <div class="container">
        <a href="/" class="back">&larr; Volver</a>
        <h1>Terminos de Servicio</h1>
        <p class="date">Ultima actualizacion: 25 de agosto de 2026</p>
        <h2>1. Aceptacion</h2>
        <p>Al usar el bot de Discord PokeBot, aceptas estos terminos de servicio.</p>
        <h2>2. Uso del bot</h2>
        <p>El bot se proporciona "tal cual" para entretenimiento. No garantizamos disponibilidad continua.</p>
        <h2>3. Verificacion</h2>
        <p>Al verificar tu cuenta con Twitch o YouTube, confirmas que eres titular de esa cuenta. El uso de cuentas falsas o de terceros esta prohibido.</p>
        <h2>4. Sistema de puntuacion</h2>
        <p>La puntuacion y las rachas son informativas y no tienen valor monetario. Nos reservamos el derecho de resetear puntuaciones en caso de fraude o abuso.</p>
        <h2>5. Prohibiciones</h2>
        <ul>
            <li>Usar el bot para spam o abuso</li>
            <li>Intentar explotar fallos del bot</li>
            <li>Usar cuentas falsas para verificar</li>
            <li>Manipular puntuaciones o rachas</li>
        </ul>
        <h2>6. Responsabilidad</h2>
        <p>No somos responsables de danos derivados del uso del bot.</p>
        <h2>7. Cambios</h2>
        <p>Podemos modificar estos terminos en cualquier momento. Los cambios se publicaran en esta pagina.</p>
    </div>
</body>
</html>"""


async def handle_index(request):
    return web.Response(text=PAGE_INDEX, content_type="text/html")


async def handle_privacy(request):
    return web.Response(text=PAGE_PRIVACY, content_type="text/html")


async def handle_terms(request):
    return web.Response(text=PAGE_TERMS, content_type="text/html")


async def handle_callback(request):
    code = request.query.get("code")
    state = request.query.get("state", "unknown")

    if code:
        pending_codes[state] = code
        html = f"""
        <html>
        <head><title>Verificacion</title></head>
        <body style="font-family: Arial; text-align: center; padding: 50px; background: #2C2F33; color: white;">
            <h1>&#9989; Codigo obtenido!</h1>
            <p style="font-size: 20px; background: #40444B; padding: 15px; border-radius: 10px; word-break: break-all;">
                <strong>{code}</strong>
            </p>
            <p style="color: #aaa;">Copia el codigo de arriba y vuelve a Discord a pegarlo.</p>
            <p style="color: #aaa;">Puedes cerrar esta ventana.</p>
        </body>
        </html>
        """
    else:
        html = """
        <html>
        <head><title>Verificacion</title></head>
        <body style="font-family: Arial; text-align: center; padding: 50px; background: #2C2F33; color: white;">
            <h1>&#10060; Error</h1>
            <p>No se recibio ningun codigo.</p>
        </body>
        </html>
        """
    return web.Response(text=html, content_type="text/html")


async def handle_health(request):
    return web.Response(text="OK", content_type="text/plain")


def get_code(user_id: str):
    return pending_codes.pop(user_id, None)


async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_index)
    app.router.add_get("/privacy", handle_privacy)
    app.router.add_get("/terms", handle_terms)
    app.router.add_get("/callback", handle_callback)
    app.router.add_get("/health", handle_health)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"[OK] Web server started on port {port}")
