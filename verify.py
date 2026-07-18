import discord
from discord.ext import commands, tasks
from discord import ui
import requests
import re
import time
import asyncio
import os
import logging
import io
from urllib.parse import urlencode

log = logging.getLogger("verify")
from config import (
    TWITCH_CLIENT_ID,
    TWITCH_CLIENT_SECRET,
    TWITCH_BROADCASTER_ID,
    TWITCH_BROADCASTER_LOGIN,
    TWITCH_REDIRECT_URI,
    YOUTUBE_API_KEY,
    YOUTUBE_CHANNEL_ID,
    MIEMBRO_ROLE_ID,
    TWITCH_VIP_ROLE_ID,
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_REDIRECT_URI,
)
import database as db

try:
    import pytesseract
    from PIL import Image
    HAS_OCR = True
except ImportError:
    HAS_OCR = False
    log.warning("pytesseract no instalado - verificación por screenshot deshabilitada")

YOUTUBE_CHANNEL_NAMES = [
    "pokejgamer",
    "poke jgamer",
    "pokej gameryt",
    "pokejgamer yt",
]

SUBSCRIBED_KEYWORDS = [
    "suscrito",
    "subscribed",
    "suscrib",
    "subscrib",
]

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
        log.error("No se pudo obtener token de Twitch")
        return False
    headers = {"Client-ID": TWITCH_CLIENT_ID, "Authorization": f"Bearer {token}"}
    resp = requests.get(
        "https://api.twitch.tv/helix/users",
        headers=headers,
        params={"login": username.lower()},
    )
    log.info(f"Twitch users API: status={resp.status_code}, response={resp.text[:300]}")
    if resp.status_code != 200:
        log.error(f"Twitch users API falló ({resp.status_code}): {resp.text}")
        return False
    users = resp.json().get("data", [])
    if not users:
        log.error(f"No se encontró el usuario de Twitch: {username}")
        return False
    user_id = users[0]["id"]
    log.info(f"Twitch user found: {username} -> id={user_id}")
    resp = requests.get(
        "https://api.twitch.tv/helix/channels/followers",
        headers=headers,
        params={"broadcaster_id": TWITCH_BROADCASTER_ID, "user_id": user_id},
    )
    log.info(f"Twitch followers API: status={resp.status_code}, response={resp.text[:300]}")
    if resp.status_code != 200:
        log.error(f"Twitch followers API falló ({resp.status_code}): {resp.text}")
        return False
    result = len(resp.json().get("data", [])) > 0
    log.info(f"check_twitch_follow({username}): user_id={user_id}, broadcaster_id={TWITCH_BROADCASTER_ID}, follows={result}")
    return result


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


class YouTubeCodeModal(ui.Modal, title="Pega el código de YouTube"):
    code = ui.TextInput(
        label="Código de Google",
        placeholder="Pega aquí el código de la URL después de autorizar",
        required=True,
        max_length=200,
    )

    async def on_submit(self, interaction: discord.Interaction):
        log.info(f"YouTubeCodeModal.on_submit iniciado por {interaction.user}")
        try:
            await interaction.response.defer(ephemeral=True)

            code_value = self.code.value.strip()

            if "code=" in code_value:
                import re
                match = re.search(r'code=([^&]+)', code_value)
                if match:
                    code_value = match.group(1)
                    log.info(f"Extracted YouTube code from URL: {code_value[:10]}...")

            log.info(f"YouTube código recibido: {code_value[:10]}...")

            import aiohttp as _aiohttp
            async with _aiohttp.ClientSession() as session:
                data = {
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "grant_type": "authorization_code",
                    "code": code_value,
                    "redirect_uri": GOOGLE_REDIRECT_URI,
                }
                async with session.post("https://oauth2.googleapis.com/token", data=data) as resp:
                    resp_text = await resp.text()
                    log.info(f"Google token response: {resp.status} - {resp_text[:200]}")
                    if resp.status != 200:
                        error_msg = "Código inválido o expirado."
                        if "500" in resp_text or resp.status == 500:
                            error_msg = (
                                "Error del servidor de Google (500).\n\n"
                                "Esto suele ocurrir cuando la aplicación de Google aún está en modo **Pruebas**.\n"
                                "El creador del servidor debe publicar la app en Google Console para que todos puedan verificarla.\n\n"
                                "Mientras tanto, usa **🟣 Verificar con Twitch** como alternativa."
                            )
                        elif "redirect_uri_mismatch" in resp_text:
                            error_msg = "Error: La URI de redirección no coincide con la configurada en Google Console."
                        elif "invalid_grant" in resp_text:
                            error_msg = "Código inválido o expirado. Solicita uno nuevo."
                        
                        await interaction.followup.send(
                            embed=discord.Embed(
                                title="❌ Error de Google",
                                description=error_msg,
                                color=discord.Color.red(),
                            ),
                            ephemeral=True,
                        )
                        return
                    token_data = await resp.json()
                    access_token = token_data["access_token"]

                headers = {"Authorization": f"Bearer {access_token}"}
                params = {
                    "part": "snippet",
                    "forChannelId": YOUTUBE_CHANNEL_ID,
                    "mine": "true",
                    "maxResults": 5,
                }
                async with session.get(
                    "https://www.googleapis.com/youtube/v3/subscriptions",
                    headers=headers,
                    params=params,
                ) as resp:
                    resp_text = await resp.text()
                    log.info(f"YouTube subscriptions response: {resp.status} - {resp_text[:300]}")
                    if resp.status != 200:
                        error_msg = f"Error de YouTube API: {resp_text[:200]}"
                        if resp.status == 500:
                            error_msg = (
                                "Error del servidor de YouTube (500).\n\n"
                                "La aplicación de Google necesita ser verificada para acceder a datos privados.\n"
                                "Usa **🟣 Verificar con Twitch** como alternativa mientras tanto."
                            )
                        elif resp.status == 403:
                            error_msg = (
                                "Acceso denegado (403).\n\n"
                                "La aplicación de Google no tiene permiso para ver suscripciones.\n"
                                "El creador debe habilitar la API de YouTube y verificar la app en Google Console."
                            )
                        
                        await interaction.followup.send(
                            embed=discord.Embed(
                                title="❌ Error al verificar",
                                description=error_msg,
                                color=discord.Color.red(),
                            ),
                            ephemeral=True,
                        )
                        return
                    data = await resp.json()
                    items = data.get("items", [])
                    log.info(f"YouTube subscription items: {len(items)}")

            if items:
                db.create_user(interaction.user.id, interaction.user.display_name)
                db.set_verified(interaction.user.id, True, "youtube", "youtube-verified")
                role = interaction.guild.get_role(MIEMBRO_ROLE_ID)
                if role:
                    await interaction.user.add_roles(role)
                await interaction.followup.send(
                    embed=discord.Embed(
                        title="✅ Verificado por YouTube",
                        description="Estás suscrito a mi canal.\n\nYa tienes el rol **Verificado**.",
                        color=discord.Color.green(),
                    ),
                    ephemeral=True,
                )
            else:
                await interaction.followup.send(
                    embed=discord.Embed(
                        title="❌ No estás suscrito",
                        description="No estás suscrito a mi canal de YouTube.\n\nSuscríbete: **https://youtube.com/@pokejgamer**",
                        color=discord.Color.red(),
                    ),
                    ephemeral=True,
                )
        except Exception as e:
            log.exception(f"Error en YouTubeCodeModal.on_submit: {e}")
            try:
                await interaction.followup.send(
                    embed=discord.Embed(
                        title="❌ Error interno",
                        description=f"Error: {e}",
                        color=discord.Color.red(),
                    ),
                    ephemeral=True,
                )
            except:
                pass


class YouTubeCodeView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="Pegar código YouTube", style=discord.ButtonStyle.red, emoji="📋", custom_id="paste_yt_code_btn")
    async def paste_code(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(YouTubeCodeModal())


class TwitchCodeModal(ui.Modal, title="Pega el código de Twitch"):
    code = ui.TextInput(
        label="Código de Twitch",
        placeholder="Pega aquí el código de la URL después de autorizar",
        required=True,
        max_length=200,
    )

    async def on_submit(self, interaction: discord.Interaction):
        log.info(f"TwitchCodeModal.on_submit iniciado por {interaction.user}")
        try:
            await interaction.response.defer(ephemeral=True)

            code_value = self.code.value.strip()

            if "code=" in code_value:
                import re
                match = re.search(r'code=([^&]+)', code_value)
                if match:
                    code_value = match.group(1)
                    log.info(f"Extracted Twitch code from URL: {code_value[:10]}...")

            log.info(f"Twitch código recibido: {code_value[:10]}...")

            import aiohttp as _aiohttp
            async with _aiohttp.ClientSession() as session:
                data = {
                    "client_id": TWITCH_CLIENT_ID,
                    "client_secret": TWITCH_CLIENT_SECRET,
                    "grant_type": "authorization_code",
                    "code": code_value,
                    "redirect_uri": TWITCH_REDIRECT_URI,
                }
                async with session.post("https://id.twitch.tv/oauth2/token", data=data) as resp:
                    resp_text = await resp.text()
                    log.info(f"Twitch token response: {resp.status} - {resp_text[:200]}")
                    if resp.status != 200:
                        await interaction.followup.send(
                            embed=discord.Embed(
                                title="❌ Código inválido",
                                description=f"Error de Twitch: {resp_text[:200]}",
                                color=discord.Color.red(),
                            ),
                            ephemeral=True,
                        )
                        return
                    token_data = await resp.json()
                    access_token = token_data["access_token"]

                headers = {
                    "Authorization": f"Bearer {access_token}",
                    "Client-Id": TWITCH_CLIENT_ID,
                }
                async with session.get(
                    "https://api.twitch.tv/helix/users",
                    headers=headers,
                ) as resp:
                    resp_text = await resp.text()
                    log.info(f"Twitch users response: {resp.status} - {resp_text[:300]}")
                    if resp.status != 200:
                        await interaction.followup.send(
                            embed=discord.Embed(
                                title="❌ Error al obtener usuario",
                                description=f"Error de Twitch: {resp_text[:200]}",
                                color=discord.Color.red(),
                            ),
                            ephemeral=True,
                        )
                        return
                    user_data = await resp.json()
                    twitch_users = user_data.get("data", [])
                    if not twitch_users:
                        await interaction.followup.send(
                            embed=discord.Embed(
                                title="❌ No se encontró tu usuario de Twitch",
                                description="No se pudo obtener tu información de Twitch.",
                                color=discord.Color.red(),
                            ),
                            ephemeral=True,
                        )
                        return
                    user_id = twitch_users[0]["id"]
                    log.info(f"Twitch user ID: {user_id}")

                async with session.get(
                    "https://api.twitch.tv/helix/channels/followed",
                    headers=headers,
                    params={"broadcaster_id": TWITCH_BROADCASTER_ID, "user_id": user_id},
                ) as resp:
                    resp_text = await resp.text()
                    log.info(f"Twitch followed response: {resp.status} - {resp_text[:300]}")
                    if resp.status != 200:
                        await interaction.followup.send(
                            embed=discord.Embed(
                                title="❌ Error al verificar",
                                description=f"Error de Twitch: {resp_text[:200]}",
                                color=discord.Color.red(),
                            ),
                            ephemeral=True,
                        )
                        return
                    data = await resp.json()
                    items = data.get("data", [])
                    log.info(f"Twitch followed items: {len(items)}")

            if items:
                db.create_user(interaction.user.id, interaction.user.display_name)
                db.set_verified(interaction.user.id, True, "twitch", "twitch-verified")
                role = interaction.guild.get_role(MIEMBRO_ROLE_ID)
                if role:
                    await interaction.user.add_roles(role)
                await interaction.followup.send(
                    embed=discord.Embed(
                        title="✅ Verificado por Twitch",
                        description="Sigues el canal en Twitch.\n\nYa tienes el rol **Verificado**.",
                        color=discord.Color.green(),
                    ),
                    ephemeral=True,
                )
            else:
                await interaction.followup.send(
                    embed=discord.Embed(
                        title="❌ No sigues el canal",
                        description="No sigues el canal en Twitch.\n\nSigue: **https://twitch.tv/pokejgamer**",
                        color=discord.Color.red(),
                    ),
                    ephemeral=True,
                )
        except Exception as e:
            log.exception(f"Error en TwitchCodeModal.on_submit: {e}")
            try:
                await interaction.followup.send(
                    embed=discord.Embed(
                        title="❌ Error interno",
                        description=f"Error: {e}",
                        color=discord.Color.red(),
                    ),
                    ephemeral=True,
                )
            except:
                pass


class TwitchCodeView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="Pegar código Twitch", style=discord.ButtonStyle.green, emoji="📋", custom_id="paste_twitch_code_btn")
    async def paste_code(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(TwitchCodeModal())


class YouTubeScreenshotModal(ui.Modal, title="Verificación de YouTube"):
    async def on_submit(self, interaction: discord.Interaction):
        pass


class YouTubeScreenshotView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="📸 Enviar screenshot", style=discord.ButtonStyle.red, emoji="📸", custom_id="yt_screenshot_btn")
    async def screenshot_button(self, interaction: discord.Interaction, button: ui.Button):
        try:
            dm_embed = discord.Embed(
                title="📸 Envía tu screenshot de YouTube",
                description=(
                    "Envía aquí una captura de pantalla de que estás **suscrito** a mi canal de YouTube.\n\n"
                    "**Cómo hacerlo:**\n"
                    "1. Haz clic en el enlace de abajo para ir a mi canal\n"
                    "2. Haz clic en el botón de suscripción\n"
                    "3. Haz una captura de pantalla que muestre que pone \"Suscrito\"\n"
                    "4. Envía la imagen aquí\n\n"
                    f"▶️ **[Ir a mi canal de YouTube](https://youtube.com/@pokejgamer)**"
                ),
                color=discord.Color.blue()
            )
            await interaction.user.send(embed=dm_embed)
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="📩 Te he enviado un MD",
                    description="Revisa tus mensajes privados para completar la verificación.",
                    color=discord.Color.blue()
                ),
                ephemeral=True
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="❌ No puedo enviarte MD",
                    description="Tienes los mensajes privados desactivados. Actívalos para verificar.",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )
            return

        def check(msg):
            return msg.author.id == interaction.user.id and msg.guild is None and msg.attachments

        try:
            msg = await interaction.client.wait_for('message', check=check, timeout=None)
        except:
            return

        attachment = msg.attachments[0]
        if not attachment.content_type or not attachment.content_type.startswith('image/'):
            await interaction.user.send(
                embed=discord.Embed(
                    title="❌ No es una imagen",
                    description="Por favor envía una captura de pantalla, no otro tipo de archivo. Intenta de nuevo.",
                    color=discord.Color.red()
                )
            )
            return

        image_data = await attachment.read()
        
        if not HAS_OCR:
            await interaction.user.send(
                embed=discord.Embed(
                    title="❌ Error de configuración",
                    description="El sistema de verificación no está disponible. Contacta al admin.",
                    color=discord.Color.red()
                )
            )
            return

        try:
            image = Image.open(io.BytesIO(image_data))
            text = pytesseract.image_to_string(image, lang='spa+eng')
            text_lower = text.lower()
        except Exception as e:
            await interaction.user.send(
                embed=discord.Embed(
                    title="❌ Error al procesar imagen",
                    description="No pude leer la imagen. Intenta con otra captura más clara.",
                    color=discord.Color.red()
                )
            )
            return

        has_subscribed = any(kw in text_lower for kw in SUBSCRIBED_KEYWORDS)
        has_channel = any(name in text_lower for name in YOUTUBE_CHANNEL_NAMES)
        has_youtube = "youtube" in text_lower or "youtu.be" in text_lower

        if has_subscribed and (has_channel or has_youtube):
            role = interaction.guild.get_role(MIEMBRO_ROLE_ID)
            if role:
                await interaction.user.add_roles(role)
            
            db.create_user(interaction.user.id, interaction.user.display_name)
            db.set_verified(interaction.user.id, True, "youtube", "youtube-screenshot")
            
            await interaction.user.send(
                embed=discord.Embed(
                    title="✅ ¡Verificación exitosa!",
                    description=(
                        f"Se confirmó que estás suscrito a mi canal de YouTube.\n"
                        f"Se te ha asignado el rol **{role.name}**.\n\n"
                        f"¡Gracias por suscribirte! 🔔"
                    ),
                    color=discord.Color.green()
                )
            )
        else:
            reasons = []
            if not has_subscribed:
                reasons.append("no se detectó \"Suscrito\" o \"Subscribed\"")
            if not has_channel and not has_youtube:
                reasons.append("no se detectó el nombre del canal o YouTube")
            
            await interaction.user.send(
                embed=discord.Embed(
                    title="❌ Verificación fallida",
                    description=(
                        "La imagen no cumple con los requisitos.\n\n"
                        f"**Motivo:** {', '.join(reasons)}\n\n"
                        "**Asegúrate de:**\n"
                        "- Enviar una captura de la página de suscripciones\n"
                        "- Que se vea claramente que pone \"Suscrito\"\n"
                        "- Que se vea el nombre del canal o el logo de YouTube\n\n"
                        "Intenta de nuevo con el botón."
                    ),
                    color=discord.Color.red()
                )
            )


class VerifyMainView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="Verificar con YouTube", style=discord.ButtonStyle.red, emoji="▶️", custom_id="verify_main_youtube_v3")
    async def youtube_button(self, interaction: discord.Interaction, button: ui.Button):
        role = interaction.guild.get_role(MIEMBRO_ROLE_ID) if interaction.guild else None
        if role and role in interaction.user.roles:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="✅ Ya estás verificado",
                    description="Ya tienes el rol **Verificado**. No necesitas verificar de nuevo.",
                    color=discord.Color.green(),
                ),
                ephemeral=True,
            )
            return
        
        if db.is_youtube_verified(str(interaction.user.id)):
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="✅ Ya estás verificado",
                    description="Ya tienes la verificación de YouTube activa.",
                    color=discord.Color.green(),
                ),
                ephemeral=True,
            )
            return

        embed = discord.Embed(
            title="▶️ Verificar con YouTube",
            description=(
                "**Paso 1:** Haz clic en el botón de abajo\n\n"
                "**Paso 2:** Ve a mi canal de YouTube y suscríbete si no lo has hecho\n\n"
                "**Paso 3:** Haz una captura de pantalla de que estás suscrito\n\n"
                "**Paso 4:** Envía la captura aquí\n\n"
                "El bot verificará automáticamente tu suscripción."
            ),
            color=discord.Color.red(),
        )
        await interaction.response.send_message(embed=embed, view=YouTubeScreenshotView(), ephemeral=True)

    @ui.button(label="Verificar con Twitch", style=discord.ButtonStyle.green, emoji="🟣", custom_id="verify_main_twitch_v3")
    async def twitch_button(self, interaction: discord.Interaction, button: ui.Button):
        role = interaction.guild.get_role(MIEMBRO_ROLE_ID) if interaction.guild else None
        if role and role in interaction.user.roles:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="✅ Ya estás verificado",
                    description="Ya tienes el rol **Verificado**. No necesitas verificar de nuevo.",
                    color=discord.Color.green(),
                ),
                ephemeral=True,
            )
            return
        params = {
            "client_id": TWITCH_CLIENT_ID,
            "redirect_uri": TWITCH_REDIRECT_URI,
            "response_type": "code",
            "scope": "user:read:follows",
        }
        url = f"https://id.twitch.tv/oauth2/authorize?{urlencode(params)}"
        embed = discord.Embed(
            title="🟣 Verificar con Twitch",
            description=(
                f"**Paso 1:** Haz clic en el enlace de abajo y autoriza\n\n"
                f"**Paso 2:** Se abrirá una página con un código verde. Cópialo.\n\n"
                f"**Paso 3:** Haz clic en el botón **📋 Pegar código Twitch** de abajo y pégalo\n\n"
                f"**[Clic aquí para autorizar]({url})**"
            ),
            color=discord.Color.green(),
        )
        await interaction.response.send_message(embed=embed, view=TwitchCodeView(), ephemeral=True)


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
            log.info(f" Verificados {assigned} miembros existentes")

    @tasks.loop(minutes=10)
    async def check_followers(self):
        guild = self.bot.guilds[0] if self.bot.guilds else None
        if not guild:
            return
        role = guild.get_role(MIEMBRO_ROLE_ID)
        if not role:
            return
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
            log.info(f" check_followers: removido verificación de {removed} miembros que dejaron de seguir")

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
                "1. Haz clic en uno de los botones de abajo\n"
                "2. Sigue los pasos que se muestran\n\n"
                "**Opciones:**\n"
                "▶️ **YouTube** → Envía un screenshot de que estás suscrito\n"
                "🟣 **Twitch** → Verifica directamente con tu cuenta de Twitch\n\n"
                "**Requisitos:**\n"
                "• Debes seguir el canal en **Twitch** o estar suscrito en **YouTube**\n"
                "• Tu suscripción/seguimiento debe ser **pública**\n\n"
                "⚠️ **Nota:** Si YouTube no funciona, usa Twitch como alternativa."
            ),
            color=discord.Color.blue(),
        )
        embed.set_footer(text="Pulsa el botón para verificar")
        await ctx.send(embed=embed, view=VerifyMainView())

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


def check_youtube_subscription(channel_name: str) -> bool:
    if not YOUTUBE_API_KEY:
        log.warning("No hay YOUTUBE_API_KEY configurada")
        return False
    channel_id = None
    handle = None
    if "youtube.com/@" in channel_name:
        m = re.search(r"youtube\.com/@([a-zA-Z0-9_.-]+)", channel_name)
        if m:
            handle = m.group(1)
    else:
        handle = channel_name.lstrip("@")
    if handle:
        log.info(f"YouTube handle: {handle}")
        resp = requests.get(
            "https://www.googleapis.com/youtube/v3/channels",
            params={"key": YOUTUBE_API_KEY, "forHandle": handle, "part": "id,subscriberCount"},
        )
        if resp.status_code == 200:
            items = resp.json().get("items", [])
            if items:
                channel_id = items[0]["id"]
                log.info(f"YouTube channel_id: {channel_id}")
    if not channel_id:
        log.error(f"No se pudo obtener channel_id de YouTube para: {channel_name}")
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
        log.error(f"YouTube subscriptions API falló ({resp.status_code}): {resp.text}")
        log.info("NOTA: YouTube subscriptions requiere OAuth2 para verificar suscripciones de otros usuarios")
        return False
    result = len(resp.json().get("items", [])) > 0
    log.info(f"check_youtube_subscription({channel_name}): channel_id={channel_id}, target={YOUTUBE_CHANNEL_ID}, subscribed={result}")
    return result


async def setup(bot: commands.Bot):
    await bot.add_cog(Verify(bot))
    bot.add_view(VerifyMainView())
    bot.add_view(YouTubeScreenshotView())
    bot.add_view(TwitchCodeView())
