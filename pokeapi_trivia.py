import random
import logging

log = logging.getLogger("pokeapi_trivia")


def generate_daily_trivia(used_questions: set = None) -> dict:
    try:
        from essentials_trivia import generate_essentials_trivia
        return generate_essentials_trivia(used_questions)
    except Exception as e:
        log.error(f"Error with essentials trivia: {e}")
        return {
            "question": "¿De qué tipo es BULBASAUR?",
            "correct": "GRASS/POISON",
            "options": ["GRASS/POISON", "FIRE", "WATER"],
        }
