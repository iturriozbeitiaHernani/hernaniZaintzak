"""
cargar_datos.py — Carga masiva de datos en hernaniZaintzak vía API REST.

Requisitos:
    pip install httpx

Uso:
    # Desde la carpeta ejemplos/
    python cargar_datos.py

    # Opciones:
    python cargar_datos.py --solo-profesores
    python cargar_datos.py --solo-horarios
    python cargar_datos.py --solo-ausencias
    python cargar_datos.py --solo-config
    python cargar_datos.py --url http://mi-servidor:8000 --email admin@centro.es --password mipass

El script:
  1. Hace login con las credenciales de administrador
  2. Carga profesores (omite los que ya existan por email)
  3. Carga horarios de cada profesor
  4. (Opcional) Registra ausencias de ejemplo
  5. (Opcional) Aplica la configuración del centro
"""

import json
import sys
import argparse
from pathlib import Path

import httpx

# ─── Configuración por defecto ────────────────────────────────────────────────
DEFAULT_URL      = "http://localhost:8000"
DEFAULT_EMAIL    = "admin@centro.es"
DEFAULT_PASSWORD = "admin123"

HERE = Path(__file__).parent


# ─── Helpers ──────────────────────────────────────────────────────────────────
def ok(msg: str) -> None:
    print(f"  \033[32m✓\033[0m {msg}")

def warn(msg: str) -> None:
    print(f"  \033[33m⚠\033[0m {msg}")

def err(msg: str) -> None:
    print(f"  \033[31m✗\033[0m {msg}")

def load_json(filename: str) -> dict | list:
    path = HERE / filename
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ─── Pasos de carga ───────────────────────────────────────────────────────────
def login(client: httpx.Client, email: str, password: str) -> str:
    print("\n[1/5] Login...")
    r = client.post("/api/auth/login", json={"email": email, "password": password})
    if r.status_code != 200:
        err(f"Login fallido ({r.status_code}): {r.text}")
        sys.exit(1)
    token = r.json()["access_token"]
    ok(f"Sesión iniciada como {email}")
    return token


def cargar_profesores(client: httpx.Client) -> dict[str, int]:
    """Devuelve mapa email → id de los profesores creados o ya existentes."""
    print("\n[2/5] Profesores...")
    profesores = load_json("profesores.json")
    email_to_id: dict[str, int] = {}

    # Obtener los ya existentes
    existing_r = client.get("/api/teachers")
    if existing_r.status_code == 200:
        for t in existing_r.json():
            email_to_id[t["email"]] = t["id"]

    for p in profesores:
        if p["email"] in email_to_id:
            warn(f"Ya existe: {p['nombre']} {p['apellidos']} ({p['email']}) — omitido")
            continue

        # Eliminar campos que empiezan por _ (comentarios del JSON)
        payload = {k: v for k, v in p.items() if not k.startswith("_")}
        r = client.post("/api/teachers", json=payload)

        if r.status_code == 201:
            data = r.json()
            email_to_id[data["email"]] = data["id"]
            ok(f"Creado: {data['nombre']} {data['apellidos']} (id={data['id']})")
        elif r.status_code == 409:
            warn(f"Duplicado: {p['email']}")
        else:
            err(f"Error creando {p['email']} ({r.status_code}): {r.text}")

    return email_to_id


def cargar_horarios(client: httpx.Client, email_to_id: dict[str, int]) -> None:
    print("\n[3/5] Horarios...")
    horarios: dict[str, list] = load_json("horarios.json")

    for email, tramos in horarios.items():
        if email.startswith("_"):
            continue  # campo de referencia

        teacher_id = email_to_id.get(email)
        if teacher_id is None:
            warn(f"Profesor no encontrado en el sistema: {email} — horario omitido")
            continue

        # Eliminar campos de comentario de cada tramo
        payload = [{k: v for k, v in t.items() if not k.startswith("_")} for t in tramos]
        r = client.put(f"/api/teachers/{teacher_id}/schedule", json=payload)

        if r.status_code == 200:
            ok(f"Horario cargado: {email} ({len(tramos)} tramos)")
        else:
            err(f"Error en horario de {email} ({r.status_code}): {r.text}")


def cargar_ausencias(client: httpx.Client, email_to_id: dict[str, int]) -> None:
    print("\n[4/5] Ausencias de ejemplo...")
    ausencias = load_json("ausencias.json")

    for a in ausencias:
        email = a.get("teacher_email")
        teacher_id = email_to_id.get(email)
        if teacher_id is None:
            warn(f"Profesor no encontrado: {email} — ausencia omitida")
            continue

        payload = {
            "teacher_id": teacher_id,
            "fecha_inicio": a["fecha_inicio"],
            "fecha_fin":    a["fecha_fin"],
            "motivo":       a.get("motivo", ""),
        }
        r = client.post("/api/absences", json=payload)

        if r.status_code == 201:
            ok(f"Ausencia registrada: {email} del {a['fecha_inicio']} al {a['fecha_fin']}")
        elif r.status_code == 409:
            warn(f"Ausencia ya existe o solapada: {email} {a['fecha_inicio']}")
        else:
            err(f"Error en ausencia de {email} ({r.status_code}): {r.text}")


def cargar_config(client: httpx.Client) -> None:
    print("\n[5/5] Configuración del centro...")
    config_raw: dict = load_json("config.json")

    # Eliminar campos de comentario
    payload = {k: v for k, v in config_raw.items() if not k.startswith("_")}

    r = client.put("/api/config", json=payload)
    if r.status_code == 200:
        ok(f"Configuración actualizada: {payload.get('nombre_centro', '')}")
    else:
        err(f"Error actualizando config ({r.status_code}): {r.text}")


# ─── Main ─────────────────────────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(description="Carga masiva de datos en hernaniZaintzak")
    parser.add_argument("--url",      default=DEFAULT_URL,      help="URL base de la API")
    parser.add_argument("--email",    default=DEFAULT_EMAIL,    help="Email del administrador")
    parser.add_argument("--password", default=DEFAULT_PASSWORD, help="Contraseña del administrador")
    parser.add_argument("--solo-profesores", action="store_true")
    parser.add_argument("--solo-horarios",   action="store_true")
    parser.add_argument("--solo-ausencias",  action="store_true")
    parser.add_argument("--solo-config",     action="store_true")
    args = parser.parse_args()

    todo = not any([args.solo_profesores, args.solo_horarios,
                    args.solo_ausencias, args.solo_config])

    print(f"\nhernaniZaintzak — Carga masiva de datos")
    print(f"API: {args.url}")

    with httpx.Client(base_url=args.url, timeout=60) as client:
        token = login(client, args.email, args.password)
        client.headers["Authorization"] = f"Bearer {token}"

        email_to_id: dict[str, int] = {}

        if todo or args.solo_profesores:
            email_to_id = cargar_profesores(client)
        else:
            # Resolver IDs aunque no carguemos profesores
            r = client.get("/api/teachers")
            if r.status_code == 200:
                for t in r.json():
                    email_to_id[t["email"]] = t["id"]

        if todo or args.solo_horarios:
            cargar_horarios(client, email_to_id)

        if todo or args.solo_ausencias:
            cargar_ausencias(client, email_to_id)

        if todo or args.solo_config:
            cargar_config(client)

    print("\n\033[32mCarga completada.\033[0m\n")


if __name__ == "__main__":
    main()
