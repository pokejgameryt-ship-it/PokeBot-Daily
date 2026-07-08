import random
import requests
import logging

log = logging.getLogger("pokeapi_trivia")

POKEAPI_BASE = "https://pokeapi.co/api/v2"

TYPE_NAMES_ES = {
    "normal": "Normal", "fire": "Fuego", "water": "Agua", "electric": "Eléctrico",
    "grass": "Planta", "ice": "Hielo", "fighting": "Lucha", "poison": "Veneno",
    "ground": "Tierra", "flying": "Volador", "psychic": "Psíquico", "bug": "Bicho",
    "rock": "Roca", "ghost": "Fantasma", "dragon": "Dragón", "dark": "Siniestro",
    "steel": "Acero", "fairy": "Hada",
}

CATEGORY_NAMES_ES = {
    "seed": "Semilla", "lizard": "Lagartija", "flame": "Llama", "turtle": "Tortuga",
    "pokemon": "Pokémon", "mouse": "Ratón", "bird": "Pájaro", "snake": "Serpiente",
    "dragon": "Dragón", "fish": "Pez", "fox": "Zorro", "cat": "Gato",
    "dog": "Perlo", "bear": "Oso", "insect": "Insecto", "crab": "Cangrejo",
    "bat": "Murciélago", "ghost": "Fantasma", "skull": "Cráneo", "bone": "Hueso",
    "light": "Luz", "shadow": "Sombra", "aura": "Aura", "mystic": "Místico",
    "steel": "Acero", "iron": "Hierro", "gem": "Gema", "fossil": "Fósil",
    "plant": "Planta", "flower": "Flor", "leaf": "Hoja", "tree": "Árbol",
    "water": "Agua", "sea": "Mar", "ocean": "Océano", "bubble": "Burbuja",
    "electric": "Eléctrico", "thunder": "Trueno", "spark": "Chispa",
    "fire": "Fuego", "burn": "Quemadura", "eruption": "Erupción",
    "ice": "Hielo", "frost": "Escarcha", "snow": "Nieve",
    "rock": "Roca", "stone": "Piedra", "boulder": "Rocalla",
    "ground": "Tierra", "mud": "Lodo", "sand": "Arena",
    "poison": "Veneno", "gas": "Gas", "noxious": "Nocivo",
    "psychic": "Psíquico", "brain": "Cerebro", "emotion": "Emoción",
    "fighting": "Lucha", "combat": "Combate", "martial": "Marcial",
    "dark": "Siniestro", "bad": "Malvado", "evil": "Maligno",
    "fairy": "Hada", "pixie": "Duende", "wing": "Ala",
}

POKEMON_IDS = list(range(1, 650))

_name_cache = {}
_pokemon_cache = {}


def _get_pokemon(pokemon_id: int) -> dict | None:
    if pokemon_id in _pokemon_cache:
        return _pokemon_cache[pokemon_id]
    try:
        resp = requests.get(f"{POKEAPI_BASE}/pokemon/{pokemon_id}", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            _pokemon_cache[pokemon_id] = data
            return data
    except Exception as e:
        log.error(f"Error fetching pokemon {pokemon_id}: {e}")
    return None


def _get_species(pokemon_id: int) -> dict | None:
    try:
        resp = requests.get(f"{POKEAPI_BASE}/pokemon-species/{pokemon_id}", timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        log.error(f"Error fetching species {pokemon_id}: {e}")
    return None


def _get_spanish_name(pokemon_id: int) -> str:
    if pokemon_id in _name_cache:
        return _name_cache[pokemon_id]

    species = _get_species(pokemon_id)
    if not species:
        pokemon = _get_pokemon(pokemon_id)
        if pokemon:
            return pokemon["name"].capitalize()
        return f"Pokemon-{pokemon_id}"

    for entry in species.get("names", []):
        if entry.get("language", {}).get("name") == "es":
            name = entry["name"]
            _name_cache[pokemon_id] = name
            return name

    for entry in species.get("names", []):
        if entry.get("language", {}).get("name") == "en":
            name = entry["name"]
            _name_cache[pokemon_id] = name
            return name

    return species.get("name", f"Pokemon-{pokemon_id}").capitalize()


def _get_stat_name(stat_name: str) -> str:
    stat_names = {
        "hp": "HP", "attack": "Ataque", "defense": "Defensa",
        "special-attack": "At. Esp.", "special-defense": "Def. Esp.", "speed": "Velocidad"
    }
    return stat_names.get(stat_name, stat_name)


def _generate_type_question() -> dict | None:
    pokemon_id = random.choice(POKEMON_IDS)
    pokemon = _get_pokemon(pokemon_id)
    if not pokemon:
        return None

    name = _get_spanish_name(pokemon_id)
    types = [TYPE_NAMES_ES.get(t["type"]["name"], t["type"]["name"].capitalize()) for t in pokemon["types"]]

    correct = "/".join(types)
    question = f"¿De qué tipo es {name}?"

    all_types = list(TYPE_NAMES_ES.values())
    wrong_types = [t for t in all_types if t not in types]
    if len(wrong_types) < 2:
        return None
    wrong_options = random.sample(wrong_types, 2)

    options = [correct] + wrong_options
    random.shuffle(options)

    return {"question": question, "correct": correct, "options": options}


def _generate_stat_question() -> dict | None:
    pokemon_id = random.choice(POKEMON_IDS)
    pokemon = _get_pokemon(pokemon_id)
    if not pokemon:
        return None

    name = _get_spanish_name(pokemon_id)
    stats = {s["stat"]["name"]: s["base_stat"] for s in pokemon["stats"]}

    stat_name = random.choice(list(stats.keys()))
    correct_value = stats[stat_name]
    stat_label = _get_stat_name(stat_name)

    question = f"¿Cuál es el stat base de {stat_label} de {name}?"

    wrong_values = []
    offsets = [-25, -15, -10, 10, 15, 25]
    random.shuffle(offsets)
    for offset in offsets:
        wrong = correct_value + offset
        wrong = max(1, wrong)
        if str(wrong) != str(correct_value) and str(wrong) not in wrong_values:
            wrong_values.append(str(wrong))
        if len(wrong_values) >= 2:
            break

    if len(wrong_values) < 2:
        return None

    options = [str(correct_value)] + wrong_values[:2]
    random.shuffle(options)

    return {"question": question, "correct": str(correct_value), "options": options}


def _generate_weight_question() -> dict | None:
    pokemon_id = random.choice(POKEMON_IDS)
    pokemon = _get_pokemon(pokemon_id)
    if not pokemon:
        return None

    name = _get_spanish_name(pokemon_id)
    weight_kg = pokemon["weight"] / 10

    if weight_kg < 1:
        return None

    question = f"¿Cuánto pesa {name} en kg?"

    wrong_weights = []
    pct = weight_kg * 0.3
    offsets = [-pct * 1.5, -pct, -pct * 0.5, pct * 0.5, pct, pct * 1.5]
    random.shuffle(offsets)
    for offset in offsets:
        wrong = weight_kg + offset
        wrong = max(1.0, round(wrong, 1))
        wrong_str = f"{wrong:.1f}"
        if wrong_str != f"{weight_kg:.1f}" and wrong_str not in wrong_weights:
            wrong_weights.append(wrong_str)
        if len(wrong_weights) >= 2:
            break

    if len(wrong_weights) < 2:
        return None

    options = [f"{weight_kg:.1f}"] + wrong_weights[:2]
    random.shuffle(options)

    return {"question": question, "correct": f"{weight_kg:.1f}", "options": options}


def _generate_height_question() -> dict | None:
    pokemon_id = random.choice(POKEMON_IDS)
    pokemon = _get_pokemon(pokemon_id)
    if not pokemon:
        return None

    name = _get_spanish_name(pokemon_id)
    height_m = pokemon["height"] / 10

    if height_m < 0.3:
        return None

    question = f"¿Cuánto mide {name} en metros?"

    wrong_heights = []
    pct = height_m * 0.3
    offsets = [-pct * 1.5, -pct, -pct * 0.5, pct * 0.5, pct, pct * 1.5]
    random.shuffle(offsets)
    for offset in offsets:
        wrong = height_m + offset
        wrong = max(0.3, round(wrong, 1))
        wrong_str = f"{wrong:.1f}"
        if wrong_str != f"{height_m:.1f}" and wrong_str not in wrong_heights:
            wrong_heights.append(wrong_str)
        if len(wrong_heights) >= 2:
            break

    if len(wrong_heights) < 2:
        return None

    options = [f"{height_m:.1f}"] + wrong_heights[:2]
    random.shuffle(options)

    return {"question": question, "correct": f"{height_m:.1f}", "options": options}


def _generate_category_question() -> dict | None:
    pokemon_id = random.choice(POKEMON_IDS)
    species = _get_species(pokemon_id)
    if not species:
        return None

    name = _get_spanish_name(pokemon_id)

    category_en = None
    for entry in species.get("genera", []):
        if entry.get("language", {}).get("name") == "en":
            category_en = entry["genus"]
            break

    if not category_en:
        return None

    category_es = None
    for entry in species.get("genera", []):
        if entry.get("language", {}).get("name") == "es":
            category_es = entry["genus"]
            break

    if not category_es:
        category_es = category_en

    question = f"¿Qué categoría tiene {name}?"

    wrong_categories = [
        "Pokémon Semilla", "Pokémon Lagartija", "Pokémon Llama",
        "Pokémon Tortuga", "Pokémon Ratón", "Pokémon Dragón",
        "Pokémon Pez", "Pokémon Zorro", "Pokémon Gato",
        "Pokémon Oso", "Pokémon Insecto", "Pokémon Hada",
    ]
    wrong_categories = [c for c in wrong_categories if c != category_es]
    if len(wrong_categories) < 2:
        return None
    wrong_options = random.sample(wrong_categories, 2)

    options = [category_es] + wrong_options
    random.shuffle(options)

    return {"question": question, "correct": category_es, "options": options}


def _generate_comparison_question() -> dict | None:
    id1, id2 = random.sample(POKEMON_IDS, 2)
    p1 = _get_pokemon(id1)
    p2 = _get_pokemon(id2)
    if not p1 or not p2:
        return None

    name1 = _get_spanish_name(id1)
    name2 = _get_spanish_name(id2)

    stat = random.choice(["weight", "height", "hp", "attack", "defense", "speed"])

    if stat == "weight":
        val1 = p1["weight"] / 10
        val2 = p2["weight"] / 10
        unit = "kg"
        attr = "pesa"
    elif stat == "height":
        val1 = p1["height"] / 10
        val2 = p2["height"] / 10
        unit = "m"
        attr = "mide"
    else:
        stats1 = {s["stat"]["name"]: s["base_stat"] for s in p1["stats"]}
        stats2 = {s["stat"]["name"]: s["base_stat"] for s in p2["stats"]}
        val1 = stats1.get(stat, 0)
        val2 = stats2.get(stat, 0)
        unit = ""
        attr = f"tiene de {_get_stat_name(stat)}"

    if val1 == val2:
        return None

    if val1 > val2:
        correct = name1
        wrong = name2
    else:
        correct = name2
        wrong = name1

    if unit:
        question = f"¿Quién {attr} más, {name1} o {name2}?"
    else:
        question = f"¿Quién {attr} más, {name1} o {name2}?"

    options = [correct, wrong, "Son iguales"]
    random.shuffle(options)

    return {"question": question, "correct": correct, "options": options}


def generate_daily_trivia() -> dict:
    generators = [
        _generate_type_question,
        _generate_stat_question,
        _generate_weight_question,
        _generate_height_question,
        _generate_category_question,
        _generate_comparison_question,
    ]

    random.shuffle(generators)

    for gen_func in generators:
        for _ in range(10):
            try:
                question = gen_func()
                if question:
                    log.info(f"Generated trivia: {question['question']}")
                    return question
            except Exception as e:
                log.error(f"Error generating question: {e}")
                continue

    return {
        "question": "¿De qué tipo es Pikachu?",
        "correct": "Eléctrico",
        "options": ["Eléctrico", "Fuego", "Agua"],
    }
