import os
import sys

DATABASE_URL = os.getenv("DATABASE_URL", "")

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    HAS_POSTGRES = True
except ImportError:
    HAS_POSTGRES = False
    print("WARNING: psycopg2 not installed, PostgreSQL unavailable")

import sqlite3
from datetime import datetime, timedelta
from typing import Optional

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pokebot_daily.db")


def get_connection():
    if HAS_POSTGRES and DATABASE_URL:
        url = DATABASE_URL
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        conn = psycopg2.connect(url, cursor_factory=RealDictCursor, sslmode="require")
        return conn
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _is_postgres():
    return HAS_POSTGRES and bool(DATABASE_URL)


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    if _is_postgres():
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
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
                id SERIAL PRIMARY KEY,
                question TEXT,
                answer TEXT,
                options TEXT,
                winner_id BIGINT,
                winner_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS retos (
                id SERIAL PRIMARY KEY,
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
                id SERIAL PRIMARY KEY,
                reto_id INTEGER,
                user_id BIGINT,
                completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (reto_id) REFERENCES retos(id),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_trivia (
                id SERIAL PRIMARY KEY,
                question TEXT,
                correct_answer TEXT,
                option1 TEXT,
                option2 TEXT,
                option3 TEXT,
                category TEXT,
                created_at DATE DEFAULT CURRENT_DATE,
                answered_by BIGINT
            )
        """)
    else:
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
    db_type = "PostgreSQL" if _is_postgres() else "SQLite"
    print(f"✅ Base de datos conectada: {db_type}")


def get_user(user_id: int) -> Optional[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    if _is_postgres():
        cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
    else:
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def create_user(user_id: int, username: str) -> dict:
    conn = get_connection()
    cursor = conn.cursor()
    if _is_postgres():
        cursor.execute(
            "INSERT INTO users (user_id, username) VALUES (%s, %s) ON CONFLICT (user_id) DO NOTHING",
            (user_id, username),
        )
    else:
        cursor.execute(
            "INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)",
            (user_id, username),
        )
    conn.commit()
    conn.close()
    return get_user(user_id)


def update_score(user_id: int, points: int, username: str = "Unknown"):
    try:
        create_user(user_id, username)
        conn = get_connection()
        cursor = conn.cursor()
        if _is_postgres():
            cursor.execute(
                "UPDATE users SET total_score = total_score + %s WHERE user_id = %s",
                (points, user_id),
            )
        else:
            cursor.execute(
                "UPDATE users SET total_score = total_score + ? WHERE user_id = ?",
                (points, user_id),
            )
        conn.commit()
        conn.close()
        print(f"✅ Puntos actualizados: user={user_id}, +{points}")
    except Exception as e:
        print(f"❌ Error update_score: {e}")


def update_trivia_stats(user_id: int, correct: bool, username: str = "Unknown"):
    try:
        create_user(user_id, username)
        conn = get_connection()
        cursor = conn.cursor()
        if _is_postgres():
            if correct:
                cursor.execute(
                    """UPDATE users SET 
                       trivia_correct = trivia_correct + 1,
                       trivia_total = trivia_total + 1,
                       current_streak = current_streak + 1,
                       best_streak = GREATEST(best_streak, current_streak + 1)
                       WHERE user_id = %s""",
                    (user_id,),
                )
            else:
                cursor.execute(
                    "UPDATE users SET trivia_total = trivia_total + 1, current_streak = 0 WHERE user_id = %s",
                    (user_id,),
                )
        else:
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
        print(f"✅ Trivia stats actualizados: user={user_id}, correct={correct}")
    except Exception as e:
        print(f"❌ Error update_trivia_stats: {e}")


def checkin(user_id: int) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    if _is_postgres():
        cursor.execute("SELECT last_checkin FROM users WHERE user_id = %s", (user_id,))
    else:
        cursor.execute("SELECT last_checkin FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()

    today = datetime.now().date()

    if row and row["last_checkin"]:
        last = row["last_checkin"]
        if isinstance(last, str):
            last = datetime.strptime(last, "%Y-%m-%d").date()
        if last == today:
            conn.close()
            return False
        if (today - last).days > 1:
            if _is_postgres():
                cursor.execute("UPDATE users SET current_streak = 0 WHERE user_id = %s", (user_id,))
            else:
                cursor.execute("UPDATE users SET current_streak = 0 WHERE user_id = ?", (user_id,))

    if _is_postgres():
        cursor.execute(
            "UPDATE users SET last_checkin = %s WHERE user_id = %s",
            (today.isoformat(), user_id),
        )
    else:
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
    if _is_postgres():
        cursor.execute("SELECT * FROM users ORDER BY total_score DESC LIMIT %s", (limit,))
    else:
        cursor.execute("SELECT * FROM users ORDER BY total_score DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_trivia_leaderboard(limit: int = 10) -> list:
    conn = get_connection()
    cursor = conn.cursor()
    if _is_postgres():
        cursor.execute(
            """SELECT user_id, username, trivia_correct, trivia_total,
               CASE WHEN trivia_total > 0 THEN (trivia_correct * 100.0 / trivia_total) ELSE 0 END as accuracy
               FROM users WHERE trivia_total > 0
               ORDER BY trivia_correct DESC LIMIT %s""",
            (limit,),
        )
    else:
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
    if _is_postgres():
        cursor.execute(
            "INSERT INTO retos (title, description, reward_points, start_date, end_date) VALUES (%s, %s, %s, %s, %s) RETURNING id",
            (title, description, reward, start.isoformat(), end.isoformat()),
        )
        reto_id = cursor.fetchone()["id"]
    else:
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
    if _is_postgres():
        cursor.execute(
            "SELECT * FROM retos WHERE active = 1 AND end_date >= %s ORDER BY start_date DESC LIMIT 1",
            (today,),
        )
    else:
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
    if _is_postgres():
        cursor.execute(
            "SELECT * FROM reto_completions WHERE reto_id = %s AND user_id = %s",
            (reto_id, user_id),
        )
    else:
        cursor.execute(
            "SELECT * FROM reto_completions WHERE reto_id = ? AND user_id = ?",
            (reto_id, user_id),
        )
    if cursor.fetchone():
        conn.close()
        return False

    if _is_postgres():
        cursor.execute(
            "INSERT INTO reto_completions (reto_id, user_id) VALUES (%s, %s)",
            (reto_id, user_id),
        )
        cursor.execute(
            "UPDATE users SET retos_completed = retos_completed + 1 WHERE user_id = %s",
            (user_id,),
        )
    else:
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
    if _is_postgres():
        cursor.execute(
            "INSERT INTO daily_trivia (question, correct_answer, option1, option2, option3) VALUES (%s, %s, %s, %s, %s)",
            (question, correct, options[0], options[1], options[2]),
        )
    else:
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
    if _is_postgres():
        cursor.execute("SELECT * FROM daily_trivia WHERE created_at = %s", (today,))
    else:
        cursor.execute("SELECT * FROM daily_trivia WHERE created_at = ?", (today,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def mark_trivia_answered(trivia_id: int, user_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    if _is_postgres():
        cursor.execute(
            "UPDATE daily_trivia SET answered_by = %s WHERE id = %s",
            (user_id, trivia_id),
        )
    else:
        cursor.execute(
            "UPDATE daily_trivia SET answered_by = ? WHERE id = ?",
            (user_id, trivia_id),
        )
    conn.commit()
    conn.close()


def get_streak(user_id: int) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    if _is_postgres():
        cursor.execute("SELECT current_streak FROM users WHERE user_id = %s", (user_id,))
    else:
        cursor.execute("SELECT current_streak FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row["current_streak"] if row else 0


def get_total_score(user_id: int) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    if _is_postgres():
        cursor.execute("SELECT total_score FROM users WHERE user_id = %s", (user_id,))
    else:
        cursor.execute("SELECT total_score FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row["total_score"] if row else 0
