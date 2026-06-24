import discord
from discord.ext import commands, tasks
from discord import ui
import requests
import re
import time
from config import (
    TWITCH_CLIENT_ID,
    TWITCH_CLIENT_SECRET,
    TWITCH_BROADCASTER_ID,
    YOUTUBE_API_KEY,
    YOUTUBE_CHANNEL_ID,
    MIEMBRO_ROLE_ID,
)
import database as db

_twitch_token = None
_twitch_token_time = 0


def _get_twitch_token():
    global _twitch_token, _twitch_token_time
    if _twitch_token and time.time() - _twitch_token_time < 3600:
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
        _twitch_token_time = time.time()
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
    return len(resp.json().get("data", [])) > 0


def get_twitch_followers() -> set:
    token = _get_twitch_token()
    if not token:
        return set()
    headers = {"Client-ID": TWITCH_CLIENT_ID, "Authorization": f"Bearer {token}"}
    cursor = ""
    followers = set()
    for _ in range(10):
        params = {"broadcaster_id": TWITCH_BROADCASTER_ID, "first": 100}
        if cursor:
            params["after"] = cursor
        resp = requests.get(
            "https://api.twitch.tv/helix/channels/followers",
            headers=headers,
            params=params,
        )
        if resp.status_code != 200:
            break
        data = resp.json()
        for f in data.get("data", []):
            followers.add(f["user_id"])
        cursor = data.get("pagination", {}).get("cursor", "")
        if not cursor:
            break
    return followers


def get_twitch_user_id(username: str) -> str:
    token = _get_twitch_token()
    if not token:
        return None
    headers = {"Client-ID": TWITCH_CLIENT_ID, "Authorization": f"Bearer {token}"}
    resp = requests.get(
        "https://api.twitch.tv/helix/users",
        headers=headers,
        params={"login": username},
    )
    if resp.status_code == 200:
        users = resp.json().get("data", [])
        if users:
            return users[0]["id"]
    return None


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
                params={"key": YOUTUBE_API_KEY, "forHandle": handle.group(1), "part": "id"},
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
    return len(resp.json().get("items", [])) > 0


def get_youtube_subscribers() -> set:
    if not YOUTUBE_API_KEY:
        return set()
    subscribers = set()
    page_token = ""
    for _ in range(50):
        params = {
            "key": YOUTUBE_API_KEY,
            "part": "snippet",
            "channelId": YOUTUBE_CHANNEL_ID,
            "maxResults": 50,
        }
        if page_token:
            params["pageToken"] = page_token
        resp = requests.get(
            "https://www.googleapis.com/youtube/v3/subscriptions",
            params=params,
        )
        if resp.status_code != 200:
            break
        data = resp.json()
        for item in data.get("items", []):
            subscribers.add(item["snippet"]["resourceId"]["channelId"])
        page_token = data.get("nextPageToken", "")
        if not page_token:
            break
    return subscribers


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
            db.create_user(interaction.user.id, interaction.user.display_name)
            db.set_verified(interaction.user.id, True, "twitch", self.username.value.lower())
            role = interaction.guild.get_role(MIEMBRO_ROLE_ID)
            if role:
                await interaction.user.add_roles(role)
            await interaction.followup.send(
                embed=discord.Embed(
                    title="✅ Verificado con Twitch",
                    description=f"¡Gracias por seguirme, **{self.username.value}**!\n\nYa tienes el rol **Miembro**.",
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
            db.create_user(interaction.user.id, interaction.user.display_name)
            db.set_verified(interaction.user.id, True, "youtube", self.channel_url.value)
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
                    description="Asegúrate de estar suscrito a **https://youtube.com/@pokejgameryt** con suscripción **pública**.",
                    color=discord.Color.red(),
                ),
                ephemeral=True,
            )


class VerifyView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="Twitch", style=discord.ButtonStyle.Purple, emoji="🟣", custom_id="verify_twitch")
    async def twitch_button(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(VerifyTwitchModal())

    @ui.button(label="YouTube", style=discord.ButtonStyle.Red, emoji="🔴", custom_id="verify_youtube")
    async def youtube_button(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(VerifyYouTubeModal())


class Verify(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.check_followers.start()

    def cog_unload(self):
        self.check_followers.cancel()

    @tasks.loop(minutes=10)
    async def check_followers(self):
        guild = self.bot.guilds[0] if self.bot.guilds else None
        if not guild:
            return
        role = guild.get_role(MIEMBRO_ROLE_ID)
        if not role:
            return

        twitch_followers = get_twitch_followers()
        verified_users = db.get_all_verified_users()

        for member in guild.members:
            if member.bot:
                continue
            user_data = db.get_user(member.id)
            verified = user_data.get("verified", False) if user_data else False

            if verified:
                if member.id not in twitch_followers and member.id not in [v["user_id"] for v in verified_users if v.get("platform") == "youtube"]:
                    if role in member.roles:
                        await member.remove_roles(role)
                        db.set_verified(member.id, False, None, None)
            else:
                if member.id in twitch_followers:
                    db.set_verified(member.id, True, "twitch", "auto-detected")
                    if role not in member.roles:
                        await member.add_roles(role)

    @check_followers.before_loop
    async def before_check_followers(self):
        await self.bot.wait_until_ready()

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
            db.create_user(ctx.author.id, ctx.author.display_name)
            db.set_verified(ctx.author.id, True, "twitch", username.lower())
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
            db.create_user(ctx.author.id, ctx.author.display_name)
            db.set_verified(ctx.author.id, True, "youtube", url)
            role = ctx.guild.get_role(MIEMBRO_ROLE_ID)
            if role:
                await ctx.author.add_roles(role)
            await ctx.send("✅ ¡Suscripción verificada! Rol asignado.")
        else:
            await ctx.send("❌ No se pudo verificar la suscripción.")

    @commands.command(name="verificar-todos")
    @commands.has_permissions(administrator=True)
    async def verify_all_members(self, ctx: commands.Context):
        await ctx.send("⏳ Verificando miembros existentes...")
        role = ctx.guild.get_role(MIEMBRO_ROLE_ID)
        if not role:
            await ctx.send("❌ No se encontró el rol.")
            return

        twitch_followers = get_twitch_followers()
        assigned = 0
        for member in ctx.guild.members:
            if member.bot:
                continue
            if member.id in twitch_followers:
                db.create_user(member.id, member.display_name)
                db.set_verified(member.id, True, "twitch", "auto-detected")
                if role not in member.roles:
                    await member.add_roles(role)
                    assigned += 1

        await ctx.send(f"✅ Verificación completada. Se asignó el rol a **{assigned}** miembros.")


async def setup(bot: commands.Bot):
    await bot.add_cog(Verify(bot))
    bot.add_view(VerifyView())
