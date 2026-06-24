import os
import aiohttp
from aiohttp import web
import asyncio

pending_codes = {}


async def handle_callback(request):
    code = request.query.get("code")
    state = request.query.get("state", "unknown")

    if code:
        pending_codes[state] = code
        html = f"""
        <html>
        <head><title>Verificación</title></head>
        <body style="font-family: Arial; text-align: center; padding: 50px; background: #2C2F33; color: white;">
            <h1>✅ ¡Código obtenido!</h1>
            <p style="font-size: 20px; background: #40444B; padding: 15px; border-radius: 10px; word-break: break-all;">
                <strong>{code}</strong>
            </p>
            <p style="color: #aaa;">Copia el código de arriba y vuelve a Discord a pegarlo.</p>
            <p style="color: #aaa;">Puedes cerrar esta ventana.</p>
        </body>
        </html>
        """
    else:
        html = """
        <html>
        <head><title>Verificación</title></head>
        <body style="font-family: Arial; text-align: center; padding: 50px; background: #2C2F33; color: white;">
            <h1>❌ Error</h1>
            <p>No se recibió ningún código.</p>
        </body>
        </html>
        """
    return web.Response(text=html, content_type="text/html")


def get_code(user_id: str):
    return pending_codes.pop(user_id, None)


async def start_web_server():
    app = web.Application()
    app.router.add_get("/callback", handle_callback)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"[OK] Web server started on port {port}")
