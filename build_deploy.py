"""Empaqueta el bot para subirlo a un host gratuito (zip sin secretos).

Uso:
    python build_deploy.py                  # zip SEGURO (sin .env) -> pokebot-deploy.zip
    python build_deploy.py --with-secrets   # zip CON .env incluido -> pokebot-deploy-full.zip
                                             # (para re-despliegues: nunca re-teclear secretos)

Salida: deploy/pokebot-deploy.zip [-full]
"""

import os
import sys
import zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(ROOT, "deploy")

# Exclusiones (nunca subir secretos ni datos locales)
EXCLUDE_DIRS = {"__pycache__", "logs", "backups", "deploy", "tests", ".git", "venv", ".venv", ".pytest_cache"}
EXCLUDE_FILES = {
    ".env",
    ".token",
    "firebase-service-account.json",
    ".gitignore",
    ".dockerignore",
    "reset_data.py",
    "check_trivia.py",
    "iniciar.bat",
    "bot_silent.vbs",
    "install_task.ps1",
    "backup_daily.bat",
    "MEMORY.md",
    "coverage.xml",
    ".coverage",
}
EXCLUDE_SUFFIX = (".pyc", ".key", ".pem")


def should_include(path: str, with_secrets: bool) -> bool:
    rel = os.path.relpath(path, ROOT)
    parts = rel.split(os.sep)
    name = parts[-1]
    if any(d in EXCLUDE_DIRS for d in parts[:-1]):
        return False
    if with_secrets and name == ".env":
        return True
    if name in EXCLUDE_FILES:
        return False
    if name.endswith(EXCLUDE_SUFFIX):
        return False
    return True


def main():
    with_secrets = "--with-secrets" in sys.argv[1:]
    os.makedirs(OUT_DIR, exist_ok=True)
    out_zip = os.path.join(OUT_DIR, "pokebot-deploy-full.zip" if with_secrets else "pokebot-deploy.zip")
    count = 0
    with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for base, dirs, files in os.walk(ROOT):
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            for f in files:
                p = os.path.join(base, f)
                if should_include(p, with_secrets):
                    arc = os.path.relpath(p, ROOT)
                    zf.write(p, arc)
                    count += 1
    size = os.path.getsize(out_zip)
    print(f"[OK] {out_zip} ({count} archivos, {size} bytes)")
    if with_secrets:
        print("[AVISO] Zip CON secretos (.env incluido). NO lo subas a ningún sitio público.")
    else:
        print("[INFO] Verifica que NO contiene: .env, .token, firebase-service-account.json")
    with zipfile.ZipFile(out_zip) as zf:
        names = zf.namelist()
        for bad in (".env", ".token", "firebase-service-account.json"):
            hits = [n for n in names if n.endswith(bad) and not n.endswith(".example")]
            if hits and not with_secrets:
                print(f"[ERROR] Contiene archivo prohibido: {hits}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
