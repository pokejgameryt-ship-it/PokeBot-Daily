import discord
from discord.ext import commands, tasks
from discord import ui
import requests
import re
import time
import asyncio
import os
from urllib.parse import urlencode
from config import (
    TWITCH_CLIENT_ID,
    TWITCH_CLIENT_SECRET,
    TWITCH_BROADCASTER_ID,
    YOUTUBE_API_KEY,
    YOUTUBE_CHANNEL_ID,
    MIEMBRO_ROLE_ID,
    TWITCH_VIP_ROLE_ID,
    DISCORD_CLIENT_ID,
    DISCORD_REDIRECT_URI,
)
import database as db
from web_server import get_code, start_web_server

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


def get_twitch_vips() -> set:
    token = _get_twitch_token()
    if not token:
        return set()
    headers = {"Client-ID": TWITCH_CLIENT_ID, "Authorization": f"Bearer {token}"}
    cursor = ""
    vips = set()
    for _ in range(10):
        params = {"broadcaster_id": TWITCH_BROADCASTER_ID, "first": 100}
        if cursor:
            params["after"] = cursor
        resp = requests.get(
            "https://api.twitch.tv/helix/channels/vips",
            headers=headers,
            params=params,
        )
        if resp.status_code != 200:
            break
        data = resp.json()
        for v in data.get("data", []):
            vips.add(v["user_id"])
        cursor = data.get("pagination", {}).get("cursor", "")
        if not cursor:
            break
    return vips


class CodeModal(ui.Modal, title="Pega el código de autorización"):
    code = ui.TextInput(
        label="Código de Discord",
        placeholder="Pega aquí el código de la URL después de autorizar",
        required=True,
        max_length=200,
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        import aiohttp as _aiohttp
        async with _aiohttp.ClientSession() as session:
            data = {
                "client_id": DISCORD_CLIENT_ID,
                "client_secret": os.getenv("DISCORD_CLIENT_SECRET", ""),
                "grant_type": "authorization_code",
                "code": self.code.value.strip(),
                "redirect_uri": DISCORD_REDIRECT_URI,
            }
            async with session.post("https://discord.com/api/oauth2/token", data=data) as resp:
                if resp.status != 200:
                    await interaction.followup.send(
                        embed=discord.Embed(
                            title="❌ Código inválido",
                            description="El código no es válido. Intenta de nuevo.",
                            color=discord.Color.red(),
                        ),
                        ephemeral=True,
                    )
                    return
                token_data = await resp.json()
                access_token = token_data["access_token"]

            headers = {"Authorization": f"Bearer {access_token}"}
            async with session.get("https://discord.com/api/users/@me/connections", headers=headers) as resp:
                if resp.status != 200:
                    await interaction.followup.send(
                        embed=discord.Embed(
                            title="❌ Error al leer conexiones",
                            description="No se pudieron leer tus conexiones.",
                            color=discord.Color.red(),
                        ),
                        ephemeral=True,
                    )
                    return
                connections = await resp.json()

        twitch_name = None
        youtube_name = None
        for conn in connections:
            if conn["type"] == "twitch":
                twitch_name = conn["name"]
            elif conn["type"] == "youtube":
                youtube_name = conn["name"]

        if twitch_name:
            if check_twitch_follow(twitch_name.lower()):
                db.create_user(interaction.user.id, interaction.user.display_name)
                db.set_verified(interaction.user.id, True, "twitch", twitch_name.lower())
                role = interaction.guild.get_role(MIEMBRO_ROLE_ID)
                if role:
                    await interaction.user.add_roles(role)
                await interaction.followup.send(
                    embed=discord.Embed(
                        title="✅ Verificado",
                        description=f"Tu Twitch **{twitch_name}** sigue el canal.\n\nYa tienes el rol **Miembro**.",
                        color=discord.Color.green(),
                    ),
                    ephemeral=True,
                )
            else:
                await interaction.followup.send(
                    embed=discord.Embed(
                        title="❌ Twitch no sigue el canal",
                        description=f"Tu Twitch **{twitch_name}** no sigue el canal.\n\nSigue: **https://twitch.tv/pokejgamer**",
                        color=discord.Color.red(),
                    ),
                    ephemeral=True,
                )
        elif youtube_name:
            db.create_user(interaction.user.id, interaction.user.display_name)
            db.set_verified(interaction.user.id, True, "youtube", youtube_name)
            role = interaction.guild.get_role(MIEMBRO_ROLE_ID)
            if role:
                await interaction.user.add_roles(role)
            await interaction.followup.send(
                embed=discord.Embed(
                    title="✅ Verificado",
                    description=f"Tu YouTube **{youtube_name}** está vinculado.\n\nYa tienes el rol **Miembro**.",
                    color=discord.Color.green(),
                ),
                ephemeral=True,
            )
        else:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="❌ No se encontró Twitch o YouTube",
                    description="No tienes Twitch o YouTube vinculado en Discord.\n\nVe a **Configuración de Discord → Conexiones** para vincularlos.",
                    color=discord.Color.red(),
                ),
                ephemeral=True,
            )


class VerifyView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="Verificar con Discord", style=discord.ButtonStyle.primary, emoji="🔵", custom_id="verify_discord_v2")
    async def discord_button(self, interaction: discord.Interaction, button: ui.Button):
        redirect = DISCORD_REDIRECT_URI
        params = {
            "client_id": DISCORD_CLIENT_ID,
            "redirect_uri": redirect,
            "response_type": "code",
            "scope": "identify connections",
        }
        url = f"https://discord.com/api/oauth2/authorize?{urlencode(params)}"
        embed = discord.Embed(
            title="🔗 Paso 1: Autoriza la app",
            description=(
                f"1. Haz clic en el enlace de abajo\n"
                f"2. Copia el **código** de la URL (después de `?code=`)\n"
                f"3. Vuelve aquí y pega el código en el botón de abajo\n\n"
                f"**[Clic aquí para autorizar]({url})**"
            ),
            color=discord.Color.blurple(),
        )
        await interaction.response.send_message(embed=embed, view=CodeView(), ephemeral=True)


class CodeView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="Pegar código", style=discord.ButtonStyle.green, emoji="📋", custom_id="paste_code_btn")
    async def paste_code(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(CodeModal())


class Verify(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.check_followers.start()
        self.check_vips.start()
        self.bot.loop.create_task(self.initial_verify())

    def cog_unload(self):
        self.check_followers.cancel()
        self.check_vips.cancel()

    async def initial_verify(self):
        await self.bot.wait_until_ready()
        await asyncio.sleep(5)
        guild = self.bot.guilds[0] if self.bot.guilds else None
        if not guild:
            return
        role = guild.get_role(MIEMBRO_ROLE_ID)
        if not role:
            return
        verified_users = db.get_all_verified_users()
        assigned = 0
        for user_data in verified_users:
            if user_data.get("platform") != "twitch":
                continue
            username = user_data.get("username")
            if not username or username == "auto-detected":
                continue
            member = guild.get_member(user_data["user_id"])
            if not member:
                continue
            if check_twitch_follow(username):
                if role not in member.roles:
                    await member.add_roles(role)
                    assigned += 1
            else:
                if role in member.roles:
                    await member.remove_roles(role)
                    db.set_verified(member.id, False, None, None)
        if assigned > 0:
            print(f"[OK] Verificados {assigned} miembros existentes")

    @tasks.loop(minutes=10)
    async def check_followers(self):
        guild = self.bot.guilds[0] if self.bot.guilds else None
        if not guild:
            return
        role = guild.get_role(MIEMBRO_ROLE_ID)
        if not role:
            return
        verified_users = db.get_all_verified_users()
        for user_data in verified_users:
            if user_data.get("platform") != "twitch":
                continue
            username = user_data.get("username")
            if not username or username == "auto-detected":
                continue
            member = guild.get_member(user_data["user_id"])
            if not member:
                continue
            follows = check_twitch_follow(username)
            if follows:
                if role not in member.roles:
                    await member.add_roles(role)
            else:
                if role in member.roles:
                    await member.remove_roles(role)
                    db.set_verified(member.id, False, None, None)

    @check_followers.before_loop
    async def before_check_followers(self):
        await self.bot.wait_until_ready()

    @tasks.loop(minutes=5)
    async def check_vips(self):
        guild = self.bot.guilds[0] if self.bot.guilds else None
        if not guild:
            return
        role = guild.get_role(TWITCH_VIP_ROLE_ID)
        if not role:
            return
        twitch_vips = get_twitch_vips()
        verified_users = db.get_all_verified_users()
        for user_data in verified_users:
            if user_data.get("platform") != "twitch":
                continue
            username = user_data.get("username")
            if not username or username == "auto-detected":
                continue
            member = guild.get_member(user_data["user_id"])
            if not member:
                continue
            twitch_id = get_twitch_user_id(username)
            if twitch_id and twitch_id in twitch_vips:
                if role not in member.roles:
                    await member.add_roles(role)
            else:
                if role in member.roles:
                    await member.remove_roles(role)

    @check_vips.before_loop
    async def before_check_vips(self):
        await self.bot.wait_until_ready()

    @commands.command(name="enviar-verificacion")
    @commands.has_permissions(administrator=True)
    async def send_verification(self, ctx: commands.Context):
        embed = discord.Embed(
            title="🔒 Verificación Requerida",
            description=(
                "Para acceder al servidor, debes seguirme en **Twitch** o **YouTube**.\n\n"
                "**¿Cómo verificar?**\n"
                "1. Haz clic en el botón de abajo\n"
                "2. Autoriza la app de Discord\n"
                "3. Copia el código de la URL\n"
                "4. Pega el código aquí\n\n"
                "**Requisitos:**\n"
                "• Debes tener **Twitch** o **YouTube** vinculado en Discord\n"
                "• Tu suscripción/seguimiento debe ser **pública**"
            ),
            color=discord.Color.blue(),
        )
        embed.set_footer(text="Pulsa el botón para verificar")
        await ctx.send(embed=embed, view=VerifyView())

    @commands.command(name="verificar-todos")
    @commands.has_permissions(administrator=True)
    async def verify_all_members(self, ctx: commands.Context):
        await ctx.send("⏳ Verificando miembros del servidor...")
        role = ctx.guild.get_role(MIEMBRO_ROLE_ID)
        if not role:
            await ctx.send("❌ No se encontró el rol.")
            return
        verified_users = db.get_all_verified_users()
        assigned = 0
        removed = 0
        checked = 0
        for user_data in verified_users:
            platform = user_data.get("platform")
            username = user_data.get("username")
            if not username or username == "auto-detected":
                continue
            member = ctx.guild.get_member(user_data["user_id"])
            if not member:
                continue
            checked += 1
            follows = False
            if platform == "twitch":
                follows = check_twitch_follow(username)
            elif platform == "youtube":
                follows = check_youtube_subscription(username)
            if follows:
                if role not in member.roles:
                    await member.add_roles(role)
                    assigned += 1
            else:
                if role in member.roles:
                    await member.remove_roles(role)
                    db.set_verified(member.id, False, None, None)
                    removed += 1
        await ctx.send(
            f"✅ Verificación completada.\n"
            f"📊 Revisados: **{checked}**\n"
            f"🟢 Asignado: **{assigned}**\n"
            f"🔴 Quitado: **{removed}**"
        )


def check_youtube_subscription(channel_url: str) -> bool:
    if not YOUTUBE_API_KEY:
        return False
    channel_id = None
    if "youtube.com/@" in channel_url:
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


async def setup(bot: commands.Bot):
    asyncio.create_task(start_web_server())
    await bot.add_cog(Verify(bot))
    bot.add_view(VerifyView())
    bot.add_view(CodeView())
