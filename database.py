import os
import json
from datetime import datetime, timedelta
from typing import Optional

import firebase_admin
from firebase_admin import credentials, db

FIREBASE_DB_URL = "https://pokebot-1c544-default-rtdb.europe-west1.firebasedatabase.app/"

_cred = None
_SERVICE_ACCOUNT_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "firebase-service-account.json"
)

_service_account_json = os.getenv("FIREBASE_SERVICE_ACCOUNT", "")

if _service_account_json:
    try:
        service_account_info = json.loads(_service_account_json)
        _cred = credentials.Certificate(service_account_info)
        firebase_admin.initialize_app(_cred, {"databaseURL": FIREBASE_DB_URL})
        print("[OK] Firebase conectado (via env)")
    except Exception as e:
        print(f"[ERROR] Firebase env: {e}")
elif os.path.exists(_SERVICE_ACCOUNT_PATH):
    _cred = credentials.Certificate(_SERVICE_ACCOUNT_PATH)
    firebase_admin.initialize_app(_cred, {"databaseURL": FIREBASE_DB_URL})
    print("[OK] Firebase conectado (via archivo)")
else:
    print("[WARN] Firebase no configurado")


def _users_ref():
    return db.reference("users")


def _trivia_ref():
    return db.reference("trivia_history")


def _daily_ref():
    return db.reference("daily_trivia")


def _retos_ref():
    return db.reference("retos")


def _reto_completions_ref():
    return db.reference("reto_completions")


def init_db():
    print("[OK] Base de datos conectada: Firebase Realtime Database")


def get_user(user_id: int) -> Optional[dict]:
    ref = _users_ref().child(str(user_id))
    data = ref.get()
    if data:
        data["user_id"] = user_id
    return data


def create_user(user_id: int, username: str) -> dict:
    ref = _users_ref().child(str(user_id))
    existing = ref.get()
    if not existing:
        ref.set({
            "username": username,
            "total_score": 0,
            "trivia_correct": 0,
            "trivia_total": 0,
            "current_streak": 0,
            "best_streak": 0,
            "last_checkin": None,
            "last_trivia_date": None,
            "retos_completed": 0,
        })
    else:
        ref.update({"username": username})
    return get_user(user_id)


def update_score(user_id: int, points: int, username: str = "Unknown"):
    try:
        create_user(user_id, username)
        ref = _users_ref().child(str(user_id))
        current = ref.child("total_score").get() or 0
        ref.update({"total_score": current + points})
        print(f"[OK] Puntos actualizados: user={user_id}, +{points}")
    except Exception as e:
        print(f"[ERROR] update_score: {e}")


def update_trivia_stats(user_id: int, correct: bool, username: str = "Unknown"):
    try:
        create_user(user_id, username)
        ref = _users_ref().child(str(user_id))
        data = ref.get()
        today = datetime.now().date().isoformat()

        old_streak = data.get("current_streak", 0)
        last_trivia_date = data.get("last_trivia_date")

        if correct:
            if last_trivia_date:
                last_date = datetime.strptime(last_trivia_date, "%Y-%m-%d").date()
                days_since = (datetime.now().date() - last_date).days
            else:
                days_since = 999

            if days_since == 1:
                new_streak = old_streak + 1
            elif days_since == 0:
                new_streak = old_streak
            else:
                new_streak = 1

            ref.update({
                "trivia_correct": (data.get("trivia_correct", 0)) + 1,
                "trivia_total": (data.get("trivia_total", 0)) + 1,
                "current_streak": new_streak,
                "best_streak": max(data.get("best_streak", 0), new_streak),
                "last_trivia_date": today,
            })
        else:
            new_streak = 0
            ref.update({
                "trivia_total": (data.get("trivia_total", 0)) + 1,
                "current_streak": 0,
            })

        print(f"[OK] Trivia stats actualizados: user={user_id}, correct={correct}")
        return {"old_streak": old_streak, "new_streak": new_streak}
    except Exception as e:
        print(f"[ERROR] update_trivia_stats: {e}")
        return {"old_streak": 0, "new_streak": 0}


def get_users_needing_reminder():
    today = datetime.now().date()
    users = _users_ref().get() or {}
    result = []
    for uid, data in users.items():
        streak = data.get("current_streak", 0)
        last_date_str = data.get("last_trivia_date")
        if streak > 0 and last_date_str:
            last_date = datetime.strptime(last_date_str, "%Y-%m-%d").date()
            if last_date < today:
                result.append({
                    "user_id": int(uid),
                    "username": data.get("username", "Unknown"),
                    "current_streak": streak,
                })
    return result


def reset_stale_streaks():
    two_days_ago = (datetime.now().date() - timedelta(days=2)).isoformat()
    users = _users_ref().get() or {}
    updates = {}
    for uid, data in users.items():
        streak = data.get("current_streak", 0)
        last_date_str = data.get("last_trivia_date")
        if streak > 0 and last_date_str and last_date_str < two_days_ago:
            updates[f"{uid}/current_streak"] = 0
    if updates:
        _users_ref().update(updates)


def checkin(user_id: int) -> bool:
    ref = _users_ref().child(str(user_id))
    data = ref.get()
    today = datetime.now().date()

    if data and data.get("last_checkin"):
        last = datetime.strptime(data["last_checkin"], "%Y-%m-%d").date()
        if last == today:
            return False
        if (today - last).days > 1:
            ref.update({"current_streak": 0})

    ref.update({"last_checkin": today.isoformat()})
    return True


def get_leaderboard(limit: int = 10) -> list:
    users = _users_ref().get() or {}
    lista = []
    for uid, data in users.items():
        entry = dict(data)
        entry["user_id"] = int(uid)
        lista.append(entry)
    lista.sort(key=lambda x: x.get("total_score", 0), reverse=True)
    return lista[:limit]


def get_trivia_leaderboard(limit: int = 10) -> list:
    users = _users_ref().get() or {}
    lista = []
    for uid, data in users.items():
        if data.get("trivia_total", 0) > 0:
            accuracy = (data["trivia_correct"] / data["trivia_total"]) * 100
            entry = dict(data)
            entry["user_id"] = int(uid)
            entry["accuracy"] = accuracy
            lista.append(entry)
    lista.sort(key=lambda x: x.get("trivia_correct", 0), reverse=True)
    return lista[:limit]


def create_reto(title: str, description: str, reward: int, days: int = 7) -> int:
    start = datetime.now().date()
    end = start + timedelta(days=days)
    ref = _retos_ref().push()
    ref.set({
        "title": title,
        "description": description,
        "reward_points": reward,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "active": 1,
    })
    return int(ref.key.lstrip("-"))


def get_active_reto() -> Optional[dict]:
    today = datetime.now().date().isoformat()
    retos = _retos_ref().get() or {}
    for rid, data in retos.items():
        if data.get("active") == 1 and data.get("end_date", "") >= today:
            return dict(data)
    return None


def complete_reto(user_id: int, reto_id: int) -> bool:
    ref = _reto_completions_ref().child(str(reto_id)).child(str(user_id))
    if ref.get():
        return False
    ref.set({"completed_at": datetime.now().isoformat()})

    user_ref = _users_ref().child(str(user_id))
    current = user_ref.child("retos_completed").get() or 0
    user_ref.update({"retos_completed": current + 1})
    return True


def save_trivia_question(question: str, correct: str, options: list):
    today = datetime.now().date().isoformat()
    ref = _daily_ref().push()
    ref.set({
        "question": question,
        "correct_answer": correct,
        "option1": options[0],
        "option2": options[1],
        "option3": options[2],
        "created_at": today,
        "answered_by": None,
    })


def get_daily_trivia() -> Optional[dict]:
    today = datetime.now().date().isoformat()
    trivia = _daily_ref().get() or {}
    for tid, data in trivia.items():
        if data.get("created_at") == today:
            return dict(data)
    return None


def mark_trivia_answered(trivia_id: int, user_id: int):
    today = datetime.now().date().isoformat()
    trivia = _daily_ref().get() or {}
    for tid, data in trivia.items():
        if data.get("created_at") == today:
            _daily_ref().child(tid).update({"answered_by": user_id})
            break


def get_streak(user_id: int) -> int:
    data = _users_ref().child(str(user_id)).get()
    return data.get("current_streak", 0) if data else 0


def get_total_score(user_id: int) -> int:
    data = _users_ref().child(str(user_id)).get()
    return data.get("total_score", 0) if data else 0
