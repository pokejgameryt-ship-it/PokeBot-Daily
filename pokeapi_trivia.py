import random
import logging

log = logging.getLogger("pokeapi_trivia")


def generate_daily_trivia(used_questions: set = None) -> dict:
    from essentials_trivia import generate_essentials_trivia
    result = generate_essentials_trivia(used_questions)
    if result:
        return result
    log.error("essentials_trivia returned None - check file loading logs")
    return None
