import asyncio
import io
import logging
import os
import re
import sys
from logging.handlers import RotatingFileHandler

import psutil

if sys.stdout is not None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Logger propio (no root) para poder redirigir a fichero y filtrar secretos
logger = logging.getLogger("pokebot")
logger.setLevel(logging.INFO)
formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(name)s: %(message)s")

# Consola
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Fichero con rotación (logs/bot.log, 5 MB x 5)
os.makedirs("logs", exist_ok=True)
file_handler = RotatingFileHandler(
    "logs/bot.log", maxBytes=5_000_000, backupCount=5, encoding="utf-8"
)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Filtro para redactar tokens en logs
class SecretFilter(logging.Filter):
    TOKEN_PATTERNS = [
        (re.compile(r'"access_token"\s*:\s*"([^"]+)"'), '"access_token": "***"'),
        (re.compile(r'"refresh_token"\s*:\s*"([^"]+)"'), '"refresh_token": "***"'),
        (re.compile(r'Bearer\s+([A-Za-z0-9\-\._~]+)'), 'Bearer ***'),
        (re.compile(r'token=([A-Za-z0-9\-\._~]+)'), 'token=***'),
    ]
    def filter(self, record):
        try:
            msg = record.getMessage()
            for pattern, repl in self.TOKEN_PATTERNS:
                msg = pattern.sub(repl, msg)
            record.msg = msg
            record.args = ()
        except Exception:
            pass
        return True

for h in logger.handlers:
    h.addFilter(SecretFilter())

proc = psutil.Process()
try:
    proc.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
except AttributeError:
    proc.nice(1)
logger.info("Process priority set to BELOW_NORMAL. PID: %s", proc.pid)

import random as _random
from datetime import datetime, timedelta
try:
    from zoneinfo import ZoneInfo
    TZ_SPAIN = ZoneInfo("Europe/Madrid")
except Exception:
    from datetime import timezone
    TZ_SPAIN = timezone(timedelta(hours=2))

import discord
from discord import app_commands
from discord.ext import commands, tasks

import database as db
import leader
from config import (
    DISCORD_TOKEN,
    MIEMBRO_ROLE_ID,
    REWARD_ROLES,
    STREAK_ROLE_ID,
    TRIVIA_CHANNEL_ID,
    TRIVIA_HOUR,
    TRIVIA_MINUTE,
)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

ALLOWED_CHANNEL_ID = 1516733719191228416
COMMANDS_ALLOWED_CHANNELS = ["enviar-verificacion", "verificar-todos", "pkquest"]

_active_views = []


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


@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CheckFailure):
        return
    if isinstance(error, app_commands.CommandOnCooldown):
        await interaction.response.send_message(
            f"⏳ Comando en enfriamiento. Intenta en {error.retry_after:.0f}s.",
            ephemeral=True,
        )
        return
    logger.exception("Error en slash command %s: %s", interaction.command, error)
    if interaction.response.is_done():
        await interaction.followup.send("❌ Ha ocurrido un error interno.", ephemeral=True)
    else:
        await interaction.response.send_message("❌ Ha ocurrido un error interno.", ephemeral=True)


def slash_check_channel(interaction: discord.Interaction) -> bool:
    if interaction.command.name in COMMANDS_ALLOWED_CHANNELS:
        return True
    if interaction.channel.id != ALLOWED_CHANNEL_ID:
        raise app_commands.CheckFailure(
            f"Este comando solo funciona en <#{ALLOWED_CHANNEL_ID}>"
        )
    return True

# Aplicar check a todos los slash commands cargados después


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.CheckFailure):
        return
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Falta un argumento requerido: `{error.param.name}`")
        return
    if isinstance(error, commands.BadArgument):
        await ctx.send(f"❌ Argumento inválido: {error}")
        return
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"⏳ Comando en enfriamiento. Intenta en {error.retry_after:.0f}s.")
        return
    
    logger.exception("Error en comando %s: %s", ctx.command, error)
    await ctx.send("❌ Ha ocurrido un error interno. Se ha notificado al administrador.")


@bot.event
async def on_ready():
    db.init_db()
    
    print(f"✅ {bot.user} está online y listo para funcionar.")
    print("📊 Base de datos inicializada.")
    
    # Evitar reiniciar tasks en reconexiones (on_ready se dispara varias veces)
    if not daily_trivia_task.is_running():
        daily_trivia_task.start()
    if not streak_reminder_task.is_running():
        streak_reminder_task.start()
    if not reset_stale_streaks_task.is_running():
        reset_stale_streaks_task.start()
    
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.playing,
            name="Pokémon Trivia | !trivia",
        )
    )

    # === CATCH-UP: Ejecutar tareas perdidas mientras el PC estaba apagado ===
    now = datetime.now(TZ_SPAIN)
    today = now.date().isoformat()
    guild = bot.guilds[0] if bot.guilds else None

    if guild:
        # 1. Daily trivia perdida
        if now.hour >= TRIVIA_HOUR and db.get_daily_trivia() is None:
            if not db.was_startup_task_done("daily_trivia", today):
                try:
                    channel = guild.get_channel(TRIVIA_CHANNEL_ID)
                    if channel:
                        from pokeapi_trivia import generate_daily_trivia
                        from trivia import DIFFICULTY_CONFIG, TriviaView
                        difficulty = _random.choice(["easy", "medium", "hard"])
                        used_questions = db.get_used_questions()
                        trivia = generate_daily_trivia(used_questions)
                        if trivia:
                            options = trivia["options"][:]
                            _random.shuffle(options)
                            correct = trivia["correct"]
                            db.save_trivia_question(trivia["question"], correct, options)
                            db.mark_question_used(trivia["question"])
                            daily = db.get_daily_trivia()
                            if daily:
                                diff_config = DIFFICULTY_CONFIG[difficulty]
                                embed = discord.Embed(
                                    title=f"🎯 Buenos días entrenadores {diff_config['emoji']}",
                                    description=f"**{trivia['question']}**",
                                    color=diff_config["color"],
                                )
                                embed.add_field(name="Dificultad", value=diff_config["label"])
                                embed.add_field(name="Puntos", value=str(diff_config["points"]))
                                embed.add_field(name="A", value=options[0], inline=False)
                                embed.add_field(name="B", value=options[1], inline=False)
                                embed.add_field(name="C", value=options[2], inline=False)
                                embed.set_footer(text="Usa los botones para responder. Disponible hasta mañana a las 10:00.")
                                view = TriviaView(correct, daily["id"], options, difficulty)
                                msg = await channel.send(embed=embed, view=view)
                                view.message = msg
                                db.save_startup_task("daily_trivia", today)
                                logger.info("CATCHUP: Posted missed daily trivia")
                except Exception as e:
                    logger.error(f"CATCHUP error daily trivia: {e}")

        # 2. Weekly quiz perdida (lunes)
        if now.weekday() == 0 and now.hour >= 10:
            if not db.was_startup_task_done("weekly_quiz", today):
                try:
                    from trivia import WeeklyQuizStartView
                    week_key = now.strftime("%Y-W%W")
                    existing = db.get_active_weekly_quiz()
                    if not existing or existing["id"] != week_key:
                        from config import RETO_CHANNEL_ID
                        channel = guild.get_channel(RETO_CHANNEL_ID)
                        if channel:
                            used_questions = db.get_used_weekly_questions()
                            from trivia import TRUE_FALSE_QUESTIONS
                            available = [q for q in TRUE_FALSE_QUESTIONS if q["question"] not in used_questions]
                            if len(available) < 10:
                                available = TRUE_FALSE_QUESTIONS[:]
                            questions = _random.sample(available, 10)
                            db.save_weekly_quiz(questions, week_key)
                            for q in questions:
                                db.mark_weekly_question_used(q["question"])
                            embed = discord.Embed(
                                title="🎯 Quiz Semanal de Pokémon",
                                description=(
                                    "¡10 preguntas de Verdadero o Falso!\n\n"
                                    "**Puntuación:**\n"
                                    "10/10 = **50 puntos** 🏆\n"
                                    "7-9 = **20 puntos** 🥈\n"
                                    "5-6 = **10 puntos** 🥉\n"
                                    "1-4 = **5 puntos** 🎯\n\n"
                                    "Haz clic en el botón de abajo para empezar.\n"
                                    "Las preguntas se envían por MD.\n"
                                    "Disponible hasta el próximo lunes a las 10:00.\n"
                                    "Cada persona puede responder una vez."
                                ),
                                color=discord.Color.gold(),
                            )
                            embed.set_footer(text="Cada persona puede responder una vez")
                            view = WeeklyQuizStartView()
                            await channel.send(embed=embed, view=view)
                            db.save_startup_task("weekly_quiz", today)
                            logger.info(f"CATCHUP: Posted missed weekly quiz for {week_key}")
                except Exception as e:
                    logger.error(f"CATCHUP error weekly quiz: {e}")

        # 3. Check followers inmediato
        if not db.was_startup_task_done("check_followers", today):
            try:
                from verify import check_twitch_follow
                role = guild.get_role(MIEMBRO_ROLE_ID)
                if role:
                    verified_users = db.get_all_verified_users()
                    removed = 0
                    for user_data in verified_users:
                        if user_data.get("platform") != "twitch":
                            continue
                        username = user_data.get("username")
                        if not username or username == "auto-detected":
                            continue
                        member = guild.get_member(user_data["user_id"])
                        if not member:
                            continue
                        if not check_twitch_follow(username):
                            if role in member.roles:
                                await member.remove_roles(role)
                                db.set_verified(member.id, False, None, None)
                                removed += 1
                    if removed > 0:
                        logger.info(f"CATCHUP: Removed verification from {removed} unfollowers")
                    db.save_startup_task("check_followers", today)
            except Exception as e:
                logger.error(f"CATCHUP error check_followers: {e}")

        # 4. Reset streaks rotas
        if not db.was_startup_task_done("stale_streaks", today):
            try:
                broken_users = db.get_users_with_broken_streaks()
                role = guild.get_role(STREAK_ROLE_ID)
                for user_data in broken_users:
                    db.mark_streak_broken_notified(user_data["user_id"])
                    if role:
                        member = guild.get_member(user_data["user_id"])
                        if member and role in member.roles:
                            await member.remove_roles(role)
                    user = await bot.fetch_user(user_data["user_id"])
                    if user:
                        await user.send(
                            f"😢 ¡Hola {user_data['username']}!\n\n"
                            f"Tu racha de **{user_data['old_streak']} días** se ha roto. "
                            f"No respondiste la trivia en los últimos 2 días.\n\n"
                            f"¡No te preocupes! Empieza de nuevo hoy. Ve a <#{ALLOWED_CHANNEL_ID}> y escribe **!trivia** para recuperarla. 💪"
                        )
                db.save_startup_task("stale_streaks", today)
            except Exception as e:
                logger.error(f"CATCHUP error stale_streaks: {e}")

        # 5. Recordatorios de racha pendientes
        if not db.was_startup_task_done("streak_reminders", today):
            try:
                users = db.get_users_needing_reminder()
                for user_data in users:
                    user = await bot.fetch_user(user_data["user_id"])
                    if user:
                        db.mark_reminder_sent(user_data["user_id"])
                        await user.send(
                            f"¡Hola {user_data['username']}! 🔥\n\n"
                            f"¡Tienes una racha de **{user_data['current_streak']} días** en peligro! "
                            f"Si no respondes la trivia de hoy, podrías perderla.\n\n"
                            f"¡Ve a <#{ALLOWED_CHANNEL_ID}> y responde la pregunta del día para mantener tu racha! 💪"
                        )
                db.save_startup_task("streak_reminders", today)
            except Exception as e:
                logger.error(f"CATCHUP error streak_reminders: {e}")

    logger.info("CATCHUP: Startup tasks completed")


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
    role_combo = after.guild.get_role(ROLE_COMBO)
    if not role_verificado or not role_combo:
        return
    has_verificado = role_verificado in after.roles
    has_combo = role_combo in after.roles
    if has_verificado and not has_combo:
        await after.add_roles(role_combo)
    elif not has_verificado and has_combo:
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
            except (discord.Forbidden, discord.HTTPException):
                pass
    
    embed = discord.Embed(
        title="✅ Rol Miembro Asignado",
        description=f"Se asignó el rol **Miembro** a **{count}** miembros.",
        color=discord.Color.green(),
    )
    await msg.edit(embed=embed)


_daily_trivia_posted_date = None

@tasks.loop(minutes=1)
async def daily_trivia_task():
    if not await asyncio.to_thread(leader.is_leader):
        return
    now = datetime.now(TZ_SPAIN)
    # Ventana 10:00-10:30 con retry
    if now.hour != TRIVIA_HOUR or now.minute < TRIVIA_MINUTE or now.minute > 30:
        return

    global _daily_trivia_posted_date
    today = now.date()
    if _daily_trivia_posted_date == today:
        return

    # Verificar si ya existe en BD (catch-up o previo)
    daily = await asyncio.to_thread(db.get_daily_trivia)
    if daily:
        _daily_trivia_posted_date = today
        return

    try:
        guild = bot.guilds[0] if bot.guilds else None
        if not guild:
            return

        channel = guild.get_channel(TRIVIA_CHANNEL_ID)
        if not channel:
            return


        from pokeapi_trivia import generate_daily_trivia
        from trivia import DIFFICULTY_CONFIG, TriviaView

        difficulty = _random.choice(["easy", "medium", "hard"])
        
        used_questions = db.get_used_questions()
        logger.info(f"Used questions count: {len(used_questions)}")
        trivia = generate_daily_trivia(used_questions)
        if not trivia:
            logger.error("generate_daily_trivia returned None")
            return
        
        logger.info(f"Generated trivia: {trivia['question'][:50]}...")

        options = trivia["options"][:]
        _random.shuffle(options)

        correct = trivia["correct"]
        await asyncio.to_thread(db.save_trivia_question, trivia["question"], correct, options)
        await asyncio.to_thread(db.mark_question_used, trivia["question"])

        daily = await asyncio.to_thread(db.get_daily_trivia)
        if not daily:
            logger.error("get_daily_trivia returned None after save")
            return

        _daily_trivia_posted_date = today

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
        embed.set_footer(text="Usa los botones para responder. Disponible hasta mañana a las 10:00.")

        view = TriviaView(correct, daily["id"], options, difficulty)
        msg = await channel.send(embed=embed, view=view)
        view.message = msg
        _active_views.append(view)
        # Mantener solo las7 vistas más recientes (evita fuga de memoria)
        if len(_active_views) > 7:
            _active_views.pop(0)

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

            trivia_leaders = db.get_trivia_leaderboard(10, week_only=True)
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
        logger.exception(f"Error in daily_trivia_task: {e}")


@daily_trivia_task.before_loop
async def before_daily_trivia():
    await bot.wait_until_ready()


@tasks.loop(minutes=1)
async def streak_reminder_task():
    try:
        if not await asyncio.to_thread(leader.is_leader):
            return
        now = datetime.now(TZ_SPAIN)
        # Ventana 10:00-10:30 con retry
        if now.hour != TRIVIA_HOUR or now.minute < 0 or now.minute > 30:
            return
        
        # Evitar enviar recordatorios duplicados el mismo día
        today = datetime.now(TZ_SPAIN).date()
        if getattr(streak_reminder_task, "_last_reminded_date", None) == today:
            return
        
        users = await asyncio.to_thread(db.get_users_needing_reminder)
        for user_data in users:
            try:
                user = await bot.fetch_user(user_data["user_id"])
                if not user:
                    continue
                await asyncio.to_thread(db.mark_reminder_sent, user_data["user_id"])
                await user.send(
                    f"¡Hola {user_data['username']}! 🔥\n\n"
                    f"¡Tienes una racha de **{user_data['current_streak']} días** en peligro! "
                    f"Si no respondes la trivia de hoy, podrías perderla.\n\n"
                    f"¡Ve a <#{ALLOWED_CHANNEL_ID}> y responde la pregunta del día para mantener tu racha! 💪"
                )
            except Exception as e:
                logger.warning(f"Error sending reminder to {user_data.get('username')}: {e}")
        
        streak_reminder_task._last_reminded_date = datetime.now(TZ_SPAIN).date()
    except Exception as e:
        logger.exception("Error en streak_reminder_task: %s", e)


@streak_reminder_task.before_loop
async def before_streak_reminder():
    await bot.wait_until_ready()


@tasks.loop(hours=1)
async def reset_stale_streaks_task():
    if not await asyncio.to_thread(leader.is_leader):
        return
    try:
        await asyncio.to_thread(db.cleanup_old_used_questions)
    except Exception as e:
        logger.warning(f"Error cleaning up old questions: {e}")
    try:
        broken_users = await asyncio.to_thread(db.get_users_with_broken_streaks)
        guild = bot.guilds[0] if bot.guilds else None
        if not guild:
            return
        role = guild.get_role(STREAK_ROLE_ID)
        for user_data in broken_users:
            try:
                await asyncio.to_thread(db.mark_streak_broken_notified, user_data["user_id"])
                if role:
                    member = guild.get_member(user_data["user_id"])
                    if member and role in member.roles:
                        await member.remove_roles(role)
                user = await bot.fetch_user(user_data["user_id"])
                if user:
                    await user.send(
                        f"😢 ¡Hola {user_data['username']}!\n\n"
                        f"Tu racha de **{user_data['old_streak']} días** se ha roto. "
                        f"No respondiste la trivia en los últimos 2 días.\n\n"
                        f"¡No te preocupes! Empieza de nuevo hoy. Ve a <#{ALLOWED_CHANNEL_ID}> y escribe **!trivia** para recuperarla. 💪"
                    )
            except Exception as e:
                logger.warning(f"Error notifying broken streak for {user_data['username']}: {e}")
    except Exception as e:
        logger.exception("Error en reset_stale_streaks_task: %s", e)


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


# Watchdog: reinicia el bot si el loop se detiene inesperadamente
@tasks.loop(minutes=5)
async def watchdog_task():
    """Verifica que el bot siga conectado y los loops estén vivos."""
    if not bot.is_ready():
        logger.warning("Watchdog: bot no está ready, intentando reconectar...")
        return
    
    # Verificar loops críticos
    critical_tasks = [
        ("daily_trivia_task", daily_trivia_task),
        ("streak_reminder_task", streak_reminder_task),
        ("reset_stale_streaks_task", reset_stale_streaks_task),
        ("lease_renew_task", lease_renew_task),
    ]
    
    for name, task in critical_tasks:
        if not task.is_running():
            logger.error(f"Watchdog: {name} no está corriendo, reiniciando...")
            try:
                task.restart()
            except Exception as e:
                logger.exception(f"Watchdog: error reiniciando {name}: {e}")


@watchdog_task.before_loop
async def before_watchdog():
    await bot.wait_until_ready()
    # Dar tiempo a que todo arranque
    await asyncio.sleep(60)


# Renovación del lease de líder (failover PC <-> host gratuito)
@tasks.loop(seconds=leader.RENEW_INTERVAL_S)
async def lease_renew_task():
    status = await asyncio.to_thread(leader.renew_lease)
    if status is False:
        # Otra instancia tomó el control: desconectar para no duplicar
        logger.error("Lease de líder perdido (%s); desconectando", leader.INSTANCE_ID)
        await bot.close()
        return
    if await asyncio.to_thread(leader.should_yield):
        # La PC principal (prioridad mayor) está en espera: ceder el mando
        logger.info(
            "Cediendo el liderazgo a instancia prioritaria (%s)", leader.INSTANCE_ID
        )
        await asyncio.to_thread(leader.release_lease)
        await bot.close()
        return
    # visible en log cada 5 min para poder verificar la salud del lease
    lease_renew_task._n_renew = getattr(lease_renew_task, "_n_renew", 0) + 1
    if lease_renew_task._n_renew % 10 == 0:
        logger.info(
            "Lease renovado OK (%s), %d renovaciones",
            leader.INSTANCE_ID,
            lease_renew_task._n_renew,
        )


@lease_renew_task.before_loop
async def before_lease_renew():
    await bot.wait_until_ready()


async def setup_hook():
    if os.getenv("ENABLE_WEB_SERVER", "") == "1" and "web_started" not in globals():
        from web_server import start_web_server
        await start_web_server()
        globals()["web_started"] = True
        print("[OK] Web server initialized")

    # Cargar cogs solo una vez (setup_hook se llama en cada login/reconexión)
    for ext in ("trivia", "reto", "verify"):
        if ext not in bot.extensions:
            await bot.load_extension(ext)

    # Sincronizar slash commands
    try:
        synced = await bot.tree.sync()
        print(f"[OK] {len(synced)} slash commands sincronizados")
    except Exception as e:
        print(f"[WARN] Error sincronizando slash commands: {e}")

    # Aplicar check de canal a todos los slash commands (solo una vez)
    if not getattr(bot, "_slash_checks_applied", False):
        for cmd in bot.tree.walk_commands():
            if isinstance(cmd, app_commands.Command):
                cmd.add_check(slash_check_channel)
        bot._slash_checks_applied = True

    # Iniciar watchdog
    if not watchdog_task.is_running():
        watchdog_task.start()

    # Renovar lease de líder
    if not lease_renew_task.is_running():
        lease_renew_task.start()

bot.setup_hook = setup_hook


async def _run_with_lease():
    """Solo conecta a Discord la instancia con lease de líder vigente."""
    while True:
        acquired = await asyncio.to_thread(leader.acquire_lease)
        if not acquired:
            # Anunciar que estamos en espera: un líder suplente nos cederá el mando
            await asyncio.to_thread(leader.announce_standby)
            logger.info(
                "Otra instancia es líder; reintentando en %ss (%s)",
                leader.WAIT_INTERVAL_S,
                leader.INSTANCE_ID,
            )
            await asyncio.sleep(leader.WAIT_INTERVAL_S)
            continue

        await asyncio.to_thread(leader.clear_standby)
        logger.info("Conectando como líder (%s)", leader.INSTANCE_ID)
        try:
            await bot.start(DISCORD_TOKEN)
        finally:
            # Liberar el lease al apagarse (si nadie más lo tomó ya)
            await asyncio.to_thread(leader.release_lease)
        # Salida (caída o cierre): esperar y volver a intentar ser líder
        await asyncio.sleep(leader.WAIT_INTERVAL_S)


if __name__ == "__main__":
    asyncio.run(_run_with_lease())
