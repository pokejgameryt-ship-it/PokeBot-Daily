import discord
from discord.ext import commands
from discord import app_commands
import io
import re
import database as db
from config import MIEMBRO_ROLE_ID, YOUTUBE_CHANNEL_ID

try:
    import pytesseract
    from PIL import Image
    HAS_OCR = True
except ImportError:
    HAS_OCR = False

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

class YouTubeVerifyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Verificar suscripción",
        style=discord.ButtonStyle.green,
        emoji="📺",
        custom_id="yt_verify_button"
    )
    async def verify_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = str(interaction.user.id)
        if db.is_youtube_verified(user_id):
            embed = discord.Embed(
                title="✅ Ya verificado",
                description="Ya tienes la verificación de YouTube activa.",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        embed = discord.Embed(
            title="📸 Envía tu screenshot",
            description=(
                "Envía una captura de pantalla de que estás **suscrito** a mi canal de YouTube.\n\n"
                "**Cómo hacerlo:**\n"
                "1. Ve a mi canal de YouTube\n"
                "2. Haz clic en el botón de suscripción\n"
                "3. Haz una captura de pantalla muestre que pone \"Suscrito\"\n"
                "4. Envía la imagen aquí\n\n"
                "⏰ Tienes 60 segundos para enviar la imagen."
            ),
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

        def check(msg):
            return msg.author.id == interaction.user.id and msg.attachments

        try:
            msg = await interaction.client.wait_for('message', check=check, timeout=60.0)
        except:
            embed = discord.Embed(
                title="⏰ Tiempo agotado",
                description="No enviaste la imagen a tiempo. Intenta de nuevo.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        attachment = msg.attachments[0]
        if not attachment.content_type or not attachment.content_type.startswith('image/'):
            embed = discord.Embed(
                title="❌ No es una imagen",
                description="Por favor envía una captura de pantalla, no otro tipo de archivo.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        image_data = await attachment.read()
        
        if not HAS_OCR:
            embed = discord.Embed(
                title="❌ Error de configuración",
                description="El sistema de verificación no está disponible. Contacta al admin.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        try:
            image = Image.open(io.BytesIO(image_data))
            text = pytesseract.image_to_string(image, lang='spa+eng')
            text_lower = text.lower()
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error al procesar imagen",
                description="No pude leer la imagen. Intenta con otra captura más clara.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        has_subscribed = any(kw in text_lower for kw in SUBSCRIBED_KEYWORDS)
        has_channel = any(name in text_lower for name in YOUTUBE_CHANNEL_NAMES)
        has_youtube = "youtube" in text_lower or "youtu.be" in text_lower

        if has_subscribed and (has_channel or has_youtube):
            role = interaction.guild.get_role(MIEMBRO_ROLE_ID)
            if role:
                await interaction.user.add_roles(role)
            
            db.mark_youtube_verified(user_id)
            
            embed = discord.Embed(
                title="✅ ¡Verificación exitosa!",
                description=(
                    f"Se confirmó que estás suscrito a mi canal de YouTube.\n"
                    f"Se te ha asignado el rol **{role.name}** si lo tenías antes.\n\n"
                    f"¡Gracias por suscribirte! 🔔"
                ),
                color=discord.Color.green()
            )
            await interaction.followup.send(embed=embed, ephemeral=False)
        else:
            reasons = []
            if not has_subscribed:
                reasons.append("no se detectó \"Suscrito\" o \"Subscribed\"")
            if not has_channel and not has_youtube:
                reasons.append("no se detectó el nombre del canal o YouTube")
            
            embed = discord.Embed(
                title="❌ Verificación fallida",
                description=(
                    "La imagen no cumple con los requisitos.\n\n"
                    f"**Motivo:** {', '.join(reasons)}\n\n"
                    "**Asegúrate de:**\n"
                    "- Enviar una captura de la página de suscripciones\n"
                    "- Que se vea claramente que pone \"Suscrito\"\n"
                    "- Que se vea el nombre del canal o el logo de YouTube"
                ),
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)


class YouTubeVerify(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.add_view(YouTubeVerifyView())

    @app_commands.command(name="verificar-youtube", description="Verifica tu suscripción a YouTube")
    async def verificar_youtube(self, interaction: discord.Interaction):
        if db.is_youtube_verified(str(interaction.user.id)):
            embed = discord.Embed(
                title="✅ Ya verificado",
                description="Ya tienes la verificación de YouTube activa.",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        embed = discord.Embed(
            title="📺 Verificación de YouTube",
            description=(
                "Para obtener el rol de **Verificado**, necesitas demostrar que estás "
                "suscrito a mi canal de YouTube.\n\n"
                "**Pasos:**\n"
                "1. Haz clic en el botón de abajo\n"
                "2. Ve a mi canal de YouTube y suscríbete si no lo has hecho\n"
                "3. Haz una captura de pantalla de que estás suscrito\n"
                "4. Envía la captura aquí\n\n"
                "El bot verificará automáticamente tu suscripción."
            ),
            color=discord.Color.blue()
        )
        
        view = YouTubeVerifyView()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @app_commands.command(name="youtube-info", description="Muestra información sobre la verificación de YouTube")
    async def youtube_info(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="📺 Verificación de YouTube",
            description=(
                "Verifica tu suscripción a YouTube para obtener roles especiales.\n\n"
                "**Cómo verificar:**\n"
                "1. Usa `/verificar-youtube`\n"
                "2. Haz clic en el botón\n"
                "3. Envía una captura de que estás suscrito\n\n"
                "**Requisitos:**\n"
                "- La captura debe mostrar claramente que estás suscrito\n"
                "- Debe verse el nombre del canal o el logo de YouTube\n"
                "- Formatos aceptados: PNG, JPG, WEBP"
            ),
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(YouTubeVerify(bot))
