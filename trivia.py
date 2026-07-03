import random
import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime
import database as db
from config import TRIVIA_POINTS, TRIVIA_CHANNEL_ID, STREAK_ROLE_ID

DIFFICULTY_CONFIG = {
    "easy": {"label": "Fácil", "emoji": "🟢", "points": 5, "color": discord.Color.green()},
    "medium": {"label": "Intermedia", "emoji": "🟡", "points": 10, "color": discord.Color.gold()},
    "hard": {"label": "Difícil", "emoji": "🔴", "points": 15, "color": discord.Color.red()},
}

import hashlib
import json

TRIVIA_STORE = {}


class TriviaView(discord.ui.View):
    def __init__(self, correct_answer: str, trivia_id: int, options: list, difficulty: str):
        super().__init__(timeout=None)
        self.correct_answer = correct_answer
        self.trivia_id = trivia_id
        self.options = options
        self.difficulty = difficulty
        self.responders = set()
        self.message = None
        TRIVIA_STORE[trivia_id] = {
            "correct": correct_answer,
            "options": options,
            "difficulty": difficulty,
            "responders": self.responders,
        }

    @discord.ui.button(label="A", style=discord.ButtonStyle.primary, custom_id="trivia_btn_a")
    async def option_a(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.check_answer(interaction, 0)

    @discord.ui.button(label="B", style=discord.ButtonStyle.primary, custom_id="trivia_btn_b")
    async def option_b(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.check_answer(interaction, 1)

    @discord.ui.button(label="C", style=discord.ButtonStyle.primary, custom_id="trivia_btn_c")
    async def option_c(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.check_answer(interaction, 2)

    async def check_answer(self, interaction: discord.Interaction, index: int):
        trivia_id = self.trivia_id
        store = TRIVIA_STORE.get(trivia_id)
        if not store:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="⏰ Trivia expirada",
                    description="Esta trivia ya no está activa. Escribe **!trivia** para la de hoy.",
                    color=discord.Color.orange(),
                ),
                ephemeral=True,
            )
            return

        uid = interaction.user.id
        if uid in store["responders"]:
            await interaction.response.send_message(
                "Ya has respondido esta trivia.", ephemeral=True
            )
            return

        store["responders"].add(uid)

        options = store["options"]
        correct = store["correct"]
        difficulty = store["difficulty"]
        selected_option = options[index]
        is_correct = selected_option == correct
        points = DIFFICULTY_CONFIG[difficulty]["points"]

        if is_correct:
            db.update_score(uid, points, interaction.user.display_name)
            streak_change = db.update_trivia_stats(uid, True, interaction.user.display_name)
            db.mark_trivia_answered(trivia_id, uid)
            score = db.get_total_score(uid)
            streak = db.get_streak(uid)

            if streak_change["old_streak"] == 0 and streak_change["new_streak"] > 0:
                role = interaction.guild.get_role(STREAK_ROLE_ID)
                if role:
                    await interaction.user.add_roles(role)

            embed = discord.Embed(
                title=f"✅ ¡Correcto! {DIFFICULTY_CONFIG[difficulty]['emoji']}",
                description=f"La respuesta **{correct}** es correcta.",
                color=discord.Color.green(),
            )
            embed.add_field(name="Dificultad", value=DIFFICULTY_CONFIG[difficulty]["label"])
            embed.add_field(name="Puntos ganados", value=f"+{points}")
            embed.add_field(name="Puntos totales", value=str(score))
            embed.add_field(name="Racha actual", value=f"{streak} 🔥")
            embed.set_footer(text="Solo tú puedes ver esta respuesta")
        else:
            streak_change = db.update_trivia_stats(uid, False, interaction.user.display_name)
            db.mark_trivia_answered(trivia_id, uid)

            if streak_change["old_streak"] > 0 and streak_change["new_streak"] == 0:
                role = interaction.guild.get_role(STREAK_ROLE_ID)
                if role:
                    await interaction.user.remove_roles(role)

            embed = discord.Embed(
                title=f"❌ Incorrecto {DIFFICULTY_CONFIG[difficulty]['emoji']}",
                description=f"Tu respuesta: **{selected_option}**\nLa correcta: **{correct}**",
                color=discord.Color.red(),
            )
            embed.add_field(name="Dificultad", value=DIFFICULTY_CONFIG[difficulty]["label"])
            embed.set_footer(text="Solo tú puedes ver esta respuesta")

        await interaction.response.send_message(embed=embed, ephemeral=True)


class WeeklyQuizView(discord.ui.View):
    def __init__(self, questions: list, week_key: str):
        super().__init__(timeout=None)
        self.questions = questions
        self.week_key = week_key
        self.user_responses = {}

    @discord.ui.button(label="✅ Verdadero", style=discord.ButtonStyle.green, custom_id="wq_true")
    async def true_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_answer(interaction, True)

    @discord.ui.button(label="❌ Falso", style=discord.ButtonStyle.red, custom_id="wq_false")
    async def false_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_answer(interaction, False)

    async def process_answer(self, interaction: discord.Interaction, answer: bool):
        uid = interaction.user.id

        if uid not in self.user_responses:
            self.user_responses[uid] = {"answers": [], "current": 0}

        user_data = self.user_responses[uid]
        idx = user_data["current"]

        if idx >= len(self.questions):
            await interaction.response.send_message(
                "Ya has completado el quiz semanal.", ephemeral=True
            )
            return

        user_data["answers"].append(answer)
        user_data["current"] += 1

        if user_data["current"] >= len(self.questions):
            await self.finish_quiz(interaction, uid)
        else:
            q = self.questions[user_data["current"]]
            embed = discord.Embed(
                title=f"📋 Quiz Semanal - Pregunta {user_data['current'] + 1}/{len(self.questions)}",
                description=f"**{q['question']}**",
                color=discord.Color.blue(),
            )
            embed.set_footer(text=f"Respuestas: {user_data['current']}/{len(self.questions)}")
            await interaction.response.edit_message(embed=embed, view=self)

    async def finish_quiz(self, interaction: discord.Interaction, uid: int):
        user_data = self.user_responses[uid]
        correct = 0
        for i, q in enumerate(self.questions):
            if i < len(user_data["answers"]) and user_data["answers"][i] == q["answer"]:
                correct += 1

        if correct == 10:
            points = 50
        elif correct >= 7:
            points = 20
        elif correct >= 5:
            points = 10
        else:
            points = 5

        member = interaction.guild.get_member(uid)
        username = member.display_name if member else "Unknown"
        db.update_score(uid, points, username)
        db.save_weekly_quiz_answer(self.week_key, uid, user_data["answers"], correct, username)

        embed = discord.Embed(
            title="🎉 Quiz Semanal Completado",
            description=f"Has acertado **{correct}/10** preguntas",
            color=discord.Color.green() if correct >= 7 else discord.Color.orange(),
        )
        embed.add_field(name="Puntos ganados", value=f"+{points}")
        embed.add_field(name="Total", value=str(db.get_total_score(uid)))

        result_text = ""
        for i, q in enumerate(self.questions):
            user_ans = user_data["answers"][i] if i < len(user_data["answers"]) else None
            correct_emoji = "✅" if user_ans == q["answer"] else "❌"
            result_text += f"{correct_emoji} {q['question']}\n"
        embed.add_field(name="Resultados", value=result_text, inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)


TRUE_FALSE_QUESTIONS = [
    {"question": "Pikachu es de tipo Eléctrico", "answer": True},
    {"question": "Pikachu es de tipo Normal", "answer": False},
    {"question": "Charizard es de tipo Fuego/Volador", "answer": True},
    {"question": "Charizard es de tipo Dragón", "answer": False},
    {"question": "Mewtwo es un Pokémon legendario", "answer": True},
    {"question": "Mewtwo es de tipo Fantasma", "answer": False},
    {"question": "Bulbasaur es de tipo Planta/Veneno", "answer": True},
    {"question": "Bulbasaur es de tipo Planta/Fuego", "answer": False},
    {"question": "La Pokédex Nacional de Gen 1 tiene 151 Pokémon", "answer": True},
    {"question": "Eevee evoluciona en 8 formas diferentes", "answer": True},
    {"question": "Garchomp es de tipo Dragón/Tierra", "answer": True},
    {"question": "Garchomp es de tipo Dragón/Lucha", "answer": False},
    {"question": "Lucario es de tipo Lucha/Acero", "answer": True},
    {"question": "Lucario es de tipo Acero/Dragón", "answer": False},
    {"question": "Rayquaza es un Pokémon legendario de tipo Dragón/Volador", "answer": True},
    {"question": "Gengar es de tipo Fantasma/Veneno", "answer": True},
    {"question": "El Movimiento Hidroariete es de tipo Agua", "answer": True},
    {"question": "Snorlax tiene la mayor defensa base de Gen 1", "answer": False},
    {"question": "Blissey tiene más HP que Chansey", "answer": True},
    {"question": "El Pokémon más alto es Wailord", "answer": True},
    {"question": "Mew es de tipo Psíquico", "answer": True},
    {"question": "Arceus es el Pokémon más fuerte de todos", "answer": False},
    {"question": "Ditto puede transformarse en cualquier Pokémon", "answer": True},
    {"question": "Shedinja tiene solo 1 PS", "answer": True},
    {"question": "El Movimiento Terremoto es de tipo Tierra", "answer": True},
    {"question": "Gardevoir es de tipo Psíquico/Hada", "answer": True},
    {"question": "Steelix es más pesado que Onix", "answer": True},
    {"question": "El Movimiento Lanzallamas es de tipo Fuego", "answer": True},
    {"question": "Palkia controla el espacio", "answer": True},
    {"question": "Giratina controla el tiempo", "answer": False},
    {"question": "Darkrai causa pesadillas", "answer": True},
    {"question": "Cresselia es de tipo Psíquico", "answer": True},
    {"question": "El Movimiento Psíquico es de tipo Psíquico", "answer": True},
    {"question": "Scizor es de tipo Bicho/Acero", "answer": True},
    {"question": "Scizor es de tipo Bicho/Volador", "answer": False},
    {"question": "Tyranitar es de tipo Roca/Siniestro", "answer": True},
    {"question": "Tyranitar es de tipo Roca/Dragón", "answer": False},
    {"question": "Blaziken es de tipo Fuego/Lucha", "answer": True},
    {"question": "Blaziken es de tipo Fuego/Volador", "answer": False},
    {"question": "Swampert es de tipo Agua/Tierra", "answer": True},
    {"question": "Swampert es de tipo Agua/Roca", "answer": False},
    {"question": "Sceptile es de tipo Planta", "answer": True},
    {"question": "Sceptile es de tipo Planta/Dragón", "answer": False},
    {"question": "Metagross es de tipo Acero/Psíquico", "answer": True},
    {"question": "Metagross es de tipo Acero/Dragón", "answer": False},
    {"question": "Salamence es de tipo Dragón/Volador", "answer": True},
    {"question": "Salamence es de tipo Dragón/Lucha", "answer": False},
    {"question": "Alakazam es de tipo Psíquico", "answer": True},
    {"question": "Alakazam es de tipo Lucha", "answer": False},
    {"question": "Machamp es de tipo Lucha", "answer": True},
    {"question": "Machamp es de tipo Psíquico", "answer": False},
    {"question": "Golem es de tipo Roca/Tierra", "answer": True},
    {"question": "Golem es de tipo Roca/Fuego", "answer": False},
    {"question": "El Movimiento Surf es de tipo Agua", "answer": True},
    {"question": "Dragonite es de tipo Dragón/Volador", "answer": True},
    {"question": "Dragonite es de tipo Dragón/Fuego", "answer": False},
    {"question": "Blastoise es de tipo Agua", "answer": True},
    {"question": "Blastoise es de tipo Planta", "answer": False},
    {"question": "Venusaur es de tipo Planta/Veneno", "answer": True},
    {"question": "Venusaur es de tipo Fuego", "answer": False},
    {"question": "El Movimiento Rayo es de tipo Eléctrico", "answer": True},
    {"question": "El Movimiento Rayo es de tipo Normal", "answer": False},
    {"question": "El Movimiento Bofetada Lodo es de tipo Veneno", "answer": True},
    {"question": "El Movimiento Aerial Ace es de tipo Volador", "answer": True},
    {"question": "El Movimiento Colmillo Ígneo es de tipo Fuego", "answer": True},
    {"question": "El Movimiento Danza Espada es de tipo Normal", "answer": True},
    {"question": "Pikachu es el Pokémon más rápido de Gen 1", "answer": False},
    {"question": "Mewtwo tiene el stat base de ataque más alto de Gen 1", "answer": False},
    {"question": "Snorlax es de tipo Normal", "answer": True},
    {"question": "Eevee es de tipo Normal", "answer": True},
    {"question": "Gyarados es de tipo Agua/Volador", "answer": True},
    {"question": "Gyarados es de tipo Dragón", "answer": False},
    {"question": "Charizard es de tipo Fuego/Volador", "answer": True},
    {"question": "Charizard es de tipo Dragón", "answer": False},
    {"question": "Rayquaza es de tipo Dragón/Volador", "answer": True},
    {"question": "Rayquaza es de tipo Dragón/Fuego", "answer": False},
    {"question": "Groudon es de tipo Tierra", "answer": True},
    {"question": "Groudon es de tipo Tierra/Fuego", "answer": False},
    {"question": "Kyogre es de tipo Agua", "answer": True},
    {"question": "Kyogre es de tipo Agua/Psíquico", "answer": False},
    {"question": "Dialga es de tipo Acero/Dragón", "answer": True},
    {"question": "Dialga es de tipo Dragón/Psíquico", "answer": False},
    {"question": "Palkia es de tipo Agua/Dragón", "answer": True},
    {"question": "Palkia es de tipo Dragón/Volador", "answer": False},
    {"question": "Giratina es de tipo Fantasma/Dragón", "answer": True},
    {"question": "Giratina es de tipo Siniestro/Dragón", "answer": False},
    {"question": "Arceus es de tipo Normal", "answer": True},
    {"question": "Arceus es de tipo Psíquico", "answer": False},
    {"question": "El Movimiento Hoja Afilada es de tipo Planta", "answer": True},
    {"question": "El Movimiento Hoja Afilada es de tipo Normal", "answer": False},
    {"question": "El Movimiento Danza Espada es de tipo Normal", "answer": True},
    {"question": "El Movimiento Danza Espada es de tipo Lucha", "answer": False},
]


class Trivia(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.weekly_quiz_task.start()

    def cog_unload(self):
        self.weekly_quiz_task.cancel()

    @tasks.loop(hours=24)
    async def weekly_quiz_task(self):
        now = datetime.now()
        if now.weekday() != 0:
            return
        if now.hour != 10 or now.minute != 0:
            return

        guild = self.bot.guilds[0] if self.bot.guilds else None
        if not guild:
            return

        from config import RETO_CHANNEL_ID
        channel = guild.get_channel(RETO_CHANNEL_ID)
        if not channel:
            return

        existing = db.get_active_weekly_quiz()
        if existing:
            return

        from question_gen import get_weekly_questions
        questions = get_weekly_questions(TRUE_FALSE_QUESTIONS, 10)
        week_key = now.strftime("%Y-W%W")
        db.save_weekly_quiz(questions, week_key)

        embed = discord.Embed(
            title="🎯 Quiz Semanal de Pokémon",
            description="¡10 preguntas de Verdadero o Falso! Responde todas para ganar puntos.\n\n"
                       "10/10 = **50 puntos** | 7-9 = **20 puntos** | 5-6 = **10 puntos** | 1-4 = **5 puntos**\n\n"
                       " Usa los botones para responder. ¡Buena suerte!",
            color=discord.Color.gold(),
        )
        embed.set_footer(text="Cada pregunta se envía por separado (ephemeral)")

        view = WeeklyQuizView(questions, week_key)
        await channel.send(embed=embed, view=view)

    @weekly_quiz_task.before_loop
    async def before_weekly_quiz(self):
        await self.bot.wait_until_ready()

    @commands.command(name="trivia")
    async def trivia_command(self, ctx: commands.Context):
        daily = db.get_daily_trivia()
        if daily and daily.get("option1"):
            options = [daily["option1"], daily["option2"], daily["option3"]]
            random.shuffle(options)
            difficulty = "medium"
            correct = daily["correct_answer"]
            view = TriviaView(correct, daily["id"], options, difficulty)
            embed = discord.Embed(
                title="🎮 Trivia Pokémon del Día",
                description=daily["question"],
                color=discord.Color.blue(),
            )
            embed.add_field(name="Dificultad", value="Intermedia")
            embed.add_field(name="Puntos", value="10")
            embed.add_field(name="A", value=options[0], inline=False)
            embed.add_field(name="B", value=options[1], inline=False)
            embed.add_field(name="C", value=options[2], inline=False)
            embed.set_footer(text="Haz click en una opción para responder. Disponible hasta mañana a las 10:00.")
            msg = await ctx.send(embed=embed, view=view)
            view.message = msg
            return

        from pokeapi_trivia import generate_daily_trivia

        difficulty = random.choice(["easy", "medium", "hard"])
        trivia = generate_daily_trivia()
        if not trivia:
            await ctx.send("❌ No se pudo generar la pregunta. Inténtalo de nuevo.")
            return
        options = trivia["options"][:]
        random.shuffle(options)

        db.save_trivia_question(trivia["question"], trivia["correct"], options)

        diff_config = DIFFICULTY_CONFIG[difficulty]
        embed = discord.Embed(
            title=f"🎮 Trivia Pokémon del Día {diff_config['emoji']}",
            description=trivia["question"],
            color=diff_config["color"],
        )
        embed.add_field(name="Dificultad", value=diff_config["label"])
        embed.add_field(name="Puntos", value=str(diff_config["points"]))
        embed.add_field(name="A", value=options[0], inline=False)
        embed.add_field(name="B", value=options[1], inline=False)
        embed.add_field(name="C", value=options[2], inline=False)
        embed.set_footer(text="Tienes hasta mañana a las 10:00 para responder.")

        daily = db.get_daily_trivia()
        view = TriviaView(trivia["correct"], daily["id"], options, difficulty)
        msg = await ctx.send(embed=embed, view=view)
        view.message = msg

    @app_commands.command(name="trivia", description="Juega la trivia Pokémon del día")
    async def trivia_slash(self, interaction: discord.Interaction):
        daily = db.get_daily_trivia()
        if daily and daily.get("option1"):
            options = [daily["option1"], daily["option2"], daily["option3"]]
            random.shuffle(options)
            difficulty = "medium"
            correct = daily["correct_answer"]
            view = TriviaView(correct, daily["id"], options, difficulty)
            embed = discord.Embed(
                title="🎮 Trivia Pokémon del Día",
                description=daily["question"],
                color=discord.Color.blue(),
            )
            embed.add_field(name="Dificultad", value="Intermedia")
            embed.add_field(name="Puntos", value="10")
            embed.add_field(name="A", value=options[0], inline=False)
            embed.add_field(name="B", value=options[1], inline=False)
            embed.add_field(name="C", value=options[2], inline=False)
            embed.set_footer(text="Haz click en una opción para responder. Disponible hasta mañana a las 10:00.")
            await interaction.response.send_message(embed=embed, view=view)
            msg = await interaction.original_response()
            view.message = msg
            return

        from pokeapi_trivia import generate_daily_trivia

        difficulty = random.choice(["easy", "medium", "hard"])
        trivia = generate_daily_trivia()
        if not trivia:
            await interaction.response.send_message("❌ No se pudo generar la pregunta. Inténtalo de nuevo.")
            return
        options = trivia["options"][:]
        random.shuffle(options)

        db.save_trivia_question(trivia["question"], trivia["correct"], options)

        diff_config = DIFFICULTY_CONFIG[difficulty]
        embed = discord.Embed(
            title=f"🎮 Trivia Pokémon del Día {diff_config['emoji']}",
            description=trivia["question"],
            color=diff_config["color"],
        )
        embed.add_field(name="Dificultad", value=diff_config["label"])
        embed.add_field(name="Puntos", value=str(diff_config["points"]))
        embed.add_field(name="A", value=options[0], inline=False)
        embed.add_field(name="B", value=options[1], inline=False)
        embed.add_field(name="C", value=options[2], inline=False)
        embed.set_footer(text="Tienes hasta mañana a las 10:00 para responder.")

        daily = db.get_daily_trivia()
        view = TriviaView(trivia["correct"], daily["id"], options, difficulty)
        await interaction.response.send_message(embed=embed, view=view)
        msg = await interaction.original_response()
        view.message = msg

    @commands.command(name="leaderboard")
    async def leaderboard_command(self, ctx: commands.Context):
        leaders = db.get_trivia_leaderboard(10)
        if not leaders:
            await ctx.send("Aún no hay datos de trivia.")
            return

        embed = discord.Embed(
            title="🏆 Leaderboard de Trivia",
            description="Los mejores jugadores de trivia Pokémon",
            color=discord.Color.gold(),
        )

        medals = ["🥇", "🥈", "🥉"]
        for i, user in enumerate(leaders):
            medal = medals[i] if i < 3 else f"#{i+1}"
            accuracy = user["accuracy"]
            embed.add_field(
                name=f"{medal} {user['username']}",
                value=f"✅ {user['trivia_correct']}/{user['trivia_total']} ({accuracy:.1f}%)",
                inline=False,
            )

        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Trivia(bot))
