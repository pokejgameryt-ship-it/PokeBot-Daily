"""Smoke test: all main modules import without errors."""
import pytest


@pytest.mark.parametrize("module_name", [
    "config",
    "database",
    "essentials_trivia",
    "verify",
    "trivia",
    "reto",
    "pokeapi_trivia",
])
def test_module_import(module_name):
    __import__(module_name)