import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import discord
from discord.ext import commands, tasks
from datetime import datetime
import database as db
from config import (
    DISCORD_TOKEN,
    TRIVIA_CHANNEL_NAME,
    RETO_CHANNEL_NAME,
    TRIVIA_HOUR,
    TRIVIA_MINUTE,
    REWARD_ROLES,
)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    db.init_db()
    
    # Cargar cogs
    await bot.load_extension("trivia")
    await bot.load_extension("reto")
    
    print(f"✅ {bot.user} está online y listo para funcionar.")
    print(f"📊 Base de datos inicializada.")
    daily_trivia_task.start()
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.playing,
            name="Pokémon Trivia | !trivia",
        )
    )


@bot.event
async def on_member_join(member):
    db.create_user(member.id, member.display_name)
    channel = discord.utils.get(member.guild.text_channels, name="bienvenida")
    if channel:
        embed = discord.Embed(
            title=f"¡Bienvenido {member.display_name}!",
            description="Usa `!trivia` para jugar la trivia del día y ganar puntos.",
            color=discord.Color.green(),
        )
        await channel.send(embed=embed)


@tasks.loop(hours=24)
async def daily_trivia_task():
    now = datetime.now()
    if now.hour == TRIVIA_HOUR and now.minute == TRIVIA_MINUTE:
        guild = bot.guilds[0] if bot.guilds else None
        if not guild:
            return

        channel = discord.utils.get(guild.text_channels, name=TRIVIA_CHANNEL_NAME)
        if not channel:
            return

        import random

        POKEMON_TRIVIA = [
            {
                "question": "¿Cuál es el tipo de Pikachu?",
                "correct": "Eléctrico",
                "options": ["Eléctrico", "Fuego", "Normal"],
            },
            {
                "question": "¿Cuál es la evolución final de Charmander?",
                "correct": "Charizard",
                "options": ["Charmeleon", "Charizard", "Charmander"],
            },
            {
                "question": "¿De qué tipo es Bulbasaur?",
                "correct": "Planta/Veneno",
                "options": ["Planta/Veneno", "Agua/Planta", "Solo Planta"],
            },
            {
                "question": "¿Cuál es el tipo de Mewtwo?",
                "correct": "Psíquico",
                "options": ["Psíquico", "Fantasma", "Normal"],
            },
            {
                "question": "¿Qué Pokémon evoluciona con piedra fuego?",
                "correct": "Vulpix",
                "options": ["Vulpix", "Eevee", "Pikachu"],
            },
        ]

        trivia = random.choice(POKEMON_TRIVIA)
        options = trivia["options"][:]
        random.shuffle(options)

        db.save_trivia_question(trivia["question"], trivia["correct"], options)

        from trivia import TriviaView

        daily = db.get_daily_trivia()

        embed = discord.Embed(
            title="🎮 Trivia Pokémon del Día",
            description=trivia["question"],
            color=discord.Color.blue(),
        )
        embed.add_field(name="A", value=options[0], inline=False)
        embed.add_field(name="B", value=options[1], inline=False)
        embed.add_field(name="C", value=options[2], inline=False)
        embed.set_footer(text="Usa los botones para responder. Tienes 60 segundos.")

        correct_index = options.index(trivia["correct"])
        label = chr(65 + correct_index)

        view = TriviaView(label, daily["id"], 0)
        await channel.send(embed=embed, view=view)


@daily_trivia_task.before_loop
async def before_daily_trivia():
    await bot.wait_until_ready()


@bot.command(name="checkin")
async def checkin_command(ctx: commands.Context):
    db.create_user(ctx.author.id, ctx.author.display_name)

    success = db.checkin(ctx.author.id)
    if not success:
        await ctx.send("Ya hiciste check-in hoy. Vuelve mañana.")
        return

    db.update_score(ctx.author.id, 5)
    streak = db.get_streak(ctx.author.id)

    embed = discord.Embed(
        title="✅ Check-in Diario",
        description=f"**{ctx.author.display_name}** hizo check-in.",
        color=discord.Color.green(),
    )
    embed.add_field(name="Puntos ganados", value="+5")
    embed.add_field(name="Racha actual", value=f"{streak} días 🔥")

    if streak in REWARD_ROLES:
        role_name = REWARD_ROLES[streak]
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if role and role not in ctx.author.roles:
            await ctx.author.add_roles(role)
            embed.add_field(
                name="¡Nuevo rango!",
                value=f"Has desbloqueado el rol **{role_name}**",
            )

    await ctx.send(embed=embed)


@bot.command(name="top")
async def top_command(ctx: commands.Context):
    leaders = db.get_leaderboard(10)
    if not leaders:
        await ctx.send("Aún no hay datos.")
        return

    embed = discord.Embed(
        title="🏆 Top Miembros (Puntos Totales)",
        description="Los miembros más activos del servidor",
        color=discord.Color.gold(),
    )

    medals = ["🥇", "🥈", "🥉"]
    for i, user in enumerate(leaders):
        medal = medals[i] if i < 3 else f"#{i+1}"
        embed.add_field(
            name=f"{medal} {user['username']}",
            value=f"{user['total_score']} pts | Trivia: {user['trivia_correct']}/{user['trivia_total']} | Retos: {user['retos_completed']}",
            inline=False,
        )

    await ctx.send(embed=embed)


@bot.command(name="ranking-racha")
async def ranking_racha_command(ctx: commands.Context):
    leaders = db.get_leaderboard(10)
    if not leaders:
        await ctx.send("Aún no hay datos.")
        return

    # Ordenar por racha actual
    leaders_sorted = sorted(leaders, key=lambda x: x['current_streak'], reverse=True)

    embed = discord.Embed(
        title="🔥 Ranking de Racha (Check-in Diario)",
        description="Quién lleva más días consecutivos",
        color=discord.Color.orange(),
    )

    medals = ["🥇", "🥈", "🥉"]
    for i, user in enumerate(leaders_sorted[:10]):
        medal = medals[i] if i < 3 else f"#{i+1}"
        streak = user['current_streak']
        best = user['best_streak']
        if streak == 0:
            continue
        embed.add_field(
            name=f"{medal} {user['username']}",
            value=f"Racha actual: {streak} días 🔥 | Mejor: {best} ⭐",
            inline=False,
        )

    if len(embed.fields) == 0:
        embed.description = "Nadie tiene racha activa todavía."

    await ctx.send(embed=embed)


@bot.command(name="ranking-trivia")
async def ranking_trivia_command(ctx: commands.Context):
    leaders = db.get_trivia_leaderboard(10)
    if not leaders:
        await ctx.send("Aún no hay datos de trivia.")
        return

    embed = discord.Embed(
        title="🧠 Ranking de Trivia (Aciertos)",
        description="Quién tiene más respuestas correctas",
        color=discord.Color.purple(),
    )

    medals = ["🥇", "🥈", "🥉"]
    for i, user in enumerate(leaders):
        medal = medals[i] if i < 3 else f"#{i+1}"
        accuracy = user['accuracy']
        embed.add_field(
            name=f"{medal} {user['username']}",
            value=f"✅ {user['trivia_correct']}/{user['trivia_total']} ({accuracy:.1f}%)",
            inline=False,
        )

    await ctx.send(embed=embed)


@bot.command(name="comandos")
async def comandos_command(ctx: commands.Context):
    embed = discord.Embed(
        title="🎮 Comandos de PokéBot Daily",
        description="Usa estos comandos en este canal",
        color=discord.Color.blue(),
    )

    embed.add_field(
        name="━━━━━━ 🧠 TRIVIA ━━━━━━",
        value="━━━━━━━━━━━━━━━━━━━━━━━",
        inline=False,
    )
    embed.add_field(
        name="`!trivia`",
        value="Responde la trivia Pokémon del día y gana 10 puntos por acierto",
        inline=False,
    )
    embed.add_field(
        name="`!ranking-trivia`",
        value="Muestra quién tiene más aciertos en trivia",
        inline=False,
    )

    embed.add_field(
        name="━━━━━━ 🔥 RACHA ━━━━━━",
        value="━━━━━━━━━━━━━━━━━━━━━━━",
        inline=False,
    )
    embed.add_field(
        name="`!checkin`",
        value="Check-in diario. Mantén tu racha y gana 5 puntos cada día",
        inline=False,
    )
    embed.add_field(
        name="`!ranking-racha`",
        value="Muestra quién lleva más días consecutivos de check-in",
        inline=False,
    )

    embed.add_field(
        name="━━━━━━ 🏆 RANKINGS ━━━━━━",
        value="━━━━━━━━━━━━━━━━━━━━━━━",
        inline=False,
    )
    embed.add_field(
        name="`!top`",
        value="Top 10 miembros más activos por puntos totales",
        inline=False,
    )
    embed.add_field(
        name="`!leaderboard`",
        value="Ranking general con puntos, trivia y retos",
        inline=False,
    )

    embed.add_field(
        name="━━━━━━ 📊 PERFIL ━━━━━━",
        value="━━━━━━━━━━━━━━━━━━━━━━━",
        inline=False,
    )
    embed.add_field(
        name="`!profile`",
        value="Muestra tu perfil: puntos, trivia, racha y retos",
        inline=False,
    )
    embed.add_field(
        name="`!profile @usuario`",
        value="Muestra el perfil de otro miembro",
        inline=False,
    )

    embed.add_field(
        name="━━━━━━ 🎯 RETOS ━━━━━━",
        value="━━━━━━━━━━━━━━━━━━━━━━━",
        inline=False,
    )
    embed.add_field(
        name="`!reto`",
        value="Muestra el reto semanal activo y quiénes lo completaron",
        inline=False,
    )
    embed.add_field(
        name="`!completar-reto`",
        value="Marca el reto como completado y gana 50 puntos",
        inline=False,
    )
    embed.add_field(
        name="`!crear-reto [título] [desc] [puntos] [días]`",
        value="Crea un nuevo reto semanal (solo admins)",
        inline=False,
    )

    embed.add_field(
        name="━━━━━━ 🎯 POKÉCONCURSO ━━━━━━",
        value="━━━━━━━━━━━━━━━━━━━━━━━",
        inline=False,
    )
    embed.add_field(
        name="`!pkquest`",
        value="Abre un formulario para crear una pregunta de concurso",
        inline=False,
    )
    embed.add_field(
        name="`!ayuda-pkquest`",
        value="Muestra cómo crear preguntas de concurso",
        inline=False,
    )

    embed.set_footer(text="💡 Tip: Haz check-in todos los días para subir de rango")
    await ctx.send(embed=embed)


@bot.command(name="ayuda-pokebot")
async def help_command(ctx: commands.Context):
    embed = discord.Embed(
        title="📖 Comandos de PokéBot Daily",
        description="Todos los comandos disponibles",
        color=discord.Color.blue(),
    )
    embed.add_field(
        name="!trivia",
        value="Juega la trivia Pokémon del día",
        inline=False,
    )
    embed.add_field(
        name="!ranking-trivia",
        value="Ranking de aciertos en trivia",
        inline=False,
    )
    embed.add_field(
        name="!ranking-racha",
        value="Ranking de racha de check-in diario",
        inline=False,
    )
    embed.add_field(
        name="!leaderboard",
        value="Ranking general (puntos totales)",
        inline=False,
    )
    embed.add_field(
        name="!checkin",
        value="Check-in diario para mantener racha (+5 pts)",
        inline=False,
    )
    embed.add_field(
        name="!profile [@usuario]",
        value="Muestra tu perfil de estadísticas",
        inline=False,
    )
    embed.add_field(
        name="!top",
        value="Top 10 miembros más activos",
        inline=False,
    )
    embed.add_field(
        name="!reto",
        value="Muestra el reto semanal activo",
        inline=False,
    )
    embed.add_field(
        name="!completar-reto",
        value="Marca el reto como completado",
        inline=False,
    )
    embed.add_field(
        name="!crear-reto [título] [desc] [puntos] [días]",
        value="Crea un nuevo reto (solo admins)",
        inline=False,
    )
    await ctx.send(embed=embed)


class PkquestModal(discord.ui.Modal, title="🎯 Pokéconcurso - Crear Pregunta"):
    pregunta = discord.ui.TextInput(
        label="📝 Pregunta",
        placeholder="Escribe tu pregunta aquí...",
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=200,
    )
    opcion_correcta = discord.ui.TextInput(
        label="✅ Opción Correcta (en verde)",
        placeholder="Escribe la respuesta correcta...",
        style=discord.TextStyle.short,
        required=True,
        max_length=100,
    )
    opcion_incorrecta1 = discord.ui.TextInput(
        label="❌ Opción Incorrecta 1",
        placeholder="Escribe una opción incorrecta...",
        style=discord.TextStyle.short,
        required=True,
        max_length=100,
    )
    opcion_incorrecta2 = discord.ui.TextInput(
        label="❌ Opción Incorrecta 2",
        placeholder="Escribe una opción incorrecta...",
        style=discord.TextStyle.short,
        required=True,
        max_length=100,
    )
    opcion_incorrecta3 = discord.ui.TextInput(
        label="❌ Opción Incorrecta 3",
        placeholder="Escribe una opción incorrecta...",
        style=discord.TextStyle.short,
        required=True,
        max_length=100,
    )

    async def on_submit(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🎯 POKÉCONCURSO",
            description=f"**{self.pregunta}**",
            color=discord.Color.gold(),
        )
        
        embed.add_field(
            name="✅ Respuesta Correcta",
            value=f"```diff\n+ {self.opcion_correcta}\n```",
            inline=False,
        )
        
        embed.add_field(
            name="❌ Opción Incorrecta 1",
            value=f"```diff\n- {self.opcion_incorrecta1}\n```",
            inline=False,
        )
        
        embed.add_field(
            name="❌ Opción Incorrecta 2",
            value=f"```diff\n- {self.opcion_incorrecta2}\n```",
            inline=False,
        )
        
        embed.add_field(
            name="❌ Opción Incorrecta 3",
            value=f"```diff\n- {self.opcion_incorrecta3}\n```",
            inline=False,
        )
        
        embed.set_footer(text=f"Creado por {interaction.user.display_name}")
        
        await interaction.response.send_message(embed=embed)


@bot.command(name="pkquest")
async def pkquest_command(ctx: commands.Context):
    """Abre el formulario para crear una pregunta de concurso"""
    modal = PkquestModal()
    await ctx.send_modal(modal)


@bot.command(name="ayuda-pkquest")
async def ayuda_pkquest_command(ctx: commands.Context):
    embed = discord.Embed(
        title="🎯 Cómo crear preguntas de Pokéconcurso",
        description="Usa el comando `!pkquest` y se abrirá un formulario.",
        color=discord.Color.gold(),
    )
    embed.add_field(
        name="Cómo usar",
        value="Escribe `!pkquest` y se abrirá un modal con 5 campos:\n1. La pregunta\n2. La respuesta correcta (sale en verde)\n3. 3 opciones incorrectas (salen en rojo)",
        inline=False,
    )
    embed.add_field(
        name="Resultado",
        value="El bot publicará la pregunta con la respuesta correcta en verde y las incorrectas en rojo.",
        inline=False,
    )
    await ctx.send(embed=embed)


if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
