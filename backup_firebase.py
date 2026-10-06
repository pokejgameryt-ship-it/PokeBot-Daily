"""Backup y restore de la base de datos Firebase Realtime Database.

Uso:
    python backup_firebase.py                 # backup completo a backups/
    python backup_firebase.py --test          # prueba de integridad (dump + parseo)
    python backup_firebase.py --restore FILE  # restaura desde un JSON de backup
    python backup_firebase.py --list          # lista backups disponibles

Se conservan los últimos 14 backups (BACKUP_KEEP por defecto).
"""

import argparse
import glob
import json
import os
import sys
from datetime import datetime

BACKUP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backups")
BACKUP_KEEP = 14


def _get_root():
    import database  # noqa: F401  (inicializa la app Firebase)
    from firebase_admin import db

    return db.reference("/")


def backup() -> str:
    data = _get_root().get()
    if data is None:
        data = {}

    os.makedirs(BACKUP_DIR, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    path = os.path.join(BACKUP_DIR, f"firebase_{stamp}.json")

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)

    _prune_old()
    size = os.path.getsize(path)
    print(f"[OK] Backup creado: {path} ({size} bytes)")
    return path


def _prune_old():
    files = sorted(glob.glob(os.path.join(BACKUP_DIR, "firebase_*.json")))
    for old in files[:-BACKUP_KEEP]:
        os.remove(old)
        print(f"[INFO] Backup antiguo eliminado: {os.path.basename(old)}")


def test_integrity() -> bool:
    path = backup()
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"[OK] Integridad verificada: {len(data)} nodos raíz")
        return True
    except Exception as e:
        print(f"[ERROR] Backup corrupto: {e}")
        return False


def restore(path: str) -> bool:
    if not os.path.exists(path):
        print(f"[ERROR] No existe: {path}")
        return False

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    answer = input(
        f"⚠️  Esto SOBRESCRIBIRÁ toda la BD con {os.path.basename(path)} "
        f"({len(data)} nodos raíz). ¿Continuar? [s/N]: "
    ).strip().lower()
    if answer not in ("s", "si", "sí", "y", "yes"):
        print("[INFO] Restore cancelado.")
        return False

    # Backup de seguridad antes de restaurar
    print("[INFO] Creando backup de seguridad previo al restore...")
    backup()

    _get_root().set(data)
    print(f"[OK] Restaurado desde {path}")
    return True


def list_backups():
    files = sorted(glob.glob(os.path.join(BACKUP_DIR, "firebase_*.json")))
    if not files:
        print("[INFO] No hay backups.")
        return
    for f in files:
        print(f"  {os.path.basename(f)}  ({os.path.getsize(f)} bytes)")


def main():
    parser = argparse.ArgumentParser(description="Backup/restore Firebase")
    parser.add_argument("--test", action="store_true", help="backup + verificar integridad")
    parser.add_argument("--restore", metavar="FILE", help="restaurar desde JSON")
    parser.add_argument("--list", action="store_true", help="listar backups")
    args = parser.parse_args()

    if args.list:
        list_backups()
        return 0
    if args.restore:
        return 0 if restore(args.restore) else 1
    if args.test:
        return 0 if test_integrity() else 1

    backup()
    return 0


if __name__ == "__main__":
    sys.exit(main())
