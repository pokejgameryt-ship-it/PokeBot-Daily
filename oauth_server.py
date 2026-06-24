import os
import json
import requests
from flask import Flask, request, redirect, jsonify
from threading import Thread

app = Flask(__name__)

DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID", "1519386835514560734")
DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET", "r16QgnGBt_ujCZ6ZYvU_BQr43x6y5e3k")
DISCORD_REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI", "http://localhost:3000/callback")

pending_verifications = {}


@app.route("/")
def index():
    return "PokeBot OAuth Server - OK"


@app.route("/callback")
def callback():
    code = request.args.get("code")
    state = request.args.get("state")

    if not code:
        return "Error: No code received", 400

    token_resp = requests.post(
        "https://discord.com/api/oauth2/token",
        data={
            "client_id": DISCORD_CLIENT_ID,
            "client_secret": DISCORD_CLIENT_SECRET,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": DISCORD_REDIRECT_URI,
        },
    )

    if token_resp.status_code != 200:
        return "Error exchanging token", 400

    access_token = token_resp.json()["access_token"]

    user_resp = requests.get(
        "https://discord.com/api/users/@me",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    connections_resp = requests.get(
        "https://discord.com/api/users/@me/connections",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    if user_resp.status_code != 200:
        return "Error getting user", 400

    user_data = user_resp.json()
    connections = connections_resp.json() if connections_resp.status_code == 200 else []

    pending_verifications[state] = {
        "user_id": user_data["id"],
        "username": user_data.get("username"),
        "connections": connections,
    }

    twitch = None
    youtube = None
    for conn in connections:
        if conn["type"] == "twitch":
            twitch = conn["name"]
        elif conn["type"] == "youtube":
            youtube = conn["name"]

    return f"""
    <html>
    <head><title>Verificación Discord</title></head>
    <body style="font-family: Arial; text-align: center; padding: 50px; background: #2C2F33; color: white;">
        <h1>✅ ¡Cuenta verificada!</h1>
        <p>Usuario: <strong>{user_data.get("username")}</strong></p>
        {'<p>Twitch: <strong>' + twitch + '</strong></p>' if twitch else ''}
        {'<p>YouTube: <strong>' + youtube + '</strong></p>' if youtube else ''}
        <p style="color: #aaa;">Puedes cerrar esta ventana y volver a Discord.</p>
    </body>
    </html>
    """


def get_verification(user_id: str) -> dict:
    return pending_verifications.pop(user_id, None)


def start_oauth_server():
    port = int(os.getenv("PORT", 3000))
    thread = Thread(target=lambda: app.run(host="0.0.0.0", port=port, debug=False), daemon=True)
    thread.start()
    print(f"[OK] OAuth server started on port {port}")
