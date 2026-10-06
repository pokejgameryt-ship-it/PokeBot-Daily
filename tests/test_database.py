"""Tests for database streak/points logic using a fake Firebase."""
import pytest
from unittest.mock import patch
from datetime import date, timedelta

# Mock firebase_admin before importing database
with patch("firebase_admin.initialize_app"):
    with patch("firebase_admin.credentials.Certificate"):
        import database as db


class FakeRef:
    """In-memory Firebase ref replacement."""
    def __init__(self, data=None):
        self._data = data or {}
        self._children = {}

    def child(self, key):
        if key not in self._children:
            self._children[key] = FakeRef({})
        return self._children[key]

    def get(self):
        return self._data

    def set(self, value):
        self._data = value

    def update(self, value):
        if self._data is None:
            self._data = {}
        self._data.update(value)

    def push(self):
        import uuid
        new_key = str(uuid.uuid4())
        child = FakeRef({})
        child.key = new_key
        self._children[new_key] = child
        return child

    def delete(self):
        self._data = None


@pytest.fixture
def fake_db():
    """Provide a clean fake database for each test."""
    # Reset module-level refs
    db._USERS_REF = None
    db._DAILY_REF = None
    db._WEEKLY_REF = None
    db._RETO_REF = None
    db._QUESTIONS_REF = None
    db._STARTUP_REF = None

    root = FakeRef({
        "users": {},
        "daily_trivia": {},
        "weekly_quiz": {},
        "retos": {},
        "used_questions": {},
        "startup_tasks": {},
    })

    with patch("database._users_ref", return_value=root.child("users")):
        with patch("database._daily_ref", return_value=root.child("daily_trivia")):
            with patch("database._weekly_quiz_ref", return_value=root.child("weekly_quiz")):
                with patch("database._retos_ref", return_value=root.child("retos")):
                    with patch("database._trivia_ref", return_value=root.child("used_questions")):
                        with patch("database._startup_ref", return_value=root.child("startup_tasks")):
                            yield root


# Tests that work with the fake ref
def test_update_score_creates_user(fake_db):
    db.update_score(123, 10, "TestUser")
    user = db._users_ref().child("123").get()
    assert user["total_score"] == 10
    assert user["username"] == "TestUser"


def test_update_trivia_stats_gap_resets(fake_db):
    """Gap of >=1 day should reset streak."""
    user_ref = db._users_ref().child("123")
    user_ref.set({
        "username": "Test",
        "total_score": 0,
        "current_streak": 5,
        "last_trivia_date": (date.today() - timedelta(days=2)).isoformat(),
    })
    result = db.update_trivia_stats(123, True)
    assert result["new_streak"] == 1


def test_startup_tasks(fake_db):
    today = date.today().isoformat()
    assert not db.was_startup_task_done("test_task", today)
    db.save_startup_task("test_task", today)
    assert db.was_startup_task_done("test_task", today)