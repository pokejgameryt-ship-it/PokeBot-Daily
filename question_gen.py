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
            "Verifica si la respuesta marcada como correcta es realmente correcta. "
            "Si es correcta, responde: {\"valid\": true}\n"
            "Si es incorrecta, responde: {\"valid\": false, \"correct\": \"respuesta correcta\"}\n"
            "Responde SOLO con JSON válido."
        )
        payload = {
            "model": VERIFIER_MODEL,
            "messages": [
                {"role": "system", "content": "Eres un verificador de datos Pokémon. Sé preciso y estricto."},
                {"role": "user", "content": verify_prompt},
            ],
            "temperature": 0.1,
            "max_tokens": 200,
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
            return question_data
        elif "correct" in result:
            log.warning(f"Answer corrected: '{question_data['correct']}' -> '{result['correct']}'")
            if result["correct"] in question_data["options"]:
                question_data["correct"] = result["correct"]
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
                {"role": "system", "content": "Eres un experto en Pokémon. Responde solo con JSON válido, sin texto adicional."},
                {"role": "user", "content": DIFFICULTY_PROMPTS[difficulty]},
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
            log.error(f"Correct answer not in options: {question_data}")
            return None

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
    recent_cutoff = db.get_recent_question_cutoff()

    available_local = [
        q for q in local_pool
        if q["question"] not in used or used[q["question"]] < recent_cutoff
    ]

    if available_local:
        question = random.choice(available_local)
        db.mark_question_used(question["question"])
        return question

    log.info(f"No local questions available for {difficulty}, generating via API...")
    for attempt in range(3):
        question = generate_question(difficulty)
        if question and question["question"] not in used:
            db.mark_question_used(question["question"])
            return question
        log.warning(f"Generated question was duplicate or invalid, attempt {attempt + 1}")

    log.warning("All generation attempts failed, using random from local pool")
    question = random.choice(local_pool)
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
            "Verifica si la afirmación es realmente verdadera o falsa. "
            "Si es correcta, responde: {\"valid\": true}\n"
            "Si es incorrecta, responde: {\"valid\": false, \"answer\": true/false}\n"
            "Responde SOLO con JSON válido."
        )
        payload = {
            "model": VERIFIER_MODEL,
            "messages": [
                {"role": "system", "content": "Eres un verificador de datos Pokémon. Sé preciso y estricto."},
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
    recent_cutoff = db.get_recent_question_cutoff()

    available_local = [
        q for q in local_pool
        if q["question"] not in used or used[q["question"]] < recent_cutoff
    ]

    if len(available_local) >= count:
        selected = random.sample(available_local, count)
        for q in selected:
            db.mark_question_used(q["question"])
        return selected

    log.info(f"Not enough local weekly questions ({len(available_local)}/{count}), generating via API...")
    selected = available_local[:]
    for q in selected:
        db.mark_question_used(q["question"])

    while len(selected) < count:
        question = generate_weekly_question()
        if question and question["question"] not in used:
            db.mark_question_used(question["question"])
            selected.append(question)
        elif len(selected) < count:
            fallback = random.choice(local_pool)
            if fallback not in selected:
                db.mark_question_used(fallback["question"])
                selected.append(fallback)

    random.shuffle(selected)
    return selected[:count]
