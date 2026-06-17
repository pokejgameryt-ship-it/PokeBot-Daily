import os

DISCORD_TOKEN = os.getenv("POKEBOT_TOKEN", "")
if not DISCORD_TOKEN:
    try:
        with open(".token", "r") as f:
            DISCORD_TOKEN = f.read().strip()
    except FileNotFoundError:
        pass

TRIVIA_CHANNEL_NAME = "🔴｜comandos-pokebot"
RETO_CHANNEL_NAME = "retos-semanales"
HALL_OF_FAME_CHANNEL_NAME = "hall-of-fame"

TRIVIA_HOUR = 12
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
