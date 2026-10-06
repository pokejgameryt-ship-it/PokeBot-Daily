"""Entry point para paneles de hosting que ejecutan `python app.py`
(FeatherPanel / Quaxly y otros). Equivale a `python main.py`:

solo conecta a Discord si este contenedor gana el lease de líder en Firebase.
"""

import asyncio

from main import _run_with_lease

if __name__ == "__main__":
    asyncio.run(_run_with_lease())
