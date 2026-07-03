import random
import json
import os
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

POKEMON_IDS = list(range(1, 650))

_name_cache = {}
_fallback_pool = []


def _load_fallback_pool() -> list:
    global _fallback_pool
    if _fallback_pool:
        return _fallback_pool
    try:
        path = os.path.join(os.path.dirname(__file__), "fallback_trivia.json")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            _fallback_pool = data.get("trivia", [])
            log.info(f"Loaded {len(_fallback_pool)} fallback questions")
            return _fallback_pool
    except Exception as e:
        log.error(f"Error loading fallback bank: {e}")
        return []


def _get_pokemon(pokemon_id: int) -> dict | None:
    try:
        resp = requests.get(f"{POKEAPI_BASE}/pokemon/{pokemon_id}", timeout=10)
        if resp.status_code == 200:
            return resp.json()
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
    question = f"De que tipo es {name}?"

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

    question = f"Cuál es el stat base de {stat_label} de {name}?"

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

    question = f"Cuanto pesa {name} en kg?"

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

    question = f"Cuanto mide {name} en metros?"

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


def generate_daily_trivia() -> dict:
    generators = [
        _generate_type_question,
        _generate_stat_question,
        _generate_weight_question,
        _generate_height_question,
    ]

    random.shuffle(generators)

    for gen_func in generators:
        for _ in range(5):
            try:
                question = gen_func()
                if question:
                    log.info(f"Generated trivia: {question['question']}")
                    return question
            except Exception as e:
                log.error(f"Error generating question: {e}")
                continue

    # Fallback to verified local bank
    pool = _load_fallback_pool()
    if pool:
        question = random.choice(pool)
        log.info(f"Using fallback question: {question['question']}")
        return question

    return {
        "question": "De que tipo es Pikachu?",
        "correct": "Eléctrico",
        "options": ["Eléctrico", "Fuego", "Agua"],
    }
