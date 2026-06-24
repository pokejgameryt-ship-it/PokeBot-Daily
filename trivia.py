import random
import discord
from discord.ext import commands
from discord import app_commands
import database as db
from config import TRIVIA_POINTS

STREAK_ROLE_ID = 1519370767106576514


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
        "question": "¿Cuál es el Pokémon más pesado de la 1ª generación?",
        "correct": "Onix",
        "options": ["Onix", "Rhydon", "Snorlax"],
    },
    {
        "question": "¿Qué Pokémon es el mascot de la franquicia?",
        "correct": "Pikachu",
        "options": ["Pikachu", "Charizard", "Mewtwo"],
    },
    {
        "question": "¿Cuántos Pokémon hay en la Pokédex Nacional de Gen 1?",
        "correct": "151",
        "options": ["150", "151", "152"],
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
    {
        "question": "¿Cuál es la habilidad de Slaking?",
        "correct": "Holgazanería",
        "options": ["Holgazanería", "Velo Arena", "Cuerpo Puro"],
    },
    {
        "question": "¿De qué tipo es Garchomp?",
        "correct": "Dragón/Tierra",
        "options": ["Dragón/Tierra", "Dragón/Volador", "Tierra/Lucha"],
    },
    {
        "question": "¿Cuál es la evolución de Scyther con piedra obscura?",
        "correct": "Scizor",
        "options": ["Scizor", "Kleavor", "No evoluciona"],
    },
    {
        "question": "¿Qué Pokémon tiene la capacidad de dar falsos golpes críticos?",
        "correct": "Machamp",
        "options": ["Machamp", "Lucario", "Garchomp"],
    },
    {
        "question": "¿Cuál es el Pokémon más rápido de Gen 1?",
        "correct": "Electrode",
        "options": ["Electrode", "Jolteon", "Alakazam"],
    },
    {
        "question": "¿De qué tipo es Gengar?",
        "correct": "Fantasma/Veneno",
        "options": ["Fantasma/Veneno", "Fantasma/Siniestro", "Solo Fantasma"],
    },
    {
        "question": "¿Qué Pokémon legendario controla el tiempo?",
        "correct": "Dialga",
        "options": ["Dialga", "Palkia", "Giratina"],
    },
    {
        "question": "¿Qué Pokémon legendario controla el océano?",
        "correct": "Kyogre",
        "options": ["Kyogre", "Groudon", "Palkia"],
    },
    {
        "question": "¿Qué Pokémon legendario controla la tierra?",
        "correct": "Groudon",
        "options": ["Groudon", "Kyogre", "Rayquaza"],
    },
    {
        "question": "¿Cuál es el tipo de Lucario?",
        "correct": "Lucha/Acero",
        "options": ["Lucha/Acero", "Lucha/Veneno", "Acero/Dragón"],
    },
    {
        "question": "¿Qué Pokémon es conocido como el Pokémon Ave?",
        "correct": "Ho-Oh",
        "options": ["Ho-Oh", "Lugia", "Articuno"],
    },
    {
        "question": "¿Cuántas evoluciones tiene Eevee?",
        "correct": "9",
        "options": ["7", "8", "9"],
    },
    {
        "question": "¿Cuál es el Pokémon más alto?",
        "correct": "Celesteela",
        "options": ["Celesteela", "Wailord", "Eternatus"],
    },
    {
        "question": "¿Qué Pokémon absorbe el aliento de los rivales?",
        "correct": "Shedinja",
        "options": ["Shedinja", "Dusclops", "Banette"],
    },
    {
        "question": "¿De qué tipo es Umbreon?",
        "correct": "Siniestro",
        "options": ["Siniestro", "Fantasma", "Psíquico"],
    },
    {
        "question": "¿Cuál es la evolución de Togepi?",
        "correct": "Togetic",
        "options": ["Togetic", "Togekiss", "Pichu"],
    },
    {
        "question": "¿Qué Pokémon tiene 1 solo HP por su habilidad?",
        "correct": "Shedinja",
        "options": ["Shedinja", "Duskull", "Sableye"],
    },
    {
        "question": "¿Cuál es el Pokémon inicial de tipo fuego en Gen 1?",
        "correct": "Charmander",
        "options": ["Charmander", "Squirtle", "Bulbasaur"],
    },
    {
        "question": "¿De qué tipo es Tyranitar?",
        "correct": "Roca/Siniestro",
        "options": ["Roca/Siniestro", "Roca/Dragón", "Tierra/Siniestro"],
    },
    {
        "question": "¿Cuál es la evolución final de Squirtle?",
        "correct": "Blastoise",
        "options": ["Wartortle", "Blastoise", "Squirtle"],
    },
    {
        "question": "¿Qué Pokémon se camufla como árbol?",
        "correct": "Sudowoodo",
        "options": ["Sudowoodo", "Tropius", "Exeggutor"],
    },
    {
        "question": "¿Cuál es el Pokémon más rápido de Gen 4?",
        "correct": "Drapion",
        "options": ["Drapion", "Weavile", "Jolteon"],
    },
    {
        "question": "¿Qué Pokémon legendario del cielo puede controlar el clima?",
        "correct": "Rayquaza",
        "options": ["Rayquaza", "Groudon", "Kyogre"],
    },
    {
        "question": "¿Cuál es la evolución final de Totodile?",
        "correct": "Feraligatr",
        "options": ["Feraligatr", "Croconaw", "Totodile"],
    },
    {
        "question": "¿De qué tipo es Absol?",
        "correct": "Siniestro",
        "options": ["Siniestro", "Fantasma", "Lucha"],
    },
    {
        "question": "¿Qué Pokémon tiene forma de pokeball?",
        "correct": "Klefki",
        "options": ["Klefki", "Rotom", "Mimikyu"],
    },
    {
        "question": "¿Cuál es el Pokémon más pesado de todos?",
        "correct": "Celesteela",
        "options": ["Celesteela", "Cosmoem", "Giratina"],
    },
    {
        "question": "¿Qué Pokémon evoluciona con piedra agua?",
        "correct": "Staryu",
        "options": ["Staryu", "Poliwag", "Tentacool"],
    },
    {
        "question": "¿Cuál es el tipo de Dragonite?",
        "correct": "Dragón/Volador",
        "options": ["Dragón/Volador", "Dragón/Fuego", "Volador/Normal"],
    },
    {
        "question": "¿Qué Pokémon es el mascot de Pokémon Go?",
        "correct": "Pikachu",
        "options": ["Pikachu", "Eevee", "Mew"],
    },
    {
        "question": "¿Cuántos Pokémon legendarios hay en Gen 1?",
        "correct": "5",
        "options": ["3", "4", "5"],
    },
    {
        "question": "¿De qué tipo es Arcanine?",
        "correct": "Fuego",
        "options": ["Fuego", "Fuego/Lucha", "Normal"],
    },
]


class TriviaView(discord.ui.View):
    def __init__(self, correct_answer: str, trivia_id: int, options: list):
        super().__init__(timeout=60)
        self.correct_answer = correct_answer
        self.trivia_id = trivia_id
        self.options = options
        self.responders = set()

    @discord.ui.button(label="A", style=discord.ButtonStyle.primary)
    async def option_a(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.check_answer(interaction, 0)

    @discord.ui.button(label="B", style=discord.ButtonStyle.primary)
    async def option_b(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.check_answer(interaction, 1)

    @discord.ui.button(label="C", style=discord.ButtonStyle.primary)
    async def option_c(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.check_answer(interaction, 2)

    async def check_answer(self, interaction: discord.Interaction, index: int):
        if interaction.user.id in self.responders:
            await interaction.response.send_message(
                "Ya has respondido esta trivia.", ephemeral=True
            )
            return

        self.responders.add(interaction.user.id)

        selected_option = self.options[index]
        is_correct = selected_option == self.correct_answer

        if is_correct:
            db.update_score(interaction.user.id, TRIVIA_POINTS["correct"], interaction.user.display_name)
            streak_change = db.update_trivia_stats(interaction.user.id, True, interaction.user.display_name)
            db.mark_trivia_answered(self.trivia_id, interaction.user.id)
            score = db.get_total_score(interaction.user.id)
            streak = db.get_streak(interaction.user.id)

            if streak_change["old_streak"] == 0 and streak_change["new_streak"] > 0:
                role = interaction.guild.get_role(STREAK_ROLE_ID)
                if role:
                    await interaction.user.add_roles(role)

            embed = discord.Embed(
                title="✅ ¡Correcto!",
                description=f"La respuesta **{self.correct_answer}** es correcta.",
                color=discord.Color.green(),
            )
            embed.add_field(name="Puntos ganados", value=f"+{TRIVIA_POINTS['correct']}")
            embed.add_field(name="Puntos totales", value=str(score))
            embed.add_field(name="Racha actual", value=f"{streak} 🔥")
            embed.set_footer(text="Solo tú puedes ver esta respuesta")
        else:
            streak_change = db.update_trivia_stats(interaction.user.id, False, interaction.user.display_name)
            db.mark_trivia_answered(self.trivia_id, interaction.user.id)

            if streak_change["old_streak"] > 0 and streak_change["new_streak"] == 0:
                role = interaction.guild.get_role(STREAK_ROLE_ID)
                if role:
                    await interaction.user.remove_roles(role)

            embed = discord.Embed(
                title="❌ Incorrecto",
                description=f"Tu respuesta: **{selected_option}**\nLa correcta: **{self.correct_answer}**",
                color=discord.Color.red(),
            )
            embed.set_footer(text="Solo tú puedes ver esta respuesta")

        await interaction.response.send_message(embed=embed, ephemeral=True)


class Trivia(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="trivia")
    async def trivia_command(self, ctx: commands.Context):
        daily = db.get_daily_trivia()
        if daily:
            embed = discord.Embed(
                title="📚 Trivia del Día",
                description="Ya有人 respondió la trivia de hoy. Vuelve mañana.",
                color=discord.Color.orange(),
            )
            embed.add_field(name="Pregunta", value=daily["question"])
            embed.add_field(name="Respuesta", value=daily["correct_answer"])
            await ctx.send(embed=embed)
            return

        trivia = random.choice(POKEMON_TRIVIA)
        options = trivia["options"][:]
        random.shuffle(options)

        db.save_trivia_question(trivia["question"], trivia["correct"], options)

        embed = discord.Embed(
            title="🎮 Trivia Pokémon del Día",
            description=trivia["question"],
            color=discord.Color.blue(),
        )
        embed.add_field(name="A", value=options[0], inline=False)
        embed.add_field(name="B", value=options[1], inline=False)
        embed.add_field(name="C", value=options[2], inline=False)
        embed.set_footer(text="Tienes 60 segundos para responder.")

        correct_index = options.index(trivia["correct"])
        label = chr(65 + correct_index)

        daily = db.get_daily_trivia()
        view = TriviaView(trivia["correct"], daily["id"], options)
        await ctx.send(embed=embed, view=view)

    @app_commands.command(name="trivia", description="Juega la trivia Pokémon del día")
    async def trivia_slash(self, interaction: discord.Interaction):
        daily = db.get_daily_trivia()
        if daily:
            embed = discord.Embed(
                title="📚 Trivia del Día",
                description="Ya有人 respondió la trivia de hoy. Vuelve mañana.",
                color=discord.Color.orange(),
            )
            embed.add_field(name="Pregunta", value=daily["question"])
            embed.add_field(name="Respuesta", value=daily["correct_answer"])
            await interaction.response.send_message(embed=embed)
            return

        trivia = random.choice(POKEMON_TRIVIA)
        options = trivia["options"][:]
        random.shuffle(options)

        db.save_trivia_question(trivia["question"], trivia["correct"], options)

        embed = discord.Embed(
            title="🎮 Trivia Pokémon del Día",
            description=trivia["question"],
            color=discord.Color.blue(),
        )
        embed.add_field(name="A", value=options[0], inline=False)
        embed.add_field(name="B", value=options[1], inline=False)
        embed.add_field(name="C", value=options[2], inline=False)
        embed.set_footer(text="Tienes 60 segundos para responder.")

        correct_index = options.index(trivia["correct"])
        label = chr(65 + correct_index)

        daily = db.get_daily_trivia()
        view = TriviaView(trivia["correct"], daily["id"], options)
        await interaction.response.send_message(embed=embed, view=view)

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
