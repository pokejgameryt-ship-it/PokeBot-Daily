import os
import json
import requests
from datetime import datetime

FIREBASE_DB_URL = "https://pokebot-1c544-default-rtdb.europe-west1.firebasedatabase.app/"

# Get service account
SERVICE_ACCOUNT_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "firebase-service-account.json"
)

_service_account_json = os.getenv("FIREBASE_SERVICE_ACCOUNT", "")

if _service_account_json:
    service_account_info = json.loads(_service_account_json)
elif os.path.exists(SERVICE_ACCOUNT_PATH):
    with open(SERVICE_ACCOUNT_PATH) as f:
        service_account_info = json.load(f)
else:
    print("ERROR: No se encontró la cuenta de servicio de Firebase")
    exit(1)

# Get access token
import firebase_admin
from firebase_admin import credentials, db

cred = credentials.Certificate(service_account_info)
firebase_admin.initialize_app(cred, {"databaseURL": FIREBASE_DB_URL})

today = datetime.now().date().isoformat()
print(f"Fecha de hoy: {today}")

# Get daily trivia
ref = db.reference("daily_trivia")
trivia = ref.get() or {}

found = False
for tid, data in trivia.items():
    if data.get("created_at") == today:
        print(f"Encontrada trivia de hoy: {tid}")
        print(f"  Pregunta: {data.get('question', 'N/A')}")
        print(f"  Respuesta correcta: {data.get('correct_answer', 'N/A')}")
        print(f"  Opciones: {data.get('option1', 'N/A')}, {data.get('option2', 'N/A')}, {data.get('option3', 'N/A')}")
        
        # Delete it
        ref.child(tid).delete()
        print(f"  Trivia eliminada correctamente")
        found = True
        break

if not found:
    print("No se encontró trivia de hoy")

print("\nListo! Ahora ejecuta !trivia en Discord para generar una nueva pregunta.")
