import discord
from discord.ext import commands
from discord import ui
import requests
import re
from config import (
    TWITCH_CLIENT_ID,
    TWITCH_CLIENT_SECRET,
    TWITCH_BROADCASTER_ID,
    YOUTUBE_API_KEY,
    YOUTUBE_CHANNEL_ID,
    MIEMBRO_ROLE_ID,
)

_twitch_token = None


def _get_twitch_token():
    global _twitch_token
    if _twitch_token:
        return _twitch_token
    resp = requests.post(
        "https://id.twitch.tv/oauth2/token",
        params={
            "client_id": TWITCH_CLIENT_ID,
            "client_secret": TWITCH_CLIENT_SECRET,
            "grant_type": "client_credentials",
        },
    )
    if resp.status_code == 200:
        _twitch_token = resp.json()["access_token"]
        return _twitch_token
    return None


def check_twitch_follow(username: str) -> bool:
    token = _get_twitch_token()
    if not token:
        return False

    headers = {"Client-ID": TWITCH_CLIENT_ID, "Authorization": f"Bearer {token}"}

    resp = requests.get(
        "https://api.twitch.tv/helix/users",
        headers=headers,
        params={"login": username},
    )
    if resp.status_code != 200:
        return False

    users = resp.json().get("data", [])
    if not users:
        return False

    user_id = users[0]["id"]

    resp = requests.get(
        "https://api.twitch.tv/helix/channels/followers",
        headers=headers,
        params={"broadcaster_id": TWITCH_BROADCASTER_ID, "user_id": user_id},
    )
    if resp.status_code != 200:
        return False

    data = resp.json().get("data", [])
    return len(data) > 0


def check_youtube_subscription(channel_url: str) -> bool:
    if not YOUTUBE_API_KEY:
        return False

    channel_id = None
    if "youtube.com/channel/" in channel_url:
        match = re.search(r"youtube\.com/channel/([a-zA-Z0-9_-]+)", channel_url)
        if match:
            channel_id = match.group(1)
    elif "youtube.com/@" in channel_url:
        handle = re.search(r"youtube\.com/@([a-zA-Z0-9_.-]+)", channel_url)
        if handle:
            resp = requests.get(
                "https://www.googleapis.com/youtube/v3/channels",
                params={
                    "key": YOUTUBE_API_KEY,
                    "forHandle": handle.group(1),
                    "part": "id",
                },
            )
            if resp.status_code == 200:
                items = resp.json().get("items", [])
                if items:
                    channel_id = items[0]["id"]

    if not channel_id:
        return False

    resp = requests.get(
        "https://www.googleapis.com/youtube/v3/subscriptions",
        params={
            "key": YOUTUBE_API_KEY,
            "part": "snippet",
            "channelId": channel_id,
            "forChannelId": YOUTUBE_CHANNEL_ID,
            "maxResults": 1,
        },
    )
    if resp.status_code != 200:
        return False

    items = resp.json().get("items", [])
    return len(items) > 0


class VerifyTwitchModal(ui.Modal, title="Verificar con Twitch"):
    username = ui.TextInput(
        label="Tu usuario de Twitch",
        placeholder="Ej: pokejgameryt",
        required=True,
        max_length=25,
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        follows = check_twitch_follow(self.username.value.lower())

        if follows:
            role = interaction.guild.get_role(MIEMBRO_ROLE_ID)
            if role:
                await interaction.user.add_roles(role)
            await interaction.followup.send(
                embed=discord.Embed(
                    title="✅ Verificado con Twitch",
                    description=f"¡Gracias por seguirme en Twitch, **{self.username.value}**!\n\nYa tienes el rol **Miembro**.",
                    color=discord.Color.green(),
                ),
                ephemeral=True,
            )
        else:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="❌ No se encontró seguimiento",
                    description=f"**{self.username.value}** no parece seguir el canal.\n\nAsegúrate de estar siguiendo: **https://twitch.tv/pokejgameryt**",
                    color=discord.Color.red(),
                ),
                ephemeral=True,
            )


class VerifyYouTubeModal(ui.Modal, title="Verificar con YouTube"):
    channel_url = ui.TextInput(
        label="URL de tu canal de YouTube",
        placeholder="Ej: https://youtube.com/@pokejgameryt",
        required=True,
        max_length=200,
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        subscribed = check_youtube_subscription(self.channel_url.value)

        if subscribed:
            role = interaction.guild.get_role(MIEMBRO_ROLE_ID)
            if role:
                await interaction.user.add_roles(role)
            await interaction.followup.send(
                embed=discord.Embed(
                    title="✅ Verificado con YouTube",
                    description="¡Gracias por suscribirte!\n\nYa tienes el rol **Miembro**.",
                    color=discord.Color.green(),
                ),
                ephemeral=True,
            )
        else:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="❌ No se encontró suscripción",
                    description="No se pudo verificar tu suscripción.\n\nAsegúrate de:\n1. Estar suscrito a **https://youtube.com/@pokejgameryt**\n2. Que tu suscripción sea **pública**",
                    color=discord.Color.red(),
                ),
                ephemeral=True,
            )


class VerifyView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(
        label="Twitch",
        style=discord.ButtonStyle.Purple,
        emoji="🟣",
        custom_id="verify_twitch",
    )
    async def twitch_button(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(VerifyTwitchModal())

    @ui.button(
        label="YouTube",
        style=discord.ButtonStyle.Red,
        emoji="🔴",
        custom_id="verify_youtube",
    )
    async def youtube_button(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(VerifyYouTubeModal())


class Verify(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="enviar-verificacion")
    @commands.has_permissions(administrator=True)
    async def send_verification(self, ctx: commands.Context):
        embed = discord.Embed(
            title="🔒 Verificación Requerida",
            description=(
                "Para acceder al servidor, debes seguirme en **Twitch** o **YouTube**.\n\n"
                "**¿Cómo funciona?**\n"
                "1. Haz clic en el botón de tu plataforma\n"
                "2. Introduce tu usuario o URL de canal\n"
                "3. ¡Listo! Se te asignará el rol **Miembro**\n\n"
                "⚠️ Asegúrate de que tu suscripción/seguimiento sea **público**."
            ),
            color=discord.Color.blue(),
        )
        embed.set_footer(text="Pulsa un botón para verificar")
        await ctx.send(embed=embed, view=VerifyView())

    @commands.command(name="verificar-twitch")
    async def verify_twitch_cmd(self, ctx: commands.Context, username: str = None):
        if not username:
            await ctx.send("Uso: `!verificar-twitch <usuario>`")
            return

        follows = check_twitch_follow(username.lower())
        if follows:
            role = ctx.guild.get_role(MIEMBRO_ROLE_ID)
            if role:
                await ctx.author.add_roles(role)
            await ctx.send(f"✅ **{username}** sigue el canal. ¡Rol asignado!")
        else:
            await ctx.send(f"❌ **{username}** no sigue el canal.")

    @commands.command(name="verificar-youtube")
    async def verify_youtube_cmd(self, ctx: commands.Context, url: str = None):
        if not url:
            await ctx.send("Uso: `!verificar-youtube <url>`")
            return

        subscribed = check_youtube_subscription(url)
        if subscribed:
            role = ctx.guild.get_role(MIEMBRO_ROLE_ID)
            if role:
                await ctx.author.add_roles(role)
            await ctx.send("✅ ¡Suscripción verificada! Rol asignado.")
        else:
            await ctx.send("❌ No se pudo verificar la suscripción.")


async def setup(bot: commands.Bot):
    await bot.add_cog(Verify(bot))
    bot.add_view(VerifyView())
