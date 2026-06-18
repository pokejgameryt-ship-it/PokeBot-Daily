import discord
from discord.ext import commands
from discord import app_commands
import database as db
from config import RETO_POINTS, REWARD_ROLES
from datetime import datetime


class Reto(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="reto")
    async def reto_command(self, ctx: commands.Context):
        reto = db.get_active_reto()
        if not reto:
            embed = discord.Embed(
                title="🎯 Sin reto activo",
                description="No hay reto semanal activo. Espera al próximo.",
                color=discord.Color.grey(),
            )
            await ctx.send(embed=embed)
            return

        embed = discord.Embed(
            title="🎯 Reto de la Semana",
            description=reto["description"],
            color=discord.Color.purple(),
        )
        embed.add_field(name="Recompensa", value=f"{reto['reward_points']} puntos")
        embed.add_field(
            name="Fecha límite",
            value=reto["end_date"],
            inline=False,
        )

        completions = []
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT u.username FROM reto_completions rc 
               JOIN users u ON rc.user_id = u.user_id 
               WHERE rc.reto_id = ?""",
            (reto["id"],),
        )
        completions = [row["username"] for row in cursor.fetchall()]
        conn.close()

        if completions:
            embed.add_field(
                name="Completado por",
                value=", ".join(completions),
                inline=False,
            )
        else:
            embed.add_field(
                name="Completado por", value="Nadie aún", inline=False
            )

        await ctx.send(embed=embed)

    @commands.command(name="completar-reto")
    async def completar_reto_command(self, ctx: commands.Context):
        reto = db.get_active_reto()
        if not reto:
            await ctx.send("No hay reto activo.")
            return

        db.create_user(ctx.author.id, ctx.author.display_name)

        success = db.complete_reto(ctx.author.id, reto["id"])
        if not success:
            await ctx.send("Ya completaste este reto.")
            return

        db.update_score(ctx.author.id, RETO_POINTS["completed"], ctx.author.display_name)

        embed = discord.Embed(
            title="🎉 ¡Reto Completado!",
            description=f"**{ctx.author.display_name}** completó el reto: {reto['title']}",
            color=discord.Color.green(),
        )
        embed.add_field(
            name="Puntos ganados",
            value=f"+{RETO_POINTS['completed']}",
        )
        embed.set_footer(text="Tu logro ha sido registrado en el Hall of Fame.")

        channel = discord.utils.get(
            ctx.guild.text_channels, name="retos-semanales"
        )
        if channel:
            await channel.send(embed=embed)

        await ctx.send(
            f"¡Felicidades {ctx.author.display_name}! Completaste el reto y ganaste {RETO_POINTS['completed']} puntos."
        )

    @app_commands.command(
        name="reto", description="Muestra el reto semanal activo"
    )
    async def reto_slash(self, interaction: discord.Interaction):
        reto = db.get_active_reto()
        if not reto:
            embed = discord.Embed(
                title="🎯 Sin reto activo",
                description="No hay reto semanal activo. Espera al próximo.",
                color=discord.Color.grey(),
            )
            await interaction.response.send_message(embed=embed)
            return

        embed = discord.Embed(
            title="🎯 Reto de la Semana",
            description=reto["description"],
            color=discord.Color.purple(),
        )
        embed.add_field(name="Recompensa", value=f"{reto['reward_points']} puntos")
        embed.add_field(name="Fecha límite", value=reto["end_date"])

        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="completar-reto",
        description="Marca el reto semanal como completado",
    )
    async def completar_reto_slash(self, interaction: discord.Interaction):
        reto = db.get_active_reto()
        if not reto:
            await interaction.response.send_message("No hay reto activo.")
            return

        db.create_user(interaction.user.id, interaction.user.display_name)

        success = db.complete_reto(interaction.user.id, reto["id"])
        if not success:
            await interaction.response.send_message(
                "Ya completaste este reto.", ephemeral=True
            )
            return

        db.update_score(interaction.user.id, RETO_POINTS["completed"], interaction.user.display_name)

        embed = discord.Embed(
            title="🎉 ¡Reto Completado!",
            description=f"**{interaction.user.display_name}** completó el reto: {reto['title']}",
            color=discord.Color.green(),
        )
        embed.add_field(
            name="Puntos ganados",
            value=f"+{RETO_POINTS['completed']}",
        )

        await interaction.response.send_message(embed=embed)

        channel = discord.utils.get(
            interaction.guild.text_channels, name="retos-semanales"
        )
        if channel:
            await channel.send(embed=embed)

    @commands.command(name="crear-reto")
    @commands.has_permissions(administrator=True)
    async def crear_reto_command(
        self,
        ctx: commands.Context,
        titulo: str,
        descripcion: str,
        puntos: int = 50,
        dias: int = 7,
    ):
        reto_id = db.create_reto(titulo, descripcion, puntos, dias)

        embed = discord.Embed(
            title="🎯 ¡Nuevo Reto Creado!",
            description=descripcion,
            color=discord.Color.green(),
        )
        embed.add_field(name="Título", value=titulo)
        embed.add_field(name="Recompensa", value=f"{puntos} puntos")
        embed.add_field(name="Duración", value=f"{dias} días")

        channel = discord.utils.get(
            ctx.guild.text_channels, name="retos-semanales"
        )
        if channel:
            await channel.send(embed=embed)

        await ctx.send(f"Reto #{reto_id} creado exitosamente.")

    @commands.command(name="profile")
    async def profile_command(self, ctx: commands.Context, member: discord.Member = None):
        member = member or ctx.author
        user = db.get_user(member.id)

        if not user:
            db.create_user(member.id, member.display_name)
            user = db.get_user(member.id)

        embed = discord.Embed(
            title=f"📊 Perfil de {member.display_name}",
            color=discord.Color.blue(),
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Puntos totales", value=str(user["total_score"]))
        embed.add_field(
            name="Trivia",
            value=f"{user['trivia_correct']}/{user['trivia_total']}",
        )
        embed.add_field(name="Racha actual", value=f"{user['current_streak']} 🔥")
        embed.add_field(name="Mejor racha", value=f"{user['best_streak']} ⭐")
        embed.add_field(
            name="Retos completados", value=str(user["retos_completed"])
        )

        rank_roles = []
        for days, role_name in sorted(REWARD_ROLES.items(), reverse=True):
            if user["current_streak"] >= days:
                rank_roles.append(role_name)
                break

        if rank_roles:
            embed.add_field(name="Rango", value=rank_roles[0])

        await ctx.send(embed=embed)

    @app_commands.command(
        name="profile", description="Muestra tu perfil de PokéBot Daily"
    )
    async def profile_slash(
        self, interaction: discord.Interaction, member: discord.Member = None
    ):
        member = member or interaction.user
        user = db.get_user(member.id)

        if not user:
            db.create_user(member.id, member.display_name)
            user = db.get_user(member.id)

        embed = discord.Embed(
            title=f"📊 Perfil de {member.display_name}",
            color=discord.Color.blue(),
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Puntos totales", value=str(user["total_score"]))
        embed.add_field(
            name="Trivia",
            value=f"{user['trivia_correct']}/{user['trivia_total']}",
        )
        embed.add_field(name="Racha actual", value=f"{user['current_streak']} 🔥")
        embed.add_field(name="Mejor racha", value=f"{user['best_streak']} ⭐")
        embed.add_field(
            name="Retos completados", value=str(user["retos_completed"])
        )

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Reto(bot))
