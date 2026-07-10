import random
import logging
import os

log = logging.getLogger("essentials_trivia")

DATA_DIR = os.path.dirname(os.path.abspath(__file__))

_types_data = {}
_pokemon_data = {}
_moves_data = {}
_abilities_data = {}
_items_data = {}

_loaded = False


def _parse_types():
    global _types_data
    filepath = os.path.join(DATA_DIR, "types.txt")
    current_type = None
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("[") and line.endswith("]"):
                current_type = line[1:-1]
                _types_data[current_type] = {"weaknesses": [], "resistances": [], "immunities": []}
            elif line.startswith("Weaknesses =") and current_type:
                _types_data[current_type]["weaknesses"] = [t.strip() for t in line.split("=", 1)[1].split(",") if t.strip()]
            elif line.startswith("Resistances =") and current_type:
                _types_data[current_type]["resistances"] = [t.strip() for t in line.split("=", 1)[1].split(",") if t.strip()]
            elif line.startswith("Immunities =") and current_type:
                _types_data[current_type]["immunities"] = [t.strip() for t in line.split("=", 1)[1].split(",") if t.strip()]
    log.info(f"Loaded {len(_types_data)} types")


def _parse_pokemon():
    global _pokemon_data
    filepath = os.path.join(DATA_DIR, "pokemon.txt")
    current_id = None
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("[") and line.endswith("]"):
                current_id = line[1:-1]
                _pokemon_data[current_id] = {}
            elif current_id and "=" in line:
                key, _, val = line.partition("=")
                key = key.strip()
                val = val.strip()
                if key == "Name":
                    _pokemon_data[current_id]["name"] = val
                elif key == "Types":
                    _pokemon_data[current_id]["types"] = [t.strip() for t in val.split(",")]
                elif key == "BaseStats":
                    stats = [int(s.strip()) for s in val.split(",")]
                    if len(stats) >= 6:
                        _pokemon_data[current_id]["stats"] = {
                            "hp": stats[0], "attack": stats[1], "defense": stats[2],
                            "sp_attack": stats[3], "sp_defense": stats[4], "speed": stats[5]
                        }
                elif key == "Abilities":
                    _pokemon_data[current_id]["abilities"] = [a.strip() for a in val.split(",")]
                elif key == "HiddenAbilities":
                    _pokemon_data[current_id]["hidden_ability"] = val
                elif key == "Moves":
                    moves = []
                    parts = val.split(",")
                    i = 0
                    while i < len(parts) - 1:
                        try:
                            level = int(parts[i].strip())
                            move_name = parts[i + 1].strip()
                            moves.append({"level": level, "name": move_name})
                        except (ValueError, IndexError):
                            pass
                        i += 2
                    _pokemon_data[current_id]["moves"] = moves
                elif key == "Height":
                    _pokemon_data[current_id]["height"] = val
                elif key == "Weight":
                    _pokemon_data[current_id]["weight"] = val
                elif key == "Category":
                    _pokemon_data[current_id]["category"] = val
                elif key == "Evolutions":
                    _pokemon_data[current_id]["evolutions"] = val
                elif key == "CatchRate":
                    _pokemon_data[current_id]["catch_rate"] = val
                elif key == "BaseExp":
                    _pokemon_data[current_id]["base_exp"] = val
                elif key == "EVs":
                    _pokemon_data[current_id]["evs"] = val
                elif key == "EggGroups":
                    _pokemon_data[current_id]["egg_groups"] = val
                elif key == "HatchSteps":
                    _pokemon_data[current_id]["hatch_steps"] = val
                elif key == "Color":
                    _pokemon_data[current_id]["color"] = val
                elif key == "Shape":
                    _pokemon_data[current_id]["shape"] = val
                elif key == "Generation":
                    _pokemon_data[current_id]["generation"] = val
    log.info(f"Loaded {len(_pokemon_data)} pokemon")


def _parse_moves():
    global _moves_data
    filepath = os.path.join(DATA_DIR, "moves.txt")
    current_move = None
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("[") and line.endswith("]"):
                current_move = line[1:-1]
                _moves_data[current_move] = {}
            elif current_move and "=" in line:
                key, _, val = line.partition("=")
                key = key.strip()
                val = val.strip()
                if key == "Name":
                    _moves_data[current_move]["name"] = val
                elif key == "Type":
                    _moves_data[current_move]["type"] = val
                elif key == "Category":
                    _moves_data[current_move]["category"] = val
                elif key == "Power":
                    _moves_data[current_move]["power"] = val
                elif key == "Accuracy":
                    _moves_data[current_move]["accuracy"] = val
                elif key == "TotalPP":
                    _moves_data[current_move]["pp"] = val
                elif key == "Description":
                    _moves_data[current_move]["description"] = val
    log.info(f"Loaded {len(_moves_data)} moves")


def _parse_abilities():
    global _abilities_data
    filepath = os.path.join(DATA_DIR, "abilities.txt")
    current_ability = None
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("[") and line.endswith("]"):
                current_ability = line[1:-1]
                _abilities_data[current_ability] = {}
            elif current_ability and "=" in line:
                key, _, val = line.partition("=")
                key = key.strip()
                val = val.strip()
                if key == "Name":
                    _abilities_data[current_ability]["name"] = val
                elif key == "Description":
                    _abilities_data[current_ability]["description"] = val
    log.info(f"Loaded {len(_abilities_data)} abilities")


def _parse_items():
    global _items_data
    filepath = os.path.join(DATA_DIR, "items.txt")
    current_item = None
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("[") and line.endswith("]"):
                current_item = line[1:-1]
                _items_data[current_item] = {}
            elif current_item and "=" in line:
                key, _, val = line.partition("=")
                key = key.strip()
                val = val.strip()
                if key == "Name":
                    _items_data[current_item]["name"] = val
                elif key == "Description":
                    _items_data[current_item]["description"] = val
                elif key == "Price":
                    _items_data[current_item]["price"] = val
    log.info(f"Loaded {len(_items_data)} items")


def load_all():
    global _loaded
    if _loaded:
        return
    _parse_types()
    _parse_pokemon()
    _parse_moves()
    _parse_abilities()
    _parse_items()
    _loaded = True
    log.info("All Essentials data loaded")


def _generate_type_weakness_question():
    if not _types_data:
        return None
    valid_types = [t for t in _types_data if _types_data[t].get("weaknesses") and t != "QMARKS"]
    if not valid_types:
        return None
    target_type = random.choice(valid_types)
    weaknesses = _types_data[target_type]["weaknesses"]
    correct = weaknesses[0]
    question = f"¿Qué tipo es débil contra el tipo {target_type}?"
    all_types = [t for t in _types_data if t != "QMARKS" and t != target_type]
    wrong_options = random.sample([t for t in all_types if t not in weaknesses], min(2, len(all_types)))
    options = [correct] + wrong_options
    random.shuffle(options)
    return {"question": question, "correct": correct, "options": options}


def _generate_type_resistance_question():
    if not _types_data:
        return None
    valid_types = [t for t in _types_data if _types_data[t].get("resistances") and t != "QMARKS"]
    if not valid_types:
        return None
    target_type = random.choice(valid_types)
    resistances = _types_data[target_type]["resistances"]
    correct = resistances[0]
    question = f"¿Qué tipo resiste al tipo {target_type}?"
    all_types = [t for t in _types_data if t != "QMARKS" and t != target_type]
    wrong_options = random.sample([t for t in all_types if t not in resistances], min(2, len(all_types)))
    options = [correct] + wrong_options
    random.shuffle(options)
    return {"question": question, "correct": correct, "options": options}


def _generate_type_immunity_question():
    if not _types_data:
        return None
    valid_types = [t for t in _types_data if _types_data[t].get("immunities") and t != "QMARKS"]
    if not valid_types:
        return None
    target_type = random.choice(valid_types)
    immunities = _types_data[target_type]["immunities"]
    correct = immunities[0]
    question = f"¿Qué tipo es inmune al tipo {target_type}?"
    all_types = [t for t in _types_data if t != "QMARKS" and t != target_type]
    wrong_options = random.sample([t for t in all_types if t not in immunities], min(2, len(all_types)))
    options = [correct] + wrong_options
    random.shuffle(options)
    return {"question": question, "correct": correct, "options": options}


def _generate_pokemon_type_question():
    if not _pokemon_data:
        return None
    pokemon_id = random.choice(list(_pokemon_data.keys()))
    pokemon = _pokemon_data[pokemon_id]
    if "types" not in pokemon:
        return None
    correct = "/".join(pokemon["types"])
    question = f"¿De qué tipo es el Pokémon {pokemon_id}?"
    all_types = list(_types_data.keys())
    wrong_types = [t for t in all_types if t not in pokemon["types"] and t != "QMARKS"]
    wrong_options = random.sample(wrong_types, min(2, len(wrong_types)))
    options = [correct] + wrong_options
    random.shuffle(options)
    return {"question": question, "correct": correct, "options": options}


def _generate_pokemon_stat_question():
    if not _pokemon_data:
        return None
    valid_pokemon = [p for p in _pokemon_data if "stats" in _pokemon_data[p]]
    if not valid_pokemon:
        return None
    pokemon_id = random.choice(valid_pokemon)
    pokemon = _pokemon_data[pokemon_id]
    stat_names = {"hp": "HP", "attack": "Ataque", "defense": "Defensa",
                  "sp_attack": "At. Esp.", "sp_defense": "Def. Esp.", "speed": "Velocidad"}
    stat_key = random.choice(list(stat_names.keys()))
    correct_value = pokemon["stats"][stat_key]
    stat_label = stat_names[stat_key]
    question = f"¿Cuál es el stat base de {stat_label} de {pokemon_id}?"
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


def _generate_pokemon_weight_question():
    if not _pokemon_data:
        return None
    valid_pokemon = [p for p in _pokemon_data if "weight" in _pokemon_data[p]]
    if not valid_pokemon:
        return None
    pokemon_id = random.choice(valid_pokemon)
    pokemon = _pokemon_data[pokemon_id]
    weight = pokemon["weight"]
    question = f"¿Cuánto pesa {pokemon_id} en kg?"
    wrong_weights = []
    try:
        weight_val = float(weight)
    except ValueError:
        return None
    pct = weight_val * 0.3
    offsets = [-pct * 1.5, -pct, -pct * 0.5, pct * 0.5, pct, pct * 1.5]
    random.shuffle(offsets)
    for offset in offsets:
        wrong = weight_val + offset
        wrong = max(0.1, round(wrong, 1))
        wrong_str = f"{wrong:.1f}"
        if wrong_str != f"{weight_val:.1f}" and wrong_str not in wrong_weights:
            wrong_weights.append(wrong_str)
        if len(wrong_weights) >= 2:
            break
    if len(wrong_weights) < 2:
        return None
    options = [f"{weight_val:.1f}"] + wrong_weights[:2]
    random.shuffle(options)
    return {"question": question, "correct": f"{weight_val:.1f}", "options": options}


def _generate_pokemon_height_question():
    if not _pokemon_data:
        return None
    valid_pokemon = [p for p in _pokemon_data if "height" in _pokemon_data[p]]
    if not valid_pokemon:
        return None
    pokemon_id = random.choice(valid_pokemon)
    pokemon = _pokemon_data[pokemon_id]
    height = pokemon["height"]
    question = f"¿Cuánto mide {pokemon_id} en metros?"
    wrong_heights = []
    try:
        height_val = float(height)
    except ValueError:
        return None
    if height_val < 0.3:
        return None
    pct = height_val * 0.3
    offsets = [-pct * 1.5, -pct, -pct * 0.5, pct * 0.5, pct, pct * 1.5]
    random.shuffle(offsets)
    for offset in offsets:
        wrong = height_val + offset
        wrong = max(0.3, round(wrong, 1))
        wrong_str = f"{wrong:.1f}"
        if wrong_str != f"{height_val:.1f}" and wrong_str not in wrong_heights:
            wrong_heights.append(wrong_str)
        if len(wrong_heights) >= 2:
            break
    if len(wrong_heights) < 2:
        return None
    options = [f"{height_val:.1f}"] + wrong_heights[:2]
    random.shuffle(options)
    return {"question": question, "correct": f"{height_val:.1f}", "options": options}


def _generate_pokemon_category_question():
    if not _pokemon_data:
        return None
    valid_pokemon = [p for p in _pokemon_data if "category" in _pokemon_data[p]]
    if not valid_pokemon:
        return None
    pokemon_id = random.choice(valid_pokemon)
    pokemon = _pokemon_data[pokemon_id]
    correct = pokemon["category"]
    question = f"¿Qué categoría tiene el Pokémon {pokemon_id}?"
    all_categories = list(set(_pokemon_data[p]["category"] for p in _pokemon_data if "category" in _pokemon_data[p]))
    wrong_categories = [c for c in all_categories if c != correct]
    if len(wrong_categories) < 2:
        return None
    wrong_options = random.sample(wrong_categories, 2)
    options = [correct] + wrong_options
    random.shuffle(options)
    return {"question": question, "correct": correct, "options": options}


def _generate_pokemon_evolution_question():
    if not _pokemon_data:
        return None
    valid_pokemon = [p for p in _pokemon_data if "evolutions" in _pokemon_data[p]]
    if not valid_pokemon:
        return None
    pokemon_id = random.choice(valid_pokemon)
    pokemon = _pokemon_data[pokemon_id]
    evo_data = pokemon["evolutions"]
    parts = evo_data.split(",")
    if len(parts) < 3:
        return None
    evo_to = parts[0].strip()
    evo_method = parts[1].strip()
    evo_level = parts[2].strip()
    if evo_method != "Level":
        return None
    question = f"¿En qué nivel evoluciona {pokemon_id} hacia {evo_to}?"
    correct = evo_level
    wrong_levels = []
    try:
        level_val = int(evo_level)
    except ValueError:
        return None
    for offset in [-5, -3, -2, 2, 3, 5]:
        wrong = level_val + offset
        if 1 <= wrong <= 100 and str(wrong) != correct and str(wrong) not in wrong_levels:
            wrong_levels.append(str(wrong))
        if len(wrong_levels) >= 2:
            break
    if len(wrong_levels) < 2:
        return None
    options = [correct] + wrong_levels[:2]
    random.shuffle(options)
    return {"question": question, "correct": correct, "options": options}


def _generate_pokemon_ability_question():
    if not _pokemon_data:
        return None
    valid_pokemon = [p for p in _pokemon_data if "abilities" in _pokemon_data[p] and _pokemon_data[p]["abilities"]]
    if not valid_pokemon:
        return None
    pokemon_id = random.choice(valid_pokemon)
    pokemon = _pokemon_data[pokemon_id]
    abilities = pokemon["abilities"]
    correct = abilities[0]
    question = f"¿Cuál es la habilidad principal de {pokemon_id}?"
    all_abilities = list(_abilities_data.keys())
    wrong_abilities = [a for a in all_abilities if a not in abilities]
    if len(wrong_abilities) < 2:
        return None
    wrong_options = random.sample(wrong_abilities, 2)
    options = [correct] + wrong_options
    random.shuffle(options)
    return {"question": question, "correct": correct, "options": options}


def _generate_move_type_question():
    if not _moves_data:
        return None
    valid_moves = [m for m in _moves_data if "type" in _moves_data[m]]
    if not valid_moves:
        return None
    move_id = random.choice(valid_moves)
    move = _moves_data[move_id]
    correct = move["type"]
    question = f"¿De qué tipo es el movimiento {move_id}?"
    all_types = list(_types_data.keys())
    wrong_types = [t for t in all_types if t != correct and t != "QMARKS"]
    wrong_options = random.sample(wrong_types, min(2, len(wrong_types)))
    options = [correct] + wrong_options
    random.shuffle(options)
    return {"question": question, "correct": correct, "options": options}


def _generate_move_category_question():
    if not _moves_data:
        return None
    valid_moves = [m for m in _moves_data if "category" in _moves_data[m]]
    if not valid_moves:
        return None
    move_id = random.choice(valid_moves)
    move = _moves_data[move_id]
    correct = move["category"]
    question = f"¿Qué categoría de movimiento es {move_id}?"
    categories = ["Physical", "Special", "Status"]
    wrong_categories = [c for c in categories if c != correct]
    if len(wrong_categories) < 2:
        return None
    wrong_options = random.sample(wrong_categories, 2)
    options = [correct] + wrong_options
    random.shuffle(options)
    return {"question": question, "correct": correct, "options": options}


def _generate_move_power_question():
    if not _moves_data:
        return None
    valid_moves = [m for m in _moves_data if "power" in _moves_data[m] and _moves_data[m]["power"] not in ("", "0")]
    if not valid_moves:
        return None
    move_id = random.choice(valid_moves)
    move = _moves_data[move_id]
    correct = move["power"]
    question = f"¿Cuánto daño base hace el movimiento {move_id}?"
    try:
        power_val = int(correct)
    except ValueError:
        return None
    wrong_powers = []
    offsets = [-40, -30, -20, -10, 10, 20, 30, 40]
    random.shuffle(offsets)
    for offset in offsets:
        wrong = power_val + offset
        if wrong > 0 and str(wrong) != correct and str(wrong) not in wrong_powers:
            wrong_powers.append(str(wrong))
        if len(wrong_powers) >= 2:
            break
    if len(wrong_powers) < 2:
        return None
    options = [correct] + wrong_powers[:2]
    random.shuffle(options)
    return {"question": question, "correct": correct, "options": options}


def _generate_move_accuracy_question():
    if not _moves_data:
        return None
    valid_moves = [m for m in _moves_data if "accuracy" in _moves_data[m] and _moves_data[m]["accuracy"] not in ("", "0")]
    if not valid_moves:
        return None
    move_id = random.choice(valid_moves)
    move = _moves_data[move_id]
    correct = move["accuracy"]
    question = f"¿Cuál es la precisión del movimiento {move_id}?"
    try:
        acc_val = int(correct)
    except ValueError:
        return None
    wrong_accs = []
    offsets = [-30, -20, -10, 10, 20, 30]
    random.shuffle(offsets)
    for offset in offsets:
        wrong = acc_val + offset
        if 1 <= wrong <= 100 and str(wrong) != correct and str(wrong) not in wrong_accs:
            wrong_accs.append(str(wrong))
        if len(wrong_accs) >= 2:
            break
    if len(wrong_accs) < 2:
        return None
    options = [correct] + wrong_accs[:2]
    random.shuffle(options)
    return {"question": question, "correct": correct, "options": options}


def _generate_ability_description_question():
    if not _abilities_data:
        return None
    valid_abilities = [a for a in _abilities_data if "description" in _abilities_data[a]]
    if not valid_abilities:
        return None
    ability_id = random.choice(valid_abilities)
    ability = _abilities_data[ability_id]
    correct = ability["name"]
    question = f"¿Qué hace la habilidad {ability_id}?"
    all_abilities = [a for a in valid_abilities if a != ability_id]
    if len(all_abilities) < 2:
        return None
    wrong_ids = random.sample(all_abilities, 2)
    wrong_options = [_abilities_data[a]["name"] for a in wrong_ids]
    options = [correct] + wrong_options
    random.shuffle(options)
    return {"question": question, "correct": correct, "options": options}


def _generate_pokemon_moves_at_level():
    if not _pokemon_data:
        return None
    valid_pokemon = [p for p in _pokemon_data if "moves" in _pokemon_data[p] and _pokemon_data[p]["moves"]]
    if not valid_pokemon:
        return None
    pokemon_id = random.choice(valid_pokemon)
    pokemon = _pokemon_data[pokemon_id]
    moves = pokemon["moves"]
    if len(moves) < 4:
        return None
    random.shuffle(moves)
    move = moves[0]
    correct = str(move["level"])
    question = f"¿En qué nivel {pokemon_id} aprende {move['name']}?"
    wrong_levels = []
    for offset in [-3, -2, -1, 1, 2, 3]:
        wrong = move["level"] + offset
        if 1 <= wrong <= 100 and str(wrong) != correct and str(wrong) not in wrong_levels:
            wrong_levels.append(str(wrong))
        if len(wrong_levels) >= 2:
            break
    if len(wrong_levels) < 2:
        return None
    options = [correct] + wrong_levels[:2]
    random.shuffle(options)
    return {"question": question, "correct": correct, "options": options}


def _generate_pokemon_color_question():
    if not _pokemon_data:
        return None
    valid_pokemon = [p for p in _pokemon_data if "color" in _pokemon_data[p]]
    if not valid_pokemon:
        return None
    pokemon_id = random.choice(valid_pokemon)
    pokemon = _pokemon_data[pokemon_id]
    correct = pokemon["color"]
    question = f"¿De qué color es {pokemon_id}?"
    all_colors = list(set(_pokemon_data[p]["color"] for p in _pokemon_data if "color" in _pokemon_data[p]))
    wrong_colors = [c for c in all_colors if c != correct]
    if len(wrong_colors) < 2:
        return None
    wrong_options = random.sample(wrong_colors, 2)
    options = [correct] + wrong_options
    random.shuffle(options)
    return {"question": question, "correct": correct, "options": options}


def _generate_pokemon_shape_question():
    if not _pokemon_data:
        return None
    valid_pokemon = [p for p in _pokemon_data if "shape" in _pokemon_data[p]]
    if not valid_pokemon:
        return None
    pokemon_id = random.choice(valid_pokemon)
    pokemon = _pokemon_data[pokemon_id]
    correct = pokemon["shape"]
    question = f"¿Qué forma tiene {pokemon_id}?"
    all_shapes = list(set(_pokemon_data[p]["shape"] for p in _pokemon_data if "shape" in _pokemon_data[p]))
    wrong_shapes = [s for s in all_shapes if s != correct]
    if len(wrong_shapes) < 2:
        return None
    wrong_options = random.sample(wrong_shapes, 2)
    options = [correct] + wrong_options
    random.shuffle(options)
    return {"question": question, "correct": correct, "options": options}


def _generate_pokemon_generation_question():
    if not _pokemon_data:
        return None
    valid_pokemon = [p for p in _pokemon_data if "generation" in _pokemon_data[p]]
    if not valid_pokemon:
        return None
    pokemon_id = random.choice(valid_pokemon)
    pokemon = _pokemon_data[pokemon_id]
    correct = pokemon["generation"]
    question = f"¿De qué generación es {pokemon_id}?"
    wrong_gens = [str(g) for g in range(1, 9) if str(g) != correct]
    if len(wrong_gens) < 2:
        return None
    wrong_options = random.sample(wrong_gens, 2)
    options = [correct] + wrong_options
    random.shuffle(options)
    return {"question": question, "correct": correct, "options": options}


def _generate_pokemon_catch_rate_question():
    if not _pokemon_data:
        return None
    valid_pokemon = [p for p in _pokemon_data if "catch_rate" in _pokemon_data[p]]
    if not valid_pokemon:
        return None
    pokemon_id = random.choice(valid_pokemon)
    pokemon = _pokemon_data[pokemon_id]
    correct = pokemon["catch_rate"]
    question = f"¿Cuál es la tasa de captura de {pokemon_id}?"
    try:
        rate_val = int(correct)
    except ValueError:
        return None
    wrong_rates = []
    offsets = [-100, -50, -25, 25, 50, 100]
    random.shuffle(offsets)
    for offset in offsets:
        wrong = rate_val + offset
        if 1 <= wrong <= 255 and str(wrong) != correct and str(wrong) not in wrong_rates:
            wrong_rates.append(str(wrong))
        if len(wrong_rates) >= 2:
            break
    if len(wrong_rates) < 2:
        return None
    options = [correct] + wrong_rates[:2]
    random.shuffle(options)
    return {"question": question, "correct": correct, "options": options}


GENERATORS = [
    _generate_type_weakness_question,
    _generate_type_resistance_question,
    _generate_type_immunity_question,
    _generate_pokemon_type_question,
    _generate_pokemon_stat_question,
    _generate_pokemon_weight_question,
    _generate_pokemon_height_question,
    _generate_pokemon_category_question,
    _generate_pokemon_evolution_question,
    _generate_pokemon_ability_question,
    _generate_pokemon_moves_at_level,
    _generate_pokemon_color_question,
    _generate_pokemon_shape_question,
    _generate_pokemon_generation_question,
    _generate_pokemon_catch_rate_question,
    _generate_move_type_question,
    _generate_move_category_question,
    _generate_move_power_question,
    _generate_move_accuracy_question,
    _generate_ability_description_question,
]


def generate_essentials_trivia(used_questions: set = None) -> dict:
    load_all()
    if used_questions is None:
        used_questions = set()
    generators = GENERATORS.copy()
    random.shuffle(generators)
    for gen_func in generators:
        for _ in range(20):
            try:
                question = gen_func()
                if question and question["question"] not in used_questions:
                    log.info(f"Generated essentials trivia: {question['question']}")
                    return question
            except Exception as e:
                log.error(f"Error generating question: {e}")
                continue
    for gen_func in generators:
        try:
            question = gen_func()
            if question:
                log.info(f"Generated essentials trivia (fallback): {question['question']}")
                return question
        except Exception as e:
            continue
    return {
        "question": "¿De qué tipo es BULBASAUR?",
        "correct": "GRASS/POISON",
        "options": ["GRASS/POISON", "FIRE", "WATER"],
    }
