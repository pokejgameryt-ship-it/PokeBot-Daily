"""Tests de regresión: send_quiz_question debe ENVIAR la pregunta por MD.

Cubre el bug donde la función construía embed+view pero no llamaba a
user.send (código muerto con `interaction` indefinido).
"""
import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import discord

import trivia


def test_send_quiz_question_envia_pregunta():
    user = AsyncMock()
    questions = [{"question": "¿Es Pikachu eléctrico?", "answer": True}]

    asyncio.run(trivia.send_quiz_question(user, questions, 0, "2026-W40", []))

    user.send.assert_awaited_once()
    kwargs = user.send.await_args.kwargs
    assert isinstance(kwargs["embed"], discord.Embed)
    assert isinstance(kwargs["view"], trivia.WeeklyQuizAnswerView)
    assert "1/1" in kwargs["embed"].title
    assert "Pikachu" in kwargs["embed"].description


def test_send_quiz_question_no_explota_si_dms_cerrados():
    user = AsyncMock()
    user.send.side_effect = discord.Forbidden(
        SimpleNamespace(status=403, reason="Forbidden"), "DMs closed"
    )
    questions = [{"question": "Q1", "answer": True}]

    # No debe explotar: Forbidden debe caer en su rama específica
    asyncio.run(trivia.send_quiz_question(user, questions, 0, "2026-W40", []))


def test_send_quiz_question_termina_al_acabar():
    user = AsyncMock()
    questions = [{"question": "Q1", "answer": True}]

    with patch.object(trivia, "finish_weekly_quiz", new=AsyncMock()) as finish:
        asyncio.run(trivia.send_quiz_question(user, questions, 1, "2026-W40", [True]))
        finish.assert_awaited_once()

    user.send.assert_not_awaited()
