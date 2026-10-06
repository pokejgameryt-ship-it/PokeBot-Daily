"""Tests for essentials_trivia generators."""
import pytest

# Import the module to trigger load_all()
from essentials_trivia import load_all, generate_essentials_trivia


@pytest.fixture(scope="session", autouse=True)
def _load_all():
    """Load all data once per test session."""
    ok = load_all()
    assert ok, "load_all() should succeed"


# Some generators return None if data pool is too small (e.g., evolution, height, moves at level)
# We test the ones that should always work with full data
GENERATORS_ALWAYS_WORK = [
    "_generate_type_weakness_question",
    "_generate_type_resistance_question",
    "_generate_type_immunity_question",
    "_generate_pokemon_type_question",
    "_generate_pokemon_stat_question",
    "_generate_pokemon_weight_question",
    "_generate_pokemon_category_question",
    "_generate_pokemon_ability_question",
    "_generate_pokemon_color_question",
    "_generate_pokemon_shape_question",
    "_generate_pokemon_generation_question",
    "_generate_pokemon_catch_rate_question",
    "_generate_move_type_question",
    "_generate_move_category_question",
    "_generate_move_power_question",
    "_generate_move_accuracy_question",
    "_generate_ability_description_question",
]


@pytest.mark.parametrize("gen_name", GENERATORS_ALWAYS_WORK)
def test_generators_produce_valid_question(gen_name):
    """Each generator should produce a valid question dict."""
    gen_func = getattr(__import__("essentials_trivia"), gen_name)
    question = gen_func()
    assert question is not None, f"{gen_name} returned None"
    assert isinstance(question, dict), f"{gen_name} returned non-dict"
    assert "question" in question, f"{gen_name} missing 'question'"
    assert "correct" in question, f"{gen_name} missing 'correct'"
    assert "options" in question, f"{gen_name} missing 'options'"
    assert isinstance(question["options"], list), f"{gen_name} options not list"
    assert len(question["options"]) == 3, f"{gen_name} should have 3 options"
    assert question["correct"] in question["options"], f"{gen_name} correct not in options"
    assert len(set(question["options"])) == 3, f"{gen_name} options not unique"
    assert question["question"], f"{gen_name} empty question"


def test_generate_essentials_trivia_skips_used():
    """generate_essentials_trivia should not return a question in used_questions."""
    used = set()
    q1 = generate_essentials_trivia(used)
    assert q1 is not None
    used.add(q1["question"])
    q2 = generate_essentials_trivia(used)
    if q2:
        assert q2["question"] not in used, "Should not return used question"