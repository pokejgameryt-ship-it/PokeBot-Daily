import os

DISCORD_TOKEN = os.getenv("POKEBOT_TOKEN", "")
if not DISCORD_TOKEN:
    try:
        with open(".token", "r") as f:
            DISCORD_TOKEN = f.read().strip()
    except FileNotFoundError:
        pass

TRIVIA_CHANNEL_ID = 1516733719191228416
TRIVIA_CHANNEL_NAME = "🔴｜comandos-pokebot"
RETO_CHANNEL_NAME = "retos-semanales"
HALL_OF_FAME_CHANNEL_NAME = "hall-of-fame"

TRIVIA_HOUR = 10
TRIVIA_MINUTE = 0

REWARD_ROLES = {
    7: "🔥 Activo",
    30: "⭐ Veterano",
    100: "🏆 Leyenda",
}

TRIVIA_POINTS = {
    "correct": 10,
    "streak_bonus": 5,
}

RETO_POINTS = {
    "completed": 50,
}

MIEMBRO_ROLE_ID = 1519384320886706296

TWITCH_VIP_ROLE_ID = 838388782612086814

TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID", "")
TWITCH_CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET", "")
TWITCH_BROADCASTER_ID = os.getenv("TWITCH_BROADCASTER_ID", "1134721153")

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")
YOUTUBE_CHANNEL_ID = os.getenv("YOUTUBE_CHANNEL_ID", "UCY-yUwAx1C0ApRHWKdo8o0Q")

DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID", "1519386835514560734")
DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET", "r16QgnGBt_ujCZ6ZYvU_BQr43x6y5e3k")
DISCORD_REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI", "https://pokejgameryt-ship-it.github.io/PokeBot-Daily/callback.html")
