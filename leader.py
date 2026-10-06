"""Lease de líder en Firebase Realtime Database.

Garantiza que UNA sola instancia del bot (PC local o host gratuito) esté
activa a la vez. La instancia líder escribe su ID en `leader/` con un
`expires_at` (TTL 90s). Cada 30s se renueva; si la líder muere, la otra
instancia toma el control en ≤90s.

Uso:
    if leader.acquire_lease(): ...      # intentar ser líder (sync)
    status = leader.renew_lease()       # True / False (perdido) / None (error red)
    leader.release_lease()              # liberar al apagarse
    leader.is_leader()                  # comprobar propiedad actual
"""

import logging
import os
import socket
import time

logger = logging.getLogger("leader")

LEASE_TTL_MS = 90_000          # el lease caduca a los 90s sin renovar
RENEW_INTERVAL_S = 30          # cada cuánto se renueva
WAIT_INTERVAL_S = 30           # esperar entre intentos si otro es líder

INSTANCE_ID = os.getenv("INSTANCE_ID") or socket.gethostname()
HOSTNAME = socket.gethostname()


def _now_ms() -> int:
    return int(time.time() * 1000)


def _leader_ref():
    import database  # noqa: F401  (inicializa la app Firebase)
    from firebase_admin import db

    return db.reference("leader")


def _new_claim(now_ms: int) -> dict:
    return {
        "id": INSTANCE_ID,
        "hostname": HOSTNAME,
        "expires_at": now_ms + LEASE_TTL_MS,
        "renewed_at": now_ms,
    }


def claim(current, now_ms: int) -> dict:
    """Decide si INSTANCE_ID puede tomar/refrescar el lease (función pura)."""
    if current is None:
        return _new_claim(now_ms)
    try:
        expires = int(current.get("expires_at", 0) or 0)
    except (TypeError, ValueError):
        expires = 0
    if current.get("id") == INSTANCE_ID or expires <= now_ms:
        return _new_claim(now_ms)
    return current


def release_claim(current, now_ms: int) -> dict:
    """Libera el lease solo si somos los poseedores (función pura)."""
    if current is None:
        return {"id": None, "expires_at": 0}
    if current.get("id") == INSTANCE_ID:
        return {"id": None, "expires_at": 0}
    return current


def lease_is_valid(data, now_ms: int | None = None) -> bool:
    """True si `data` es un lease vigente (no caducado) de cualquier instancia."""
    if not isinstance(data, dict) or not data.get("id"):
        return False
    if now_ms is None:
        now_ms = _now_ms()
    try:
        return int(data.get("expires_at", 0) or 0) > now_ms
    except (TypeError, ValueError):
        return False


def _transaction(update_fn) -> dict | None:
    try:
        result = _leader_ref().transaction(update_fn)
        return result if isinstance(result, dict) else None
    except Exception as e:
        logger.exception("Transacción de lease falló: %s", e)
        return None


def acquire_lease() -> bool:
    """Intenta tomar el lease. True si somos líderes tras la operación."""
    # Fast-path: si otro mantiene un lease vigente, no escribir en BD
    try:
        current = _leader_ref().get()
    except Exception as e:
        logger.exception("Error leyendo lease: %s", e)
        return False
    now = _now_ms()
    if (
        isinstance(current, dict)
        and current.get("id")
        and current.get("id") != INSTANCE_ID
        and lease_is_valid(current, now)
    ):
        logger.info("Otra instancia posee el lease: %s", current.get("id"))
        return False

    result = _transaction(lambda c: claim(c, _now_ms()))
    if result is None:
        return False
    got = result.get("id") == INSTANCE_ID
    if got:
        logger.info("Lease de líder adquirido/renovado (%s)", INSTANCE_ID)
    else:
        logger.info("Otra instancia posee el lease: %s", result.get("id"))
    return got


def renew_lease() -> bool | None:
    """Renueva el lease.

    Returns:
        True  -> renovado correctamente (seguimos líderes)
        False -> LO DIMOS: otra instancia es líder ahora (debemos parar)
        None  -> error de red/desconocido (no parar por esto)
    """
    def _update(current):
        return claim(current, _now_ms())

    result = _transaction(_update)
    if result is None:
        return None  # error de red: no decidir en base a esto
    return result.get("id") == INSTANCE_ID


def release_lease() -> None:
    """Libera el lease si lo poseemos (llamar al apagarse limpio)."""
    def _update(current):
        return release_claim(current, _now_ms())

    _transaction(_update)
    logger.info("Lease liberado (%s)", INSTANCE_ID)


def is_leader() -> bool:
    """True si este proceso posee actualmente un lease vigente."""
    try:
        data = _leader_ref().get()
    except Exception as e:
        logger.exception("Error leyendo lease: %s", e)
        return False
    return isinstance(data, dict) and data.get("id") == INSTANCE_ID and lease_is_valid(data)
