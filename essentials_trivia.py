import random
import logging
import os
import re

log = logging.getLogger("essentials_trivia")

DATA_DIR = os.path.dirname(os.path.abspath(__file__))

_ABILITY_TRANSLATIONS = {
    "The stench may cause the target to flinch.": "El hedor puede hacer que el objetivo retroceda.",
    "The Pokémon makes it rain if it appears in battle.": "El Pokémon hace que llueva si aparece en batalla.",
    "Its Speed stat is gradually boosted.": "Su estadística de Velocidad aumenta gradualmente.",
    "The Pokémon is protected against critical hits.": "El Pokémon está protegido contra golpes críticos.",
    "It cannot be knocked out with one hit.": "No puede ser derrotado de un solo golpe.",
    "Prevents the use of self-destructing moves.": "Impide el uso de movimientos auto destructivos.",
    "The Pokémon is protected from paralysis.": "El Pokémon está protegido contra la parálisis.",
    "Boosts the Pokémon's evasion in a sandstorm.": "Aumenta la evasión del Pokémon en una tormenta de arena.",
    "Contact with the Pokémon may cause paralysis.": "El contacto con el Pokémon puede causar parálisis.",
    "Restores HP if hit by an Electric-type move.": "Restaura PS si recibe un movimiento de tipo Eléctrico.",
    "Restores HP if hit by a Water-type move.": "Restaura PS si recibe un movimiento de tipo Agua.",
    "Prevents it from becoming infatuated.": "Impide que se enamore.",
    "Eliminates the effects of weather.": "Elimina los efectos del clima.",
    "The Pokémon's accuracy is boosted.": "La precisión del Pokémon aumenta.",
    "Prevents the Pokémon from falling asleep.": "Impide que el Pokémon se duerma.",
    "Changes the Pokémon's type to the foe's move.": "Cambia el tipo del Pokémon al del movimiento del rival.",
    "Prevents the Pokémon from getting poisoned.": "Impide que el Pokémon se envenene.",
    "It powers up Fire-type moves if it's hit by one.": "Potencia movimientos de tipo Fuego si recibe uno.",
    "Blocks the added effects of attacks taken.": "Bloquea los efectos adicionales de los ataques recibidos.",
    "Prevents the Pokémon from becoming confused.": "Impide que el Pokémon se confunda.",
    "Negates all moves that force switching out.": "Anula todos los movimientos que fuerzan el cambio.",
    "Lowers the foe's Attack stat.": "Reduce la estadística de Ataque del rival.",
    "Prevents the foe from escaping.": "Impide que el rival escape.",
    "Inflicts damage to the foe on contact.": "Inflige daño al rival al contacto.",
    "Only super-effective moves will hit.": "Solo los movimientos súper efectivos impactan.",
    "Gives full immunity to all Ground-type moves.": "Da inmunidad total a todos los movimientos de tipo Tierra.",
    "Contact may poison or cause paralysis or sleep.": "El contacto puede envenenar, paralizar o dormir.",
    "Passes a burn, poison, or paralysis to the foe.": "Transfiere quemadura, veneno o parálisis al rival.",
    "Prevents other Pokémon from lowering its stats.": "Impide que otros Pokémon bajen sus estadísticas.",
    "All status problems heal when it switches out.": "Todos los problemas de estado se curan al cambiar.",
    "Draws in all Electric-type moves to up Sp. Attack.": "Atrae todos los movimientos de tipo Eléctrico para subir At. Esp.",
    "Boosts the likelihood of added effects appearing.": "Aumenta la probabilidad de efectos adicionales.",
    "Boosts the Pokémon's Speed in rain.": "Aumenta la Velocidad del Pokémon bajo la lluvia.",
    "Boosts the Pokémon's Speed in sunshine.": "Aumenta la Velocidad del Pokémon bajo el sol.",
    "Raises the likelihood of meeting wild Pokémon.": "Aumenta la probabilidad de encontrar Pokémon salvajes.",
    "The Pokémon copies a foe's Ability.": "El Pokémon copia la Habilidad del rival.",
    "Raises the Pokémon's Attack stat.": "Aumenta la estadística de Ataque del Pokémon.",
    "Contact with the Pokémon may poison the attacker.": "El contacto con el Pokémon puede envenenar al atacante.",
    "The Pokémon is protected from flinching.": "El Pokémon está protegido contra retrocesos.",
    "Prevents the Pokémon from becoming frozen.": "Impide que el Pokémon se congele.",
    "Prevents the Pokémon from getting a burn.": "Impide que el Pokémon se queme.",
    "Prevents Steel-type Pokémon from escaping.": "Impide que Pokémon de tipo Acero escapen.",
    "Gives full immunity to all sound-based moves.": "Da inmunidad total a todos los movimientos basados en sonido.",
    "The Pokémon gradually regains HP in rain.": "El Pokémon recupera PS gradualmente bajo la lluvia.",
    "The Pokémon summons a sandstorm in battle.": "El Pokémon invoca una tormenta de arena en batalla.",
    "The Pokémon raises the foe's PP usage.": "El Pokémon aumenta el uso de PP del rival.",
    "Ups resistance to Fire- and Ice-type moves.": "Aumenta la resistencia a movimientos de tipo Fuego y Hielo.",
    "The Pokémon awakens quickly from sleep.": "El Pokémon se despierta rápidamente del sueño.",
    "Contact with the Pokémon may burn the attacker.": "El contacto con el Pokémon puede quemar al atacante.",
    "Enables a sure getaway from wild Pokémon.": "Permite escapar siempre de Pokémon salvajes.",
    "Prevents other Pokémon from lowering accuracy.": "Impide que otros Pokémon bajen la precisión.",
    "Prevents other Pokémon from lowering Attack stat.": "Impide que otros Pokémon bajen la estadística de Ataque.",
    "The Pokémon may pick up items.": "El Pokémon puede recoger objetos.",
    "Pokémon can't attack on consecutive turns.": "El Pokémon no puede atacar en turnos consecutivos.",
    "Boosts the Attack stat, but lowers accuracy.": "Aumenta el Ataque, pero reduce la precisión.",
    "Contact with the Pokémon may cause infatuation.": "El contacto con el Pokémon puede causar enamoramiento.",
    "Ups Sp. Atk if another Pokémon has Plus or Minus.": "Aumenta At. Esp. si otro Pokémon tiene Más o Menos.",
    "Castform transforms with the weather.": "Castform se transforma con el clima.",
    "Protects the Pokémon from item theft.": "Protege al Pokémon del robo de objetos.",
    "The Pokémon may heal its own status problems.": "El Pokémon puede curar sus propios problemas de estado.",
    "Boosts Attack if there is a status problem.": "Aumenta el Ataque si hay un problema de estado.",
    "Ups Defense if there is a status problem.": "Aumenta la Defensa si hay un problema de estado.",
    "Damages attackers using any draining move.": "Daña a los atacantes que usen movimientos absorbentes.",
    "Powers up Grass-type moves in a pinch.": "Potencia movimientos de tipo Planta en apuros.",
    "Powers up Fire-type moves in a pinch.": "Potencia movimientos de tipo Fuego en apuros.",
    "Powers up Water-type moves in a pinch.": "Potencia movimientos de tipo Agua en apuros.",
    "Powers up Bug-type moves in a pinch.": "Potencia movimientos de tipo Bicho en apuros.",
    "Protects the Pokémon from recoil damage.": "Protege al Pokémon del daño de retroceso.",
    "Turns the sunlight harsh if it is in battle.": "Hace que el sol sea intenso si está en batalla.",
    "Prevents the foe from fleeing.": "Impide que el rival huya.",
    "Raises evasion if the Pokémon is confused.": "Aumenta la evasión si el Pokémon está confundido.",
    "Raises Speed if hit by an Electric-type move.": "Aumenta la Velocidad si recibe un movimiento de tipo Eléctrico.",
    "Deals more damage to a foe of the same gender.": "Inflige más daño a un rival del mismo género.",
    "Raises Speed each time the Pokémon flinches.": "Aumenta la Velocidad cada vez que el Pokémon retrocede.",
    "Raises evasion in a hailstorm.": "Aumenta la evasión en una tormenta de granizo.",
    "Encourages the early use of a held Berry.": "Favorece el uso temprano de una Baya equipada.",
    "Maxes Attack after taking a critical hit.": "Maximiza el Ataque después de recibir un golpe crítico.",
    "Raises Speed if a held item is used.": "Aumenta la Velocidad si se usa un objeto equipado.",
    "Weakens the power of Fire-type moves.": "Debilita la potencia de los movimientos de tipo Fuego.",
    "The Pokémon is prone to wild stat changes.": "El Pokémon es propenso a cambios salvajes de estadísticas.",
    "Reduces HP if it is hot. Water restores HP.": "Reduce PS si hace calor. El agua restaura PS.",
    "Adjusts power according to a foe's defenses.": "Ajusta la potencia según las defensas del rival.",
    "Boosts the power of punching moves.": "Aumenta la potencia de los movimientos de puñetazo.",
    "Restores HP if the Pokémon is poisoned.": "Restaura PS si el Pokémon está envenenado.",
    "Powers up moves of the same type.": "Potencia movimientos del mismo tipo.",
    "Increases the frequency of multi-strike moves.": "Aumenta la frecuencia de movimientos de múltiples golpes.",
    "Heals status problems if it is raining.": "Cura problemas de estado si está lloviendo.",
    "In sunshine, Sp. Atk is boosted but HP decreases.": "Bajo el sol, At. Esp. aumenta pero los PS disminuyen.",
    "Boosts Speed if there is a status problem.": "Aumenta la Velocidad si hay un problema de estado.",
    "All the Pokémon's moves become the Normal type.": "Todos los movimientos del Pokémon se vuelven de tipo Normal.",
    "Powers up moves if they become critical hits.": "Potencia movimientos si se convierten en golpes críticos.",
    "The Pokémon only takes damage from attacks.": "El Pokémon solo recibe daño de ataques.",
    "Ensures attacks by or against the Pokémon land.": "Asegura que los ataques por o contra el Pokémon impacten.",
    "The Pokémon moves after all other Pokémon do.": "El Pokémon se mueve después de todos los demás Pokémon.",
    "The Pokémon can switch out when its HP drops to half or less.": "El Pokémon puede cambiar cuando sus PS bajan a la mitad o menos.",
    "Boosts evasion if it is hailing.": "Aumenta la evasión si está granizando.",
    "The Pokémon isProtected from priority moves.": "El Pokémon está protegido contra movimientos prioritarios.",
    "The Pokémon's type changes to match the move used.": "El tipo del Pokémon cambia según el movimiento usado.",
    "Restores a little HP when withdrawn from battle.": "Restaura un poco de PS al ser cambiado de batalla.",
    "Protects the Pokémon from status problems.": "Protege al Pokémon de problemas de estado.",
    "It may confuse the attacker if it makes contact.": "Puede confundir al atacante si hay contacto.",
    "Restores HP if it is poisoned.": "Restaura PS si está envenenado.",
    "The Pokémon may be protected from attacks.": "El Pokémon puede estar protegido contra ataques.",
    "Damages the attacker on contact.": "Daña al atacante al contacto.",
    "The Pokémon restores HP if it uses a held Berry.": "El Pokémon restaura PS si usa una Baya equipada.",
    "Boosts Sp. Atk when hit by a Fire-type move.": "Aumenta At. Esp. al recibir un movimiento de tipo Fuego.",
    "Boosts evasion in a hailstorm.": "Aumenta la evasión en una tormenta de granizo.",
    "Protects from moves with increased critical-hit ratios.": "Protege de movimientos con mayor ratio de golpes críticos.",
    "Contact with the Pokémon may lower the attacker's Sp. Atk.": "El contacto con el Pokémon puede bajar el At. Esp. del atacante.",
    "The Pokémon copies the foe's held item.": "El Pokémon copia el objeto equipado del rival.",
    "Only damage will land on the Pokémon.": "Solo el daño impactará en el Pokémon.",
    "The Pokémon transforms into the foe.": "El Pokémon se transforma en el rival.",
    "Transforms into the foe's type before attacks.": "Se transforma en el tipo del rival antes de los ataques.",
    "Protects the Pokémon from having its item stolen.": "Protege al Pokémon de que le roben su objeto.",
    "Makes the Pokémon use its held Berry before fainting.": "Hace que el Pokémon use su Baya antes de debilitarse.",
    "Protects the Pokémon from having its item taken.": "Protege al Pokémon de que le quiten su objeto.",
    "The Pokémon intimidates opposing Pokémon upon entering battle.": "El Pokémon intimida a los Pokémon rivales al entrar en batalla.",
    "The Pokémon lowers the foe's Sp. Atk.": "El Pokémon reduce el At. Esp. del rival.",
    "The Pokémon is protected by its flame, which may burn attackers.": "El Pokémon está protegido por su llama, que puede quemar atacantes.",
    "The Pokémon may pick up the item the foe used.": "El Pokémon puede recoger el objeto que usó el rival.",
    "Contact with the Pokémon may lower the attacker's Defense.": "El contacto con el Pokémon puede bajar la Defensa del atacante.",
    "Contact with the Pokémon may lower the attacker's Speed.": "El contacto con el Pokémon puede bajar la Velocidad del atacante.",
    "Contact with the Pokémon may confuse the attacker.": "El contacto con el Pokémon puede confundir al atacante.",
    "Prevents the Pokémon from being forced to switch.": "Impide que el Pokémon sea forzado a cambiar.",
    "The Pokémon may break the foe's held item.": "El Pokémon puede romper el objeto equipado del rival.",
    "The Pokémon may steal the foe's held item.": "El Pokémon puede robar el objeto equipado del rival.",
    "The Pokémon may switch status problems with the foe.": "El Pokémon puede intercambiar problemas de estado con el rival.",
    "The Pokémon may poison the attacker on contact.": "El Pokémon puede envenenar al atacante al contacto.",
    "The Pokémon may paralyze the attacker on contact.": "El Pokémon puede paralizar al atacante al contacto.",
    "The Pokémon may burn the attacker on contact.": "El Pokémon puede quemar al atacante al contacto.",
    "The Pokémon may freeze the attacker on contact.": "El Pokémon puede congelar al atacante al contacto.",
    "The Pokémon may put the attacker to sleep on contact.": "El Pokémon puede dormir al atacante al contacto.",
    "The Pokémon may badly poison the attacker on contact.": "El Pokémon puede envenenar gravemente al atacante al contacto.",
    "The Pokémon's contact moves have increased critical-hit ratios.": "Los movimientos de contacto del Pokémon tienen mayor ratio de golpes críticos.",
    "The Pokémon may raise the foe's Attack stat.": "El Pokémon puede aumentar la estadística de Ataque del rival.",
    "The Pokémon may raise the foe's Sp. Atk stat.": "El Pokémon puede aumentar la estadística de At. Esp. del rival.",
    "The Pokémon may lower the foe's Attack stat.": "El Pokémon puede reducir la estadística de Ataque del rival.",
    "The Pokémon may lower the foe's Defense stat.": "El Pokémon puede reducir la estadística de Defensa del rival.",
    "The Pokémon may lower the foe's Sp. Atk stat.": "El Pokémon puede reducir la estadística de At. Esp. del rival.",
    "The Pokémon may lower the foe's Sp. Def stat.": "El Pokémon puede reducir la estadística de Def. Esp. del rival.",
    "The Pokémon may lower the foe's Speed stat.": "El Pokémon puede reducir la estadística de Velocidad del rival.",
    "The Pokémon may lower the foe's accuracy.": "El Pokémon puede reducir la precisión del rival.",
    "The Pokémon may confuse the foe.": "El Pokémon puede confundir al rival.",
    "The Pokémon may paralyze the foe.": "El Pokémon puede paralizar al rival.",
    "The Pokémon may burn the foe.": "El Pokémon puede quemar al rival.",
    "The Pokémon may freeze the foe.": "El Pokémon puede congelar al rival.",
    "The Pokémon may put the foe to sleep.": "El Pokémon puede dormir al rival.",
    "The Pokémon may poison the foe.": "El Pokémon puede envenenar al rival.",
    "The Pokémon may cause the foe to flinch.": "El Pokémon puede hacer retroceder al rival.",
    "The Pokémon may lower the foe's Sp. Def.": "El Pokémon puede reducir la Def. Esp. del rival.",
    "Boosts the power of Grass-type moves.": "Aumenta la potencia de los movimientos de tipo Planta.",
    "Boosts the power of Fire-type moves.": "Aumenta la potencia de los movimientos de tipo Fuego.",
    "Boosts the power of Water-type moves.": "Aumenta la potencia de los movimientos de tipo Agua.",
    "Boosts the power of Electric-type moves.": "Aumenta la potencia de los movimientos de tipo Eléctrico.",
    "Boosts the power of Ice-type moves.": "Aumenta la potencia de los movimientos de tipo Hielo.",
    "Boosts the power of Fighting-type moves.": "Aumenta la potencia de los movimientos de tipo Lucha.",
    "Boosts the power of Poison-type moves.": "Aumenta la potencia de los movimientos de tipo Veneno.",
    "Boosts the power of Ground-type moves.": "Aumenta la potencia de los movimientos de tipo Tierra.",
    "Boosts the power of Flying-type moves.": "Aumenta la potencia de los movimientos de tipo Volador.",
    "Boosts the power of Psychic-type moves.": "Aumenta la potencia de los movimientos de tipo Psíquico.",
    "Boosts the power of Bug-type moves.": "Aumenta la potencia de los movimientos de tipo Bicho.",
    "Boosts the power of Rock-type moves.": "Aumenta la potencia de los movimientos de tipo Roca.",
    "Boosts the power of Ghost-type moves.": "Aumenta la potencia de los movimientos de tipo Fantasma.",
    "Boosts the power of Dragon-type moves.": "Aumenta la potencia de los movimientos de tipo Dragón.",
    "Boosts the power of Dark-type moves.": "Aumenta la potencia de los movimientos de tipo Siniestro.",
    "Boosts the power of Steel-type moves.": "Aumenta la potencia de los movimientos de tipo Acero.",
    "Boosts the power of Fairy-type moves.": "Aumenta la potencia de los movimientos de tipo Hada.",
    "The Pokémon is less likely to be startled.": "El Pokémon es menos propenso a ser sorprendido.",
    "Boosts the Pokémon's stats in a hailstorm.": "Aumenta las estadísticas del Pokémon en una tormenta de granizo.",
    "Boosts the Pokémon's stats in rain.": "Aumenta las estadísticas del Pokémon bajo la lluvia.",
    "Boosts the Pokémon's stats in sun.": "Aumenta las estadísticas del Pokémon bajo el sol.",
    "Boosts the Pokémon's stats in a sandstorm.": "Aumenta las estadísticas del Pokémon en una tormenta de arena.",
    "Boosts the Pokémon's stats during harsh sunlight.": "Aumenta las estadísticas del Pokémon bajo luz solar intensa.",
    "The Pokémon can hit Ghost-type Pokémon with Normal- and Fighting-type moves.": "El Pokémon puede golpear a Pokémon Fantasma con movimientos Normal y Lucha.",
    "The Pokémon can hit Dark-type Pokémon with Psychic-type moves.": "El Pokémon puede golpear a Pokémon Siniestro con movimientos Psíquico.",
    "The Pokémon can hit Steel-type Pokémon with Poison-type moves.": "El Pokémon puede golpear a Pokémon Acero con movimientos Veneno.",
    "The Pokémon can hit Ground-type Pokémon with Flying-type moves.": "El Pokémon puede golpear a Pokémon Tierra con movimientos Volador.",
    "The Pokémon can hit Grass-type Pokémon with Bug-type moves.": "El Pokémon puede golpear a Pokémon Planta con movimientos Bicho.",
    "The Pokémon can hit Fire-type Pokémon with Grass-type moves.": "El Pokémon puede golpear a Pokémon Fuego con movimientos Planta.",
    "The Pokémon can hit Water-type Pokémon with Grass-type moves.": "El Pokémon puede golpear a Pokémon Agua con movimientos Planta.",
    "The Pokémon can hit Flying-type Pokémon with Ground-type moves.": "El Pokémon puede golpear a Pokémon Volador con movimientos Tierra.",
    "The Pokémon can hit Rock-type Pokémon with Grass-type moves.": "El Pokémon puede golpear a Pokémon Roca con movimientos Planta.",
    "The Pokémon can hit Dragon-type Pokémon with Fairy-type moves.": "El Pokémon puede golpear a Pokémon Dragón con movimientos Hada.",
    "The Pokémon can hit Dark-type Pokémon with Dark-type moves.": "El Pokémon puede golpear a Pokémon Siniestro con movimientos Siniestro.",
    "The Pokémon can hit Ghost-type Pokémon with Ghost-type moves.": "El Pokémon puede golpear a Pokémon Fantasma con movimientos Fantasma.",
    "The Pokémon can hit Steel-type Pokémon with Steel-type moves.": "El Pokémon puede golpear a Pokémon Acero con movimientos Acero.",
    "The Pokémon can hit Ice-type Pokémon with Fire-type moves.": "El Pokémon puede golpear a Pokémon Hielo con movimientos Fuego.",
    "The Pokémon can hit Fire-type Pokémon with Water-type moves.": "El Pokémon puede golpear a Pokémon Fuego con movimientos Agua.",
    "The Pokémon can hit Grass-type Pokémon with Fire-type moves.": "El Pokémon puede golpear a Pokémon Planta con movimientos Fuego.",
    "The Pokémon can hit Water-type Pokémon with Electric-type moves.": "El Pokémon puede golpear a Pokémon Agua con movimientos Eléctrico.",
    "The Pokémon can hit Electric-type Pokémon with Ground-type moves.": "El Pokémon puede golpear a Pokémon Eléctrico con movimientos Tierra.",
    "The Pokémon can hit Rock-type Pokémon with Water-type moves.": "El Pokémon puede golpear a Pokémon Roca con movimientos Agua.",
    "The Pokémon can hit Bug-type Pokémon with Flying-type moves.": "El Pokémon puede golpear a Pokémon Bicho con movimientos Volador.",
    "The Pokémon can hit Fighting-type Pokémon with Psychic-type moves.": "El Pokémon puede golpear a Pokémon Lucha con movimientos Psíquico.",
    "The Pokémon can hit Poison-type Pokémon with Ground-type moves.": "El Pokémon puede golpear a Pokémon Veneno con movimientos Tierra.",
}

def _translate_desc(eng: str) -> str:
    if eng in _ABILITY_TRANSLATIONS:
        return _ABILITY_TRANSLATIONS[eng]
    return eng

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
    try:
        with open(filepath, "r", encoding="utf-8-sig") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
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
    except Exception as e:
        log.error(f"Failed to load types.txt: {e}")


def _parse_pokemon():
    global _pokemon_data
    filepath = os.path.join(DATA_DIR, "pokemon.txt")
    current_id = None
    try:
        with open(filepath, "r", encoding="utf-8-sig") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
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
    except Exception as e:
        log.error(f"Failed to load pokemon.txt: {e}")


def _parse_moves():
    global _moves_data
    filepath = os.path.join(DATA_DIR, "moves.txt")
    current_move = None
    try:
        with open(filepath, "r", encoding="utf-8-sig") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
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
    except Exception as e:
        log.error(f"Failed to load moves.txt: {e}")


def _parse_abilities():
    global _abilities_data
    filepath = os.path.join(DATA_DIR, "abilities.txt")
    current_ability = None
    try:
        with open(filepath, "r", encoding="utf-8-sig") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
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
    except Exception as e:
        log.error(f"Failed to load abilities.txt: {e}")


def _parse_items():
    global _items_data
    filepath = os.path.join(DATA_DIR, "items.txt")
    current_item = None
    try:
        with open(filepath, "r", encoding="utf-8-sig") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
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
    except Exception as e:
        log.error(f"Failed to load items.txt: {e}")


def load_all():
    global _loaded
    if _loaded:
        return True
    _parse_types()
    _parse_pokemon()
    _parse_moves()
    _parse_abilities()
    _parse_items()
    total = len(_types_data) + len(_pokemon_data) + len(_moves_data) + len(_abilities_data)
    if total == 0:
        log.error("CRITICAL: No data loaded from any Essentials file!")
        return False
    _loaded = True
    log.info(f"All Essentials data loaded: {len(_types_data)} types, {len(_pokemon_data)} pokemon, {len(_moves_data)} moves, {len(_abilities_data)} abilities, {len(_items_data)} items")
    return True


def _generate_type_weakness_question():
    valid_types = [t for t in _types_data if _types_data[t].get("weaknesses") and t != "QMARKS"]
    if not valid_types:
        return None
    target_type = random.choice(valid_types)
    weaknesses = _types_data[target_type]["weaknesses"]
    correct = random.choice(weaknesses)
    question = f"¿Contra qué tipo es débil {target_type}?"
    all_types = [t for t in _types_data if t != "QMARKS" and t != target_type]
    wrong_pool = [t for t in all_types if t not in weaknesses]
    if len(wrong_pool) < 2:
        return None
    wrong_options = random.sample(wrong_pool, 2)
    options = [correct] + wrong_options
    random.shuffle(options)
    return {"question": question, "correct": correct, "options": options}


def _generate_type_resistance_question():
    valid_types = [t for t in _types_data if _types_data[t].get("resistances") and t != "QMARKS"]
    if not valid_types:
        return None
    target_type = random.choice(valid_types)
    resistances = _types_data[target_type]["resistances"]
    correct = random.choice(resistances)
    question = f"¿Qué tipo puede resistir {target_type}?"
    all_types = [t for t in _types_data if t != "QMARKS" and t != target_type]
    wrong_pool = [t for t in all_types if t not in resistances]
    if len(wrong_pool) < 2:
        return None
    wrong_options = random.sample(wrong_pool, 2)
    options = [correct] + wrong_options
    random.shuffle(options)
    return {"question": question, "correct": correct, "options": options}


def _generate_type_immunity_question():
    valid_types = [t for t in _types_data if _types_data[t].get("immunities") and t != "QMARKS"]
    if not valid_types:
        return None
    target_type = random.choice(valid_types)
    immunities = _types_data[target_type]["immunities"]
    correct = random.choice(immunities)
    question = f"¿A qué tipo es inmune {target_type}?"
    all_types = [t for t in _types_data if t != "QMARKS" and t != target_type]
    wrong_pool = [t for t in all_types if t not in immunities]
    if len(wrong_pool) < 2:
        return None
    wrong_options = random.sample(wrong_pool, 2)
    options = [correct] + wrong_options
    random.shuffle(options)
    return {"question": question, "correct": correct, "options": options}


def _generate_pokemon_type_question():
    pokemon_id = random.choice(list(_pokemon_data.keys()))
    pokemon = _pokemon_data[pokemon_id]
    if "types" not in pokemon:
        return None
    correct = "/".join(pokemon["types"])
    question = f"¿De qué tipo es el Pokémon {pokemon_id}?"
    all_types = list(_types_data.keys())
    wrong_types = [t for t in all_types if t not in pokemon["types"] and t != "QMARKS"]
    if len(wrong_types) < 2:
        return None
    wrong_options = random.sample(wrong_types, 2)
    options = [correct] + wrong_options
    random.shuffle(options)
    return {"question": question, "correct": correct, "options": options}


def _generate_pokemon_stat_question():
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
    valid_pokemon = [p for p in _pokemon_data if "weight" in _pokemon_data[p]]
    if not valid_pokemon:
        return None
    pokemon_id = random.choice(valid_pokemon)
    pokemon = _pokemon_data[pokemon_id]
    try:
        weight_val = float(pokemon["weight"])
    except (ValueError, TypeError):
        return None
    if weight_val < 1:
        return None
    question = f"¿Cuánto pesa {pokemon_id} en kg?"
    wrong_weights = []
    pct = weight_val * 0.3
    offsets = [-pct * 1.5, -pct, -pct * 0.5, pct * 0.5, pct, pct * 1.5]
    random.shuffle(offsets)
    for offset in offsets:
        wrong = weight_val + offset
        wrong = max(0.5, round(wrong, 1))
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
    valid_pokemon = [p for p in _pokemon_data if "height" in _pokemon_data[p]]
    if not valid_pokemon:
        return None
    pokemon_id = random.choice(valid_pokemon)
    pokemon = _pokemon_data[pokemon_id]
    try:
        height_val = float(pokemon["height"])
    except (ValueError, TypeError):
        return None
    if height_val < 0.3:
        return None
    question = f"¿Cuánto mide {pokemon_id} en metros?"
    wrong_heights = []
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
    valid_moves = [m for m in _moves_data if "type" in _moves_data[m]]
    if not valid_moves:
        return None
    move_id = random.choice(valid_moves)
    move = _moves_data[move_id]
    correct = move["type"]
    question = f"¿De qué tipo es el movimiento {move_id}?"
    all_types = [t for t in _types_data if t != "QMARKS"]
    wrong_types = [t for t in all_types if t != correct]
    if len(wrong_types) < 2:
        return None
    wrong_options = random.sample(wrong_types, 2)
    options = [correct] + wrong_options
    random.shuffle(options)
    return {"question": question, "correct": correct, "options": options}


def _generate_move_category_question():
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
    valid_abilities = [a for a in _abilities_data if "description" in _abilities_data[a]]
    if not valid_abilities:
        return None
    ability_id = random.choice(valid_abilities)
    ability = _abilities_data[ability_id]
    eng = ability["description"]
    correct = f"{eng}\n{_translate_desc(eng)}"
    question = f"¿Qué efecto tiene la habilidad {ability_id}?"
    all_abilities = [a for a in valid_abilities if a != ability_id and _abilities_data[a].get("description")]
    if len(all_abilities) < 2:
        return None
    wrong_ids = random.sample(all_abilities, 2)
    wrong_options = []
    for a in wrong_ids:
        e = _abilities_data[a]["description"]
        wrong_options.append(f"{e}\n{_translate_desc(e)}")
    options = [correct] + wrong_options
    random.shuffle(options)
    return {"question": question, "correct": correct, "options": options}


def _generate_pokemon_moves_at_level():
    valid_pokemon = [p for p in _pokemon_data if "moves" in _pokemon_data[p] and _pokemon_data[p]["moves"]]
    if not valid_pokemon:
        return None
    pokemon_id = random.choice(valid_pokemon)
    pokemon = _pokemon_data[pokemon_id]
    moves = pokemon["moves"]
    if len(moves) < 4:
        return None
    move = random.choice(moves)
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
    ok = load_all()
    if not ok:
        log.error("Essentials data not loaded, cannot generate trivia")
        return None
    if used_questions is None:
        used_questions = set()
    generators = GENERATORS[:]
    random.shuffle(generators)
    for gen_func in generators:
        for _ in range(30):
            try:
                question = gen_func()
                if question and question["question"] not in used_questions:
                    log.info(f"Generated trivia: {question['question']}")
                    return question
            except Exception as e:
                log.error(f"Error in {gen_func.__name__}: {e}")
                continue
    log.warning(f"All {len(used_questions)} used questions exhausted, generating any question")
    for gen_func in generators:
        try:
            question = gen_func()
            if question:
                return question
        except Exception:
            continue
    return None
