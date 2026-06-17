import sqlite3
from datetime import datetime, timedelta
from typing import Optional

DB_NAME = "pokebot_daily.db"


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            total_score INTEGER DEFAULT 0,
            trivia_correct INTEGER DEFAULT 0,
            trivia_total INTEGER DEFAULT 0,
            current_streak INTEGER DEFAULT 0,
            best_streak INTEGER DEFAULT 0,
            last_checkin DATE,
            retos_completed INTEGER DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trivia_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT,
            answer TEXT,
            options TEXT,
            winner_id INTEGER,
            winner_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS retos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            description TEXT,
            reward_points INTEGER DEFAULT 50,
            start_date DATE,
            end_date DATE,
            active INTEGER DEFAULT 1
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reto_completions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reto_id INTEGER,
            user_id INTEGER,
            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (reto_id) REFERENCES retos(id),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_trivia (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT,
            correct_answer TEXT,
            option1 TEXT,
            option2 TEXT,
            option3 TEXT,
            category TEXT,
            created_at DATE DEFAULT CURRENT_DATE,
            answered_by INTEGER
        )
    """)

    conn.commit()
    conn.close()


def get_user(user_id: int) -> Optional[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def create_user(user_id: int, username: str) -> dict:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)",
        (user_id, username),
    )
    conn.commit()
    conn.close()
    return get_user(user_id)


def update_score(user_id: int, points: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET total_score = total_score + ? WHERE user_id = ?",
        (points, user_id),
    )
    conn.commit()
    conn.close()


def update_trivia_stats(user_id: int, correct: bool):
    conn = get_connection()
    cursor = conn.cursor()
    if correct:
        cursor.execute(
            """UPDATE users SET 
               trivia_correct = trivia_correct + 1,
               trivia_total = trivia_total + 1,
               current_streak = current_streak + 1,
               best_streak = MAX(best_streak, current_streak + 1)
               WHERE user_id = ?""",
            (user_id,),
        )
    else:
        cursor.execute(
            "UPDATE users SET trivia_total = trivia_total + 1, current_streak = 0 WHERE user_id = ?",
            (user_id,),
        )
    conn.commit()
    conn.close()


def checkin(user_id: int) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT last_checkin FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()

    today = datetime.now().date()

    if row and row["last_checkin"]:
        last = datetime.strptime(row["last_checkin"], "%Y-%m-%d").date()
        if last == today:
            conn.close()
            return False
        if (today - last).days > 1:
            cursor.execute(
                "UPDATE users SET current_streak = 0 WHERE user_id = ?", (user_id,)
            )

    cursor.execute(
        "UPDATE users SET last_checkin = ? WHERE user_id = ?",
        (today.isoformat(), user_id),
    )
    conn.commit()
    conn.close()
    return True


def get_leaderboard(limit: int = 10) -> list:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM users ORDER BY total_score DESC LIMIT ?", (limit,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_trivia_leaderboard(limit: int = 10) -> list:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT user_id, username, trivia_correct, trivia_total,
           CASE WHEN trivia_total > 0 THEN (trivia_correct * 100.0 / trivia_total) ELSE 0 END as accuracy
           FROM users WHERE trivia_total > 0
           ORDER BY trivia_correct DESC LIMIT ?""",
        (limit,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def create_reto(title: str, description: str, reward: int, days: int = 7) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    start = datetime.now().date()
    end = start + timedelta(days=days)
    cursor.execute(
        "INSERT INTO retos (title, description, reward_points, start_date, end_date) VALUES (?, ?, ?, ?, ?)",
        (title, description, reward, start.isoformat(), end.isoformat()),
    )
    reto_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return reto_id


def get_active_reto() -> Optional[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    today = datetime.now().date().isoformat()
    cursor.execute(
        "SELECT * FROM retos WHERE active = 1 AND end_date >= ? ORDER BY start_date DESC LIMIT 1",
        (today,),
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def complete_reto(user_id: int, reto_id: int) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM reto_completions WHERE reto_id = ? AND user_id = ?",
        (reto_id, user_id),
    )
    if cursor.fetchone():
        conn.close()
        return False

    cursor.execute(
        "INSERT INTO reto_completions (reto_id, user_id) VALUES (?, ?)",
        (reto_id, user_id),
    )
    cursor.execute(
        "UPDATE users SET retos_completed = retos_completed + 1 WHERE user_id = ?",
        (user_id,),
    )
    conn.commit()
    conn.close()
    return True


def save_trivia_question(question: str, correct: str, options: list):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO daily_trivia (question, correct_answer, option1, option2, option3) VALUES (?, ?, ?, ?, ?)",
        (question, correct, options[0], options[1], options[2]),
    )
    conn.commit()
    conn.close()


def get_daily_trivia() -> Optional[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    today = datetime.now().date().isoformat()
    cursor.execute(
        "SELECT * FROM daily_trivia WHERE created_at = ?", (today,)
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def mark_trivia_answered(trivia_id: int, user_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE daily_trivia SET answered_by = ? WHERE id = ?",
        (user_id, trivia_id),
    )
    conn.commit()
    conn.close()


def get_streak(user_id: int) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT current_streak FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row["current_streak"] if row else 0


def get_total_score(user_id: int) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT total_score FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row["total_score"] if row else 0
