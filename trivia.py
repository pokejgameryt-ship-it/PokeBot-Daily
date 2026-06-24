import random
import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime
import database as db
from config import TRIVIA_POINTS, TRIVIA_CHANNEL_ID, STREAK_ROLE_ID

DIFFICULTY_CONFIG = {
    "easy": {"label": "Fácil", "emoji": "🟢", "points": 5, "color": discord.Color.green()},
    "medium": {"label": "Intermedia", "emoji": "🟡", "points": 10, "color": discord.Color.gold()},
    "hard": {"label": "Difícil", "emoji": "🔴", "points": 15, "color": discord.Color.red()},
}

TRIVIA_EASY = [
    {"question": "¿Cuál es el tipo de Pikachu?", "correct": "Eléctrico", "options": ["Eléctrico", "Fuego", "Normal"]},
    {"question": "¿Cuál es la evolución final de Charmander?", "correct": "Charizard", "options": ["Charmeleon", "Charizard", "Charmander"]},
    {"question": "¿De qué tipo es Bulbasaur?", "correct": "Planta/Veneno", "options": ["Planta/Veneno", "Agua/Planta", "Solo Planta"]},
    {"question": "¿Qué Pokémon es el mascot de la franquicia?", "correct": "Pikachu", "options": ["Pikachu", "Charizard", "Mewtwo"]},
    {"question": "¿Cuántos Pokémon hay en la Pokédex de Gen 1?", "correct": "151", "options": ["150", "151", "152"]},
    {"question": "¿Cuál es el tipo de Mewtwo?", "correct": "Psíquico", "options": ["Psíquico", "Fantasma", "Normal"]},
    {"question": "¿Qué Pokémon inicial es de tipo fuego en Gen 1?", "correct": "Charmander", "options": ["Charmander", "Squirtle", "Bulbasaur"]},
    {"question": "¿Cuál es la evolución final de Squirtle?", "correct": "Blastoise", "options": ["Wartortle", "Blastoise", "Squirtle"]},
    {"question": "¿Cuál es la evolución final de Totodile?", "correct": "Feraligatr", "options": ["Feraligatr", "Croconaw", "Totodile"]},
    {"question": "¿Qué Pokémon legendario controla el tiempo?", "correct": "Dialga", "options": ["Dialga", "Palkia", "Giratina"]},
    {"question": "¿Qué Pokémon legendario controla el océano?", "correct": "Kyogre", "options": ["Kyogre", "Groudon", "Palkia"]},
    {"question": "¿Qué Pokémon legendario controla la tierra?", "correct": "Groudon", "options": ["Groudon", "Kyogre", "Rayquaza"]},
    {"question": "¿De qué tipo es Gengar?", "correct": "Fantasma/Veneno", "options": ["Fantasma/Veneno", "Fantasma/Siniestro", "Solo Fantasma"]},
    {"question": "¿De qué tipo es Lucario?", "correct": "Lucha/Acero", "options": ["Lucha/Acero", "Lucha/Veneno", "Acero/Dragón"]},
    {"question": "¿Qué Pokémon es conocido como el Pokémon Ave?", "correct": "Ho-Oh", "options": ["Ho-Oh", "Lugia", "Articuno"]},
    {"question": "¿De qué tipo es Umbreon?", "correct": "Siniestro", "options": ["Siniestro", "Fantasma", "Psíquico"]},
    {"question": "¿Cuál es la evolución de Togepi?", "correct": "Togetic", "options": ["Togetic", "Togekiss", "Pichu"]},
    {"question": "¿Cuántas evoluciones tiene Eevee?", "correct": "9", "options": ["7", "8", "9"]},
    {"question": "¿De qué tipo es Tyranitar?", "correct": "Roca/Siniestro", "options": ["Roca/Siniestro", "Roca/Dragón", "Tierra/Siniestro"]},
    {"question": "¿Qué Pokémon se camufla como árbol?", "correct": "Sudowoodo", "options": ["Sudowoodo", "Tropius", "Exeggutor"]},
    {"question": "¿De qué tipo es Dragonite?", "correct": "Dragón/Volador", "options": ["Dragón/Volador", "Dragón/Fuego", "Volador/Normal"]},
    {"question": "¿De qué tipo es Arcanine?", "correct": "Fuego", "options": ["Fuego", "Fuego/Lucha", "Normal"]},
    {"question": "¿De qué tipo es Absol?", "correct": "Siniestro", "options": ["Siniestro", "Fantasma", "Lucha"]},
    {"question": "¿Qué Pokémon evoluciona con piedra fuego?", "correct": "Vulpix", "options": ["Vulpix", "Eevee", "Pikachu"]},
    {"question": "¿Qué Pokémon evoluciona con piedra agua?", "correct": "Staryu", "options": ["Staryu", "Poliwag", "Tentacool"]},
    {"question": "¿Qué Pokémon legendario del cielo controla el clima?", "correct": "Rayquaza", "options": ["Rayquaza", "Groudon", "Kyogre"]},
    {"question": "¿De qué tipo es Onix?", "correct": "Roca/Tierra", "options": ["Roca/Tierra", "Tierra/Planta", "Roca/Acero"]},
    {"question": "¿Qué Pokémon tiene forma de pokeball?", "correct": "Klefki", "options": ["Klefki", "Rotom", "Mimikyu"]},
    {"question": "¿Cuál es el tipo de Jolteon?", "correct": "Eléctrico", "options": ["Eléctrico", "Agua", "Fuego"]},
    {"question": "¿Qué Pokémon es el mascot de Pokémon Go?", "correct": "Pikachu", "options": ["Pikachu", "Eevee", "Mew"]},
]

TRIVIA_MEDIUM = [
    {"question": "¿Cuál es la habilidad de Slaking?", "correct": "Holgazanería", "options": ["Holgazanería", "Velo Arena", "Cuerpo Puro"]},
    {"question": "¿Qué Pokémon tiene la capacidad de dar falsos golpes críticos?", "correct": "Machamp", "options": ["Machamp", "Lucario", "Garchomp"]},
    {"question": "¿Cuál es la evolución de Scyther con piedra obscura?", "correct": "Scizor", "options": ["Scizor", "Kleavor", "No evoluciona"]},
    {"question": "¿Qué Pokémon tiene 1 solo HP por su habilidad?", "correct": "Shedinja", "options": ["Shedinja", "Duskull", "Sableye"]},
    {"question": "¿Cuál es la habilidad de Garchomp?", "correct": "Piélago", "options": ["Piélago", "Presión", "Cuerpo Puro"]},
    {"question": "¿Qué objeto evoluciona a Onix en Steelix?", "correct": "Diente de Acero", "options": ["Diente de Acero", "Piedra Obscura", "Escama Humilde"]},
    {"question": "¿Cuál es la habilidad de Blissey?", "correct": "Naturalizar", "options": ["Naturalizar", "Fuga", "Escudo Natural"]},
    {"question": "¿Qué objeto evoluciona a Porygon2?", "correct": "Disco Dubioso", "options": ["Disco Dubioso", "Disco Actualización", "Disco Elegant"]},
    {"question": "¿Cuál es la habilidad de Gengar?", "correct": "Curanderismo", "options": ["Curanderismo", "Levitación", " absorción"]},
    {"question": "¿Qué objeto evoluciona a Cleffa?", "correct": "Piedra Lunar", "options": ["Piedra Lunar", "Piedra Solar", "Piedra Fuego"]},
    {"question": "¿Cuál es la habilidad de Tyranitar?", "correct": "Armadura Batalla", "options": ["Armadura Batalla", "Piel Tosca", "Impulso"]},
    {"question": "¿Qué objeto evoluciona a Scyther en Kleavor?", "correct": "Roca Gigante", "options": ["Roca Gigante", "Piedra Obscura", "Roca Caliza"]},
    {"question": "¿Cuál es la habilidad de Metagross?", "correct": "Cuerpo Puro", "options": ["Cuerpo Puro", "Levitación", "Piélago"]},
    {"question": "¿Qué objeto evoluciona a Gliscor?", "correct": "Piedra Nocturna", "options": ["Piedra Nocturna", "Piedra Lunar", "Escama Humilde"]},
    {"question": "¿Cuál es la habilidad de Salamence?", "correct": "Intimidación", "options": ["Intimidación", "Velo Arena", "Manto Arena"]},
    {"question": "¿Qué objeto evoluciona a Electivire?", "correct": "Cable de Combate", "options": ["Cable de Combate", "Piedra Trueno", "Piedra Solar"]},
    {"question": "¿Cuál es la habilidad de Gyarados?", "correct": "Intimidación", "options": ["Intimidación", "Presión", "Manto Arena"]},
    {"question": "¿Qué objeto evoluciona a Magmortar?", "correct": "Cable de Combate", "options": ["Cable de Combate", "Piedra Fuego", "Piedra Solar"]},
    {"question": "¿Cuál es la habilidad de Swampert?", "correct": "Torrente", "options": ["Torrente", "Ancla Arena", "Cuerpo Puro"]},
    {"question": "¿Qué objeto evoluciona a Rhyperior?", "correct": "Garra Roca", "options": ["Garra Roca", "Piedra Roca", "Piedra Tierra"]},
    {"question": "¿Cuál es la habilidad de Dusknoir?", "correct": "Presión", "options": ["Presión", "Levitación", "Curanderismo"]},
    {"question": "¿Qué objeto evoluciona a Togekiss?", "correct": "Piedra Día", "options": ["Piedra Día", "Piedra Lunar", "Piedra Solar"]},
    {"question": "¿Cuál es la habilidad de Froslass?", "correct": "Capa Nieve", "options": ["Capa Nieve", "Levitación", "Corpo Cura"]},
    {"question": "¿Qué objeto evoluciona a Tangrowth?", "correct": "Nivel + Nivel", "options": ["Nivel + Nivel", "Piedra Planta", "Ritmo"]},
    {"question": "¿Cuál es la habilidad de Abomasnow?", "correct": "Nieve Albedo", "options": ["Nieve Albedo", "Piel Tosca", "Roca Pura"]},
    {"question": "¿Qué objeto evoluciona a Yanmega?", "correct": "Nivel + Nivel", "options": ["Nivel + Nivel", "Piedra Sol", "Ritmo"]},
    {"question": "¿Cuál es la habilidad de Hippowdon?", "correct": "Ancla Arena", "options": ["Ancla Arena", "Velo Arena", "Manto Arena"]},
    {"question": "¿Qué objeto evoluciona a Mamoswine?", "correct": "Piedra Antigua", "options": ["Piedra Antigua", "Piedra Hielo", "Piedra Lunar"]},
    {"question": "¿Cuál es la habilidad de Togekiss?", "correct": "Alegría", "options": ["Alegría", "Grito Guerrero", "Magia Natural"]},
    {"question": "¿Qué objeto evoluciona a Gallade?", "correct": "Piedra Alba", "options": ["Piedra Alba", "Piedra Lunar", "Piedra Día"]},
]

TRIVIA_HARD = [
    {"question": "¿Cuál es el stat base de ataque de Mewtwo?", "correct": "150", "options": ["130", "150", "110"]},
    {"question": "¿Cuánto mide Blissey en metros?", "correct": "1.50", "options": ["1.50", "1.80", "2.00"]},
    {"question": "¿Cuál es el peso base de Snorlax en kg?", "correct": "460", "options": ["460", "350", "520"]},
    {"question": "¿En qué generación apareció el movimiento Cascada?", "correct": "Gen 1", "options": ["Gen 1", "Gen 2", "Gen 3"]},
    {"question": "¿Cuál es la probabilidad de captura base de Articuno?", "correct": "3", "options": ["3", "5", "1"]},
    {"question": "¿Cuál es el stat base de defensa de Garchomp?", "correct": "95", "options": ["85", "95", "105"]},
    {"question": "¿Qué Pokémon tiene el stat base de velocidad más alto?", "correct": "Regieleki", "options": ["Regieleki", "Ninjask", "Jolteon"]},
    {"question": "¿Cuál es el stat base de HP de Chansey?", "correct": "250", "options": ["200", "250", "300"]},
    {"question": "¿Cuántos Pokémon hay en la Pokédex Nacional de Gen 8?", "correct": "893", "options": ["890", "893", "900"]},
    {"question": "¿Cuál es el stat base de ataque de Rayquaza?", "correct": "150", "options": ["140", "150", "160"]},
    {"question": "¿Qué Pokémon tiene la defensa base más alta?", "correct": "Shuckle", "options": ["Shuckle", "Steelix", "Aggron"]},
    {"question": "¿Cuál es el stat base de Sp. Atk de Gengar?", "correct": "130", "options": ["120", "130", "140"]},
    {"question": "¿Cuánto pesa Groudon en kg?", "correct": "950", "options": ["950", "850", "1050"]},
    {"question": "¿Cuál es la descripción de Bulbasaur en Pokédex Roja?", "correct": "Semilla", "options": ["Semilla", "Hierba", "Hoja"]},
    {"question": "¿Qué Pokémon tiene el stat base de Sp. Def más alto?", "correct": "Shuckle", "options": ["Shuckle", "Claydol", "Deoxys"]},
    {"question": "¿Cuál es el stat base de ataque de Deoxys Ataque?", "correct": "180", "options": ["150", "180", "200"]},
    {"question": "¿En qué evento se obtuvo Jirachi europeo?", "correct": "Wish Maker", "options": ["Wish Maker", "Pokemon Festa", "Nintendo World"]},
    {"question": "¿Cuál es la altura base de Wailord en metros?", "correct": "14.5", "options": ["14.5", "12.0", "16.0"]},
    {"question": "¿Qué Pokémon tiene el stat base total más alto (sin mega)?", "correct": "Arceus", "options": ["Arceus", "Mewtwo", "Rayquaza"]},
    {"question": "¿Cuál es el stat base de defensa de Eternatus?", "correct": "95", "options": ["85", "95", "105"]},
    {"question": "¿Cuántos Pokémon legendarios hay en Gen 4?", "correct": "13", "options": ["11", "13", "15"]},
    {"question": "¿Cuál es la descripción de Charizard en Pokédex Roja?", "correct": "Llama", "options": ["Llama", "Fuego", "Dragón"]},
    {"question": "¿Qué objeto necesita Deoxys para cambiar de forma?", "correct": "Meteorito", "options": ["Meteorito", "Piedra Lunar", "Disco Dubioso"]},
    {"question": "¿Cuál es el stat base de HP de Blissey?", "correct": "255", "options": ["250", "255", "260"]},
    {"question": "¿En qué ruta se captura a Beldum en Gen 3?", "correct": "Ruta 119", "options": ["Ruta 119", "Ruta 120", "Ruta 118"]},
    {"question": "¿Cuál es la altura base de Celesteela en metros?", "correct": "9.2", "options": ["9.2", "7.5", "11.0"]},
    {"question": "¿Qué Pokémon tiene el stat base de Sp. Def más bajo (legendario)?", "correct": "Deoxys", "options": ["Deoxys", "Mewtwo", "Groudon"]},
    {"question": "¿Cuál es el stat base de ataque de Zacian Hero?", "correct": "130", "options": ["120", "130", "170"]},
    {"question": "¿Cuánto pesa Cosmoem en kg?", "correct": "999.9", "options": ["999.9", "500.0", "1000.0"]},
    {"question": "¿Cuál es la descripción de Mew en Pokédex Roja?", "correct": "Esquiva", "options": ["Esquiva", "Nuevo", "Genética"]},
]


class TriviaView(discord.ui.View):
    def __init__(self, correct_answer: str, trivia_id: int, options: list, difficulty: str):
        super().__init__(timeout=60)
        self.correct_answer = correct_answer
        self.trivia_id = trivia_id
        self.options = options
        self.difficulty = difficulty
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
        points = DIFFICULTY_CONFIG[self.difficulty]["points"]

        if is_correct:
            db.update_score(interaction.user.id, points, interaction.user.display_name)
            streak_change = db.update_trivia_stats(interaction.user.id, True, interaction.user.display_name)
            db.mark_trivia_answered(self.trivia_id, interaction.user.id)
            score = db.get_total_score(interaction.user.id)
            streak = db.get_streak(interaction.user.id)

            if streak_change["old_streak"] == 0 and streak_change["new_streak"] > 0:
                role = interaction.guild.get_role(STREAK_ROLE_ID)
                if role:
                    await interaction.user.add_roles(role)

            embed = discord.Embed(
                title=f"✅ ¡Correcto! {DIFFICULTY_CONFIG[self.difficulty]['emoji']}",
                description=f"La respuesta **{self.correct_answer}** es correcta.",
                color=discord.Color.green(),
            )
            embed.add_field(name="Dificultad", value=DIFFICULTY_CONFIG[self.difficulty]["label"])
            embed.add_field(name="Puntos ganados", value=f"+{points}")
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
                title=f"❌ Incorrecto {DIFFICULTY_CONFIG[self.difficulty]['emoji']}",
                description=f"Tu respuesta: **{selected_option}**\nLa correcta: **{self.correct_answer}**",
                color=discord.Color.red(),
            )
            embed.add_field(name="Dificultad", value=DIFFICULTY_CONFIG[self.difficulty]["label"])
            embed.set_footer(text="Solo tú puedes ver esta respuesta")

        await interaction.response.send_message(embed=embed, ephemeral=True)


class WeeklyQuizView(discord.ui.View):
    def __init__(self, questions: list, week_key: str):
        super().__init__(timeout=None)
        self.questions = questions
        self.week_key = week_key
        self.user_responses = {}

    @discord.ui.button(label="✅ Verdadero", style=discord.ButtonStyle.green, custom_id="wq_true")
    async def true_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_answer(interaction, True)

    @discord.ui.button(label="❌ Falso", style=discord.ButtonStyle.red, custom_id="wq_false")
    async def false_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_answer(interaction, False)

    async def process_answer(self, interaction: discord.Interaction, answer: bool):
        uid = interaction.user.id

        if uid not in self.user_responses:
            self.user_responses[uid] = {"answers": [], "current": 0}

        user_data = self.user_responses[uid]
        idx = user_data["current"]

        if idx >= len(self.questions):
            await interaction.response.send_message(
                "Ya has completado el quiz semanal.", ephemeral=True
            )
            return

        user_data["answers"].append(answer)
        user_data["current"] += 1

        if user_data["current"] >= len(self.questions):
            await self.finish_quiz(interaction, uid)
        else:
            q = self.questions[user_data["current"]]
            embed = discord.Embed(
                title=f"📋 Quiz Semanal - Pregunta {user_data['current'] + 1}/{len(self.questions)}",
                description=f"**{q['question']}**",
                color=discord.Color.blue(),
            )
            embed.set_footer(text=f"Respuestas: {user_data['current']}/{len(self.questions)}")
            await interaction.response.edit_message(embed=embed, view=self)

    async def finish_quiz(self, interaction: discord.Interaction, uid: int):
        user_data = self.user_responses[uid]
        correct = 0
        for i, q in enumerate(self.questions):
            if i < len(user_data["answers"]) and user_data["answers"][i] == q["answer"]:
                correct += 1

        if correct == 10:
            points = 50
        elif correct >= 7:
            points = 20
        elif correct >= 5:
            points = 10
        else:
            points = 5

        member = interaction.guild.get_member(uid)
        username = member.display_name if member else "Unknown"
        db.update_score(uid, points, username)
        db.save_weekly_quiz_answer(self.week_key, uid, user_data["answers"], correct, username)

        embed = discord.Embed(
            title="🎉 Quiz Semanal Completado",
            description=f"Has acertado **{correct}/10** preguntas",
            color=discord.Color.green() if correct >= 7 else discord.Color.orange(),
        )
        embed.add_field(name="Puntos ganados", value=f"+{points}")
        embed.add_field(name="Total", value=str(db.get_total_score(uid)))

        result_text = ""
        for i, q in enumerate(self.questions):
            user_ans = user_data["answers"][i] if i < len(user_data["answers"]) else None
            correct_emoji = "✅" if user_ans == q["answer"] else "❌"
            result_text += f"{correct_emoji} {q['question']}\n"
        embed.add_field(name="Resultados", value=result_text, inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)


TRUE_FALSE_QUESTIONS = [
    {"question": "Pikachu es de tipo Eléctrico", "answer": True},
    {"question": "Charizard es de tipo Dragón/Fuego", "answer": False},
    {"question": "Mewtwo es un Pokémon legendario", "answer": True},
    {"question": "Bulbasaur es de tipo Planta/Fuego", "answer": False},
    {"question": "La Pokédex Nacional de Gen 1 tiene 151 Pokémon", "answer": True},
    {"question": "Eevee evoluciona en 8 formas diferentes", "answer": True},
    {"question": "Garchomp es de tipo Dragón/Lucha", "answer": False},
    {"question": "Lucario es de tipo Acero/Lucha", "answer": True},
    {"question": "Rayquaza es un Pokémon legendario de tipo Dragón/Volador", "answer": True},
    {"question": "Gengar es de tipo Fantasma/Veneno", "answer": True},
    {"question": "El Movimiento Hidroariete es de tipo Agua", "answer": True},
    {"question": "Snorlax tiene la mayor defensa base de Gen 1", "answer": False},
    {"question": "Blissey tiene más HP que Chansey", "answer": True},
    {"question": "El Pokémon más alto es Wailord", "answer": True},
    {"question": "Mew es de tipo Psíquico", "answer": True},
    {"question": "Arceus es el Pokémon más fuerte de todos", "answer": False},
    {"question": "Ditto puede transformarse en cualquier Pokémon", "answer": True},
    {"question": "Shedinja tiene solo 1 PS", "answer": True},
    {"question": "El Movimiento Terremote es de tipo Tierra", "answer": True},
    {"question": "Gardevoir es de tipo Psíquico/Hada", "answer": True},
    {"question": "Steelix es más pesado que Onix", "answer": True},
    {"question": "El Movimiento Lanzallamas es de tipo Fuego", "answer": True},
    {"question": "Palkia controla el espacio", "answer": True},
    {"question": "Giratina controla el tiempo", "answer": False},
    {"question": "Darkrai causa pesadillas", "answer": True},
    {"question": "Cresselia es de tipo Psíquico", "answer": True},
    {"question": "El Movimiento Psíquico es de tipo Psíquico", "answer": True},
    {"question": "Scizor es de tipo Bicho/Acero", "answer": True},
    {"question": "Tyranitar es de tipo Roca/Siniestro", "answer": True},
    {"question": "Blaziken es de tipo Fuego/Lucha", "answer": True},
    {"question": "Swampert es de tipo Agua/Tierra", "answer": True},
    {"question": "Sceptile es de tipo Planta", "answer": True},
    {"question": "El Movimiento Hoja Afilada es de tipo Planta", "answer": True},
    {"question": "Metagross es de tipo Psíquico/Acero", "answer": True},
    {"question": "Salamence es de tipo Dragón/Volador", "answer": True},
    {"question": "Alakazam es de tipo Psíquico", "answer": True},
    {"question": "Machamp es de tipo Lucha", "answer": True},
    {"question": "Golem es de tipo Roca/Tierra", "answer": True},
    {"question": "El Movimiento Surf es de tipo Agua", "answer": True},
    {"question": "Dragonite es de tipo Dragón/Volador", "answer": True},
    {"question": "El Movimiento Lanzallamas es de tipo Fuego", "answer": True},
    {"question": "Blastoise es de tipo Agua", "answer": True},
    {"question": "Venusaur es de tipo Planta/Veneno", "answer": True},
    {"question": "Charizard es de tipo Fuego/Volador", "answer": True},
    {"question": "El Movimiento Rayo es de tipo Eléctrico", "answer": True},
    {"question": "El Movimiento Terremote es de tipo Tierra", "answer": True},
    {"question": "El Movimiento Bofetada Lodo es de tipo Veneno", "answer": True},
    {"question": "El Movimiento Aerial Ace es de tipo Volador", "answer": True},
    {"question": "El Movimiento Colmillo Ígneo es de tipo Fuego", "answer": True},
    {"question": "El Movimiento Danza Espada es de tipo Normal", "answer": True},
]


class Trivia(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.weekly_quiz_task.start()

    def cog_unload(self):
        self.weekly_quiz_task.cancel()

    @tasks.loop(hours=24)
    async def weekly_quiz_task(self):
        now = datetime.now()
        if now.weekday() != 0:
            return
        if now.hour != 10 or now.minute != 0:
            return

        guild = self.bot.guilds[0] if self.bot.guilds else None
        if not guild:
            return

        channel = guild.get_channel(TRIVIA_CHANNEL_ID)
        if not channel:
            return

        existing = db.get_active_weekly_quiz()
        if existing:
            return

        from question_gen import get_weekly_questions
        questions = get_weekly_questions(TRUE_FALSE_QUESTIONS, 10)
        week_key = now.strftime("%Y-W%W")
        db.save_weekly_quiz(questions, week_key)

        embed = discord.Embed(
            title="🎯 Quiz Semanal de Pokémon",
            description="¡10 preguntas de Verdadero o Falso! Responde todas para ganar puntos.\n\n"
                       "10/10 = **50 puntos** | 7-9 = **20 puntos** | 5-6 = **10 puntos** | 1-4 = **5 puntos**\n\n"
                       " Usa los botones para responder. ¡Buena suerte!",
            color=discord.Color.gold(),
        )
        embed.set_footer(text="Cada pregunta se envía por separado (ephemeral)")

        view = WeeklyQuizView(questions, week_key)
        await channel.send(embed=embed, view=view)

    @weekly_quiz_task.before_loop
    async def before_weekly_quiz(self):
        await self.bot.wait_until_ready()

    @commands.command(name="trivia")
    async def trivia_command(self, ctx: commands.Context):
        daily = db.get_daily_trivia()
        if daily and daily.get("option1"):
            options = [daily["option1"], daily["option2"], daily["option3"]]
            difficulty = "medium"
            view = TriviaView(daily["correct_answer"], daily["id"], options, difficulty)
            embed = discord.Embed(
                title="🎮 Trivia Pokémon del Día",
                description=daily["question"],
                color=discord.Color.blue(),
            )
            embed.add_field(name="A", value=options[0], inline=False)
            embed.add_field(name="B", value=options[1], inline=False)
            embed.add_field(name="C", value=options[2], inline=False)
            embed.set_footer(text="Haz click en una opción para responder.")
            await ctx.send(embed=embed, view=view)
            return

        from question_gen import get_trivia_question

        difficulty = random.choice(["easy", "medium", "hard"])
        pool = {"easy": TRIVIA_EASY, "medium": TRIVIA_MEDIUM, "hard": TRIVIA_HARD}
        trivia = get_trivia_question(difficulty, pool[difficulty])
        options = trivia["options"][:]
        random.shuffle(options)

        db.save_trivia_question(trivia["question"], trivia["correct"], options)

        diff_config = DIFFICULTY_CONFIG[difficulty]
        embed = discord.Embed(
            title=f"🎮 Trivia Pokémon del Día {diff_config['emoji']}",
            description=trivia["question"],
            color=diff_config["color"],
        )
        embed.add_field(name="Dificultad", value=diff_config["label"])
        embed.add_field(name="Puntos", value=str(diff_config["points"]))
        embed.add_field(name="A", value=options[0], inline=False)
        embed.add_field(name="B", value=options[1], inline=False)
        embed.add_field(name="C", value=options[2], inline=False)
        embed.set_footer(text="Tienes 60 segundos para responder.")

        daily = db.get_daily_trivia()
        view = TriviaView(trivia["correct"], daily["id"], options, difficulty)
        await ctx.send(embed=embed, view=view)

    @app_commands.command(name="trivia", description="Juega la trivia Pokémon del día")
    async def trivia_slash(self, interaction: discord.Interaction):
        daily = db.get_daily_trivia()
        if daily and daily.get("option1"):
            options = [daily["option1"], daily["option2"], daily["option3"]]
            difficulty = "medium"
            view = TriviaView(daily["correct_answer"], daily["id"], options, difficulty)
            embed = discord.Embed(
                title="🎮 Trivia Pokémon del Día",
                description=daily["question"],
                color=discord.Color.blue(),
            )
            embed.add_field(name="A", value=options[0], inline=False)
            embed.add_field(name="B", value=options[1], inline=False)
            embed.add_field(name="C", value=options[2], inline=False)
            embed.set_footer(text="Haz click en una opción para responder.")
            await interaction.response.send_message(embed=embed, view=view)
            return

        from question_gen import get_trivia_question

        difficulty = random.choice(["easy", "medium", "hard"])
        pool = {"easy": TRIVIA_EASY, "medium": TRIVIA_MEDIUM, "hard": TRIVIA_HARD}
        trivia = get_trivia_question(difficulty, pool[difficulty])
        options = trivia["options"][:]
        random.shuffle(options)

        db.save_trivia_question(trivia["question"], trivia["correct"], options)

        diff_config = DIFFICULTY_CONFIG[difficulty]
        embed = discord.Embed(
            title=f"🎮 Trivia Pokémon del Día {diff_config['emoji']}",
            description=trivia["question"],
            color=diff_config["color"],
        )
        embed.add_field(name="Dificultad", value=diff_config["label"])
        embed.add_field(name="Puntos", value=str(diff_config["points"]))
        embed.add_field(name="A", value=options[0], inline=False)
        embed.add_field(name="B", value=options[1], inline=False)
        embed.add_field(name="C", value=options[2], inline=False)
        embed.set_footer(text="Tienes 60 segundos para responder.")

        daily = db.get_daily_trivia()
        view = TriviaView(trivia["correct"], daily["id"], options, difficulty)
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
