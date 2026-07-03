import json
import os
import random
import logging
import requests
import database as db

log = logging.getLogger("question_gen")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
GENERATOR_MODEL = "meta-llama/llama-3.1-8b-instruct:free"
VERIFIER_MODEL = "google/gemma-2-9b-it:free"

DIFFICULTY_PROMPTS = {
    "easy": (
        "Genera 1 pregunta de trivia Pokémon de dificultad FÁCIL. "
        "La pregunta debe ser sobre tipo de Pokémon, generación, o conocimiento básico que cualquier jugador casual sepa. "
        "Responde SOLO con JSON válido: {\"question\": \"¿...?\", \"correct\": \"Respuesta\", \"options\": [\"Opción A\", \"Opción B\", \"Opción C\"]} "
        "La respuesta correcta debe estar en las opciones. Las opciones deben ser plausible pero solo una correcta."
    ),
    "medium": (
        "Genera 1 pregunta de trivia Pokémon de dificultad INTERMEDIA. "
        "La pregunta debe ser sobre habilidades, objetos de evolución, estadísticas generales, movimientos, o aspectos para jugadores recurrentes. "
        "Responde SOLO con JSON válido: {\"question\": \"¿...?\", \"correct\": \"Respuesta\", \"options\": [\"Opción A\", \"Opción B\", \"Opción C\"]} "
        "La respuesta correcta debe estar en las opciones."
    ),
    "hard": (
        "Genera 1 pregunta de trivia Pokémon de dificultad DIFÍCIL. "
        "La pregunta debe ser sobre estadísticas base concretas (números exactos), eventos temporales, descripciones de Pokédex, datos muy específicos que solo jugadores experimentados sepan. "
        "Responde SOLO con JSON válido: {\"question\": \"¿...?\", \"correct\": \"Respuesta\", \"options\": [\"Opción A\", \"Opción B\", \"Opción C\"]} "
        "La respuesta correcta debe estar en las opciones. Usa números y datos precisos."
    ),
}


def verify_question(question_data: dict) -> dict | None:
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        }
        verify_prompt = (
            f"Pregunta: {question_data['question']}\n"
            f"Respuesta marcada como correcta: {question_data['correct']}\n"
            f"Opciones: {question_data['options']}\n\n"
            "IMPORTANTE: Verifica ESTRICTAMENTE lo siguiente:\n"
            "1. ¿La respuesta marcada como correcta es REALMENTE correcta?\n"
            "2. ¿La respuesta correcta está entre las opciones?\n"
            "3. ¿Las opciones son plausible y solo una es correcta?\n\n"
            "Responde SOLO con JSON válido:\n"
            "- Si todo está correcto: {\"valid\": true}\n"
            "- Si la respuesta es incorrecta: {\"valid\": false, \"correct\": \"respuesta correcta\"}\n"
            "- Si la respuesta no está en opciones: {\"valid\": false, \"correct\": \"respuesta\", \"options\": [\"op1\", \"op2\", \"op3\"]}\n"
            "Responde SOLO con JSON, sin texto adicional."
        )
        payload = {
            "model": VERIFIER_MODEL,
            "messages": [
                {"role": "system", "content": "Eres un verificador de datos Pokémon. Sé preciso y estricto. Solo responde con JSON."},
                {"role": "user", "content": verify_prompt},
            ],
            "temperature": 0.1,
            "max_tokens": 300,
        }
        resp = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=30)
        if resp.status_code != 200:
            log.warning(f"Verify API error: {resp.status_code}")
            return question_data

        content = resp.json()["choices"][0]["message"]["content"]
        content = content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()

        result = json.loads(content)
        if result.get("valid"):
            log.info(f"Question verified as valid: {question_data['question'][:50]}...")
            return question_data
        elif "correct" in result:
            log.warning(f"Answer corrected: '{question_data['correct']}' -> '{result['correct']}'")
            question_data["correct"] = result["correct"]
            if "options" in result:
                question_data["options"] = result["options"]
                log.info(f"Options also corrected: {result['options']}")
            elif result["correct"] not in question_data["options"]:
                log.warning(f"Corrected answer not in options, replacing first option")
                question_data["options"][0] = result["correct"]
            return question_data
        return question_data

    except Exception as e:
        log.exception(f"Error verifying question: {e}")
        return question_data


def generate_question(difficulty: str) -> dict | None:
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": GENERATOR_MODEL,
            "messages": [
                {"role": "system", "content": "Eres un experto en Pokémon. Responde solo con JSON válido, sin texto adicional. ASEGÚRATE de que la respuesta correcta esté en las opciones."},
                {"role": "user", "content": DIFFICULTY_PROMPTS[difficulty] + "\n\nIMPORTANTE: La respuesta correcta DEBE estar en la lista de opciones. Verifica antes de responder."},
            ],
            "temperature": 0.9,
            "max_tokens": 300,
        }
        log.info(f"Generating {difficulty} question via OpenRouter...")
        log.info(f"API key set: {bool(OPENROUTER_API_KEY)}")
        resp = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=30)
        log.info(f"OpenRouter response: {resp.status_code}")
        if resp.status_code != 200:
            log.error(f"OpenRouter API error: {resp.status_code} - {resp.text[:200]}")
            return None

        content = resp.json()["choices"][0]["message"]["content"]
        content = content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()

        question_data = json.loads(content)

        if not all(k in question_data for k in ("question", "correct", "options")):
            log.error(f"Invalid question format: {question_data}")
            return None
        if len(question_data["options"]) != 3:
            log.error(f"Invalid options count: {question_data}")
            return None
        if question_data["correct"] not in question_data["options"]:
            log.warning(f"Correct answer not in options, adding it: {question_data['correct']}")
            question_data["options"][0] = question_data["correct"]

        log.info(f"Generated {difficulty} question: {question_data['question'][:50]}...")
        verified = verify_question(question_data)
        if verified:
            return verified
        return question_data

    except Exception as e:
        log.exception(f"Error generating question: {e}")
        return None


def get_trivia_question(difficulty: str, local_pool: list) -> dict:
    used = db.get_used_questions()

    available_local = [q for q in local_pool if q["question"] not in used]

    if available_local:
        question = random.choice(available_local)
        if question["correct"] not in question["options"]:
            log.warning(f"Local question has correct answer not in options, fixing: {question['question'][:50]}...")
            question["options"][0] = question["correct"]
        db.mark_question_used(question["question"])
        return question

    # If all questions used, reset and pick from full pool
    log.info(f"All local questions for {difficulty} used, resetting pool...")
    available_local = local_pool[:]
    question = random.choice(available_local)
    if question["correct"] not in question["options"]:
        log.warning(f"Fallback question has correct answer not in options, fixing: {question['question'][:50]}...")
        question["options"][0] = question["correct"]
    db.mark_question_used(question["question"])
    return question


def generate_weekly_question() -> dict | None:
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": GENERATOR_MODEL,
            "messages": [
                {"role": "system", "content": "Eres un experto en Pokémon. Responde solo con JSON válido, sin texto adicional."},
                {"role": "user", "content": (
                    "Genera 1 afirmación sobre Pokémon que sea VERDADERA o FALSA. "
                    "La afirmación debe ser clara y específica (tipo, movimientos, evoluciones, estadísticas, etc). "
                    "Responde SOLO con JSON válido: {\"question\": \"Afirmación sobre Pokémon\", \"answer\": true o false} "
                    "ALTERNA entre verdadero y falso."
                )},
            ],
            "temperature": 0.9,
            "max_tokens": 200,
        }
        resp = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=30)
        if resp.status_code != 200:
            log.error(f"OpenRouter API error (weekly): {resp.status_code} - {resp.text[:200]}")
            return None

        content = resp.json()["choices"][0]["message"]["content"]
        content = content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()

        data = json.loads(content)
        if "question" not in data or "answer" not in data:
            log.error(f"Invalid weekly question format: {data}")
            return None

        log.info(f"Generated weekly T/F question: {data['question'][:50]}...")
        verified = verify_weekly_question(data)
        if verified:
            return verified
        return data

    except Exception as e:
        log.exception(f"Error generating weekly question: {e}")
        return None


def verify_weekly_question(data: dict) -> dict | None:
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        }
        answer_text = "Verdadero" if data["answer"] else "Falso"
        verify_prompt = (
            f"Afirmación: {data['question']}\n"
            f"Marcada como: {answer_text}\n\n"
            "IMPORTANTE: Verifica ESTRICTAMENTE si la afirmación es verdadera o falsa.\n"
            "Responde SOLO con JSON válido:\n"
            "- Si es correcta: {\"valid\": true}\n"
            "- Si es incorrecta: {\"valid\": false, \"answer\": true/false}\n"
            "Responde SOLO con JSON, sin texto adicional."
        )
        payload = {
            "model": VERIFIER_MODEL,
            "messages": [
                {"role": "system", "content": "Eres un verificador de datos Pokémon. Sé preciso y estricto. Solo responde con JSON."},
                {"role": "user", "content": verify_prompt},
            ],
            "temperature": 0.1,
            "max_tokens": 200,
        }
        resp = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=30)
        if resp.status_code != 200:
            log.warning(f"Verify weekly API error: {resp.status_code}")
            return data

        content = resp.json()["choices"][0]["message"]["content"]
        content = content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()

        result = json.loads(content)
        if result.get("valid"):
            log.info(f"Weekly question verified as valid: {data['question'][:50]}...")
            return data
        elif "answer" in result:
            log.warning(f"Weekly answer corrected: {data['answer']} -> {result['answer']}")
            data["answer"] = result["answer"]
            return data
        return data

    except Exception as e:
        log.exception(f"Error verifying weekly question: {e}")
        return data


def get_weekly_questions(local_pool: list, count: int = 10) -> list:
    used = db.get_used_questions()

    available_local = [q for q in local_pool if q["question"] not in used]

    if len(available_local) >= count:
        selected = random.sample(available_local, count)
        for q in selected:
            db.mark_question_used(q["question"])
        return selected

    # If not enough unused questions, use all available and add from full pool
    log.info(f"Not enough unused weekly questions ({len(available_local)}/{count}), using full pool...")
    selected = available_local[:]
    for q in selected:
        db.mark_question_used(q["question"])

    # Add from full pool (excluding already selected)
    remaining = [q for q in local_pool if q not in selected]
    while len(selected) < count and remaining:
        q = remaining.pop(0)
        selected.append(q)
        db.mark_question_used(q["question"])

    # If still not enough, allow duplicates from full pool
    while len(selected) < count:
        q = random.choice(local_pool)
        selected.append(q)
        db.mark_question_used(q["question"])

    random.shuffle(selected)
    return selected[:count]
