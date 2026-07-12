import random
import logging

log = logging.getLogger("pokeapi_trivia")


def generate_daily_trivia(used_questions: set = None) -> dict:
    try:
        from essentials_trivia import generate_essentials_trivia
        result = generate_essentials_trivia(used_questions)
        if result:
            return result
    except Exception as e:
        log.error(f"Error with essentials trivia: {e}", exc_info=True)
    
    log.warning("Essentials trivia failed, using hardcoded fallback")
    return {
        "question": "¿De qué tipo es BULBASAUR?",
        "correct": "GRASS/POISON",
        "options": ["GRASS/POISON", "FIRE", "WATER"],
    }
