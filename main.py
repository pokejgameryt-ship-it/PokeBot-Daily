import sys
import io
import asyncio
import logging
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s")

import discord
from discord.ext import commands, tasks
from datetime import datetime, timezone, timedelta
import database as db
from config import (
    DISCORD_TOKEN,
    TRIVIA_CHANNEL_ID,
    TRIVIA_CHANNEL_NAME,
    TRIVIA_HOUR,
    TRIVIA_MINUTE,
    REWARD_ROLES,
    STREAK_ROLE_ID,
)

TZ_SPAIN = timezone(timedelta(hours=2))

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

ALLOWED_CHANNEL_ID = 1516733719191228416
COMMANDS_ALLOWED_CHANNELS = ["enviar-verificacion", "verificar-todos"]


@bot.check
async def check_channel(ctx):
    if ctx.command.name in COMMANDS_ALLOWED_CHANNELS:
        return True
    if ctx.channel.id != ALLOWED_CHANNEL_ID:
        await ctx.send(
            f"❌ Este comando solo funciona en <#{ALLOWED_CHANNEL_ID}>",
            delete_after=5,
        )
        return False
    return True


@bot.event
async def on_ready():
    db.init_db()
    
    # Cargar cogs
    await bot.load_extension("trivia")
    await bot.load_extension("reto")
    await bot.load_extension("verify")
    
    print(f"✅ {bot.user} está online y listo para funcionar.")
    print(f"📊 Base de datos inicializada.")
    daily_trivia_task.start()
    streak_reminder_task.start()
    reset_stale_streaks_task.start()
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

ROLE_VERIFICADO = 1519384320886706296
ROLE_MIEMBRO = 1516763647765123094
ROLE_COMBO = 1519391637170553033


@bot.event
async def on_member_update(before, after):
    if before.roles == after.roles:
        return
    role_verificado = after.guild.get_role(ROLE_VERIFICADO)
    role_miembro = after.guild.get_role(ROLE_MIEMBRO)
    role_combo = after.guild.get_role(ROLE_COMBO)
    if not role_verificado or not role_miembro or not role_combo:
        return
    has_both = role_verificado in after.roles and role_miembro in after.roles
    has_combo = role_combo in after.roles
    if has_both and not has_combo:
        await after.add_roles(role_combo)
    elif not has_both and has_combo:
        await after.remove_roles(role_combo)


@bot.command(name="dar-miembros")
@commands.has_permissions(administrator=True)
async def dar_miembros_command(ctx: commands.Context):
    """Asigna el rol 'Miembro' a todos los miembros que no lo tengan (solo admins)"""
    role = ctx.guild.get_role(1516763647765123094)
    if not role:
        await ctx.send("❌ No encontré el rol 'Miembro'.")
        return
    
    embed = discord.Embed(
        title="⏳ Asignando rol Miembro...",
        description="Esto puede tardar unos segundos.",
        color=discord.Color.yellow(),
    )
    msg = await ctx.send(embed=embed)
    
    count = 0
    for member in ctx.guild.members:
        if role not in member.roles and not member.bot:
            try:
                await member.add_roles(role)
                count += 1
            except:
                pass
    
    embed = discord.Embed(
        title="✅ Rol Miembro Asignado",
        description=f"Se asignó el rol **Miembro** a **{count}** miembros.",
        color=discord.Color.green(),
    )
    await msg.edit(embed=embed)


@tasks.loop(minutes=1)
async def daily_trivia_task():
    now = datetime.now(TZ_SPAIN)
    if now.hour != TRIVIA_HOUR or now.minute != TRIVIA_MINUTE:
        return

    try:
        guild = bot.guilds[0] if bot.guilds else None
        if not guild:
            return

        channel = guild.get_channel(TRIVIA_CHANNEL_ID)
        if not channel:
            return

        from trivia import TriviaView, TRIVIA_EASY, TRIVIA_MEDIUM, TRIVIA_HARD, DIFFICULTY_CONFIG
        from question_gen import get_trivia_question
        import random

        difficulty = random.choice(["easy", "medium", "hard"])
        pool = {"easy": TRIVIA_EASY, "medium": TRIVIA_MEDIUM, "hard": TRIVIA_HARD}
        trivia = get_trivia_question(difficulty, pool[difficulty])
        if not trivia:
            logging.error("get_trivia_question returned None")
            return

        options = trivia["options"][:]
        random.shuffle(options)

        db.save_trivia_question(trivia["question"], trivia["correct"], options)

        daily = db.get_daily_trivia()
        if not daily:
            logging.error("get_daily_trivia returned None after save")
            return

        diff_config = DIFFICULTY_CONFIG[difficulty]

        greeting = "Buenos días entrenadores"
        if now.weekday() == 0:
            greeting = "Buenos días entrenadores 🎉 ¡Es lunes! Hoy toca trivia + ranking de la semana"

        embed = discord.Embed(
            title=f"🎯 {greeting} {diff_config['emoji']}",
            description=f"**{trivia['question']}**",
            color=diff_config["color"],
        )
        embed.add_field(name="Dificultad", value=diff_config["label"])
        embed.add_field(name="Puntos", value=str(diff_config["points"]))
        embed.add_field(name="A", value=options[0], inline=False)
        embed.add_field(name="B", value=options[1], inline=False)
        embed.add_field(name="C", value=options[2], inline=False)
        embed.set_footer(text="Usa los botones para responder. Tienes 60 segundos.")

        view = TriviaView(trivia["correct"], daily["id"], options, difficulty)
        await channel.send(embed=embed, view=view)

        if now.weekday() == 0:
            await asyncio.sleep(2)

            leaders = db.get_leaderboard(10)
            if leaders:
                embed_global = discord.Embed(
                    title="🏆 Ranking Global de Puntos",
                    description="Los miembros más activos del servidor",
                    color=discord.Color.gold(),
                )
                medals = ["🥇", "🥈", "🥉"]
                for i, user in enumerate(leaders):
                    medal = medals[i] if i < 3 else f"#{i+1}"
                    embed_global.add_field(
                        name=f"{medal} {user['username']}",
                        value=f"{user['total_score']} pts | Trivia: {user['trivia_correct']}/{user['trivia_total']}",
                        inline=False,
                    )
                await channel.send(embed=embed_global)

            trivia_leaders = db.get_trivia_leaderboard(10)
            if trivia_leaders:
                embed_trivia = discord.Embed(
                    title="🧠 Ranking Trivia Semanal",
                    description="Los mejores en trivia esta semana",
                    color=discord.Color.purple(),
                )
                for i, user in enumerate(trivia_leaders):
                    medal = medals[i] if i < 3 else f"#{i+1}"
                    accuracy = user["accuracy"]
                    embed_trivia.add_field(
                        name=f"{medal} {user['username']}",
                        value=f"{user['trivia_correct']}/{user['trivia_total']} ({accuracy:.1f}%)",
                        inline=False,
                    )
                await channel.send(embed=embed_trivia)

            streak_leaders = db.get_streak_leaderboard(10)
            if streak_leaders:
                embed_streak = discord.Embed(
                    title="🔥 Ranking de Rachas",
                    description="Los miembros con las mejores rachas activas",
                    color=discord.Color.orange(),
                )
                for i, user in enumerate(streak_leaders):
                    medal = medals[i] if i < 3 else f"#{i+1}"
                    embed_streak.add_field(
                        name=f"{medal} {user['username']}",
                        value=f"{user['current_streak']} días 🔥 | Mejor: {user.get('best_streak', 0)} ⭐",
                        inline=False,
                    )
                await channel.send(embed=embed_streak)

    except Exception as e:
        logging.exception(f"Error in daily_trivia_task: {e}")


@daily_trivia_task.before_loop
async def before_daily_trivia():
    await bot.wait_until_ready()


@tasks.loop(minutes=30)
async def streak_reminder_task():
    users = db.get_users_needing_reminder()
    for user_data in users:
        try:
            user = await bot.fetch_user(user_data["user_id"])
            if user:
                await user.send(
                    f"¡Hola {user_data['username']}! 🔥\n\n"
                    f"¡Tienes una racha de **{user_data['current_streak']} días** en peligro! "
                    f"Si no respondes la trivia de hoy, podrías perderla.\n\n"
                    f"¡Ve a <#{ALLOWED_CHANNEL_ID}> y responde la pregunta del día para mantener tu racha! 💪"
                )
        except Exception as e:
            print(f"⚠️ No se pudo enviar DM a {user_data['username']}: {e}")


@streak_reminder_task.before_loop
async def before_streak_reminder():
    await bot.wait_until_ready()


@tasks.loop(hours=1)
async def reset_stale_streaks_task():
    reset_users = db.reset_stale_streaks()
    if reset_users:
        guild = bot.guilds[0] if bot.guilds else None
        if guild:
            role = guild.get_role(STREAK_ROLE_ID)
            if role:
                for user_id in reset_users:
                    try:
                        member = guild.get_member(user_id)
                        if member and role in member.roles:
                            await member.remove_roles(role)
                    except Exception as e:
                        logging.warning(f"Could not remove streak role from {user_id}: {e}")


@reset_stale_streaks_task.before_loop
async def before_reset_stale_streaks():
    await bot.wait_until_ready()


@bot.command(name="checkin")
async def checkin_command(ctx: commands.Context):
    db.create_user(ctx.author.id, ctx.author.display_name)

    success = db.checkin(ctx.author.id)
    if not success:
        await ctx.send("Ya hiciste check-in hoy. Vuelve mañana.")
        return

    db.update_score(ctx.author.id, 5, ctx.author.display_name)
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


class PkquestButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="🎯 Crear Pregunta", style=discord.ButtonStyle.green, custom_id="pkquest_button")
    async def button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = PkquestModal()
        await interaction.response.send_modal(modal)


@bot.command(name="pkquest")
async def pkquest_command(ctx: commands.Context):
    """Abre el formulario para crear una pregunta de concurso"""
    view = PkquestButton()
    embed = discord.Embed(
        title="🎯 Pokéconcurso",
        description="Haz clic en el botón de abajo para crear una pregunta.",
        color=discord.Color.gold(),
    )
    await ctx.send(embed=embed, view=view)


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
