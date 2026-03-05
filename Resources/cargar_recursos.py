"""
cargar_recursos.py — Carga profesores y horarios de todos los grupos de Resources/ en la API.

Uso:
    python cargar_recursos.py
    python cargar_recursos.py --url http://localhost:8000 --email admin@centro.es --password admin123
    python cargar_recursos.py --solo-profesores
    python cargar_recursos.py --solo-horarios

Combina automáticamente los *_profesores.json y *_horarios.json de todos los grupos.
Los profesores que aparecen en varios grupos (ej. Borja Bravo en 1MSS2 y 2MSS2) se crean una sola vez.
"""

import argparse
import json
import sys
from pathlib import Path

import httpx

DEFAULT_URL      = "http://localhost:8000"
DEFAULT_EMAIL    = "admin@centro.es"
DEFAULT_PASSWORD = "admin123"

HERE = Path(__file__).parent


def ok(msg: str)   -> None: print(f"  \033[32m[OK]\033[0m {msg}")
def warn(msg: str) -> None: print(f"  \033[33m[--]\033[0m {msg}")
def err(msg: str)  -> None: print(f"  \033[31m[!!]\033[0m {msg}")


def login(client: httpx.Client, email: str, password: str) -> str:
    print("\n[1/3] Login...")
    r = client.post("/api/auth/login", json={"email": email, "password": password})
    if r.status_code != 200:
        err(f"Login fallido ({r.status_code}): {r.text}")
        sys.exit(1)
    ok(f"Sesión iniciada como {email}")
    return r.json()["access_token"]


def cargar_profesores(client: httpx.Client) -> dict[str, int]:
    print("\n[2/3] Profesores...")

    # Consolidar todos los *_profesores.json sin duplicados de email
    vistos: dict[str, dict] = {}
    for path in sorted(HERE.glob("*_profesores.json")):
        grupo = path.stem.replace("_profesores", "")
        datos: list[dict] = json.loads(path.read_text(encoding="utf-8"))
        for p in datos:
            email = p["email"]
            if email not in vistos:
                vistos[email] = p
                print(f"    + {p['nombre']} {p['apellidos']} ({grupo})")
            else:
                print(f"    = {p['nombre']} {p['apellidos']} — ya visto en otro grupo, omitido")

    print(f"  {len(vistos)} profesores únicos encontrados en Resources/")

    # Obtener los ya existentes en la API
    email_to_id: dict[str, int] = {}
    r = client.get("/api/teachers")
    if r.status_code == 200:
        for t in r.json():
            email_to_id[t["email"]] = t["id"]

    # Crear los que no existen
    for email, p in vistos.items():
        if email in email_to_id:
            warn(f"Ya existe en BD: {p['nombre']} {p['apellidos']} — omitido")
            continue
        payload = {k: v for k, v in p.items() if not k.startswith("_")}
        r = client.post("/api/teachers", json=payload)
        if r.status_code == 201:
            data = r.json()
            email_to_id[data["email"]] = data["id"]
            ok(f"Creado: {data['nombre']} {data['apellidos']} (id={data['id']})")
        elif r.status_code == 409:
            warn(f"Duplicado (409): {email}")
        else:
            err(f"Error creando {email} ({r.status_code}): {r.text}")

    return email_to_id


def cargar_horarios(client: httpx.Client, email_to_id: dict[str, int]) -> None:
    print("\n[3/3] Horarios...")

    for path in sorted(HERE.glob("*_horarios.json")):
        grupo = path.stem.replace("_horarios", "")
        print(f"\n  Grupo {grupo}:")
        horarios: dict[str, list] = json.loads(path.read_text(encoding="utf-8"))

        for email, tramos in horarios.items():
            if email.startswith("_"):
                continue
            teacher_id = email_to_id.get(email)
            if teacher_id is None:
                warn(f"Profesor no encontrado en BD: {email} — horario omitido")
                continue

            # El PUT de horario es ACUMULATIVO si el profesor ya tiene tramos de otro grupo.
            # Primero obtenemos el horario actual y le añadimos los nuevos tramos.
            r_get = client.get(f"/api/teachers/{teacher_id}/schedule")
            tramos_actuales = r_get.json() if r_get.status_code == 200 else []

            # Detectar solapamientos (mismo dia+tramo ya cargado)
            claves_existentes = {(t["dia_semana"], t["tramo_horario"]) for t in tramos_actuales}
            tramos_nuevos = [t for t in tramos if (t["dia_semana"], t["tramo_horario"]) not in claves_existentes]
            tramos_solapados = len(tramos) - len(tramos_nuevos)

            payload = tramos_actuales + tramos_nuevos
            r = client.put(f"/api/teachers/{teacher_id}/schedule", json=payload)

            if r.status_code == 200:
                msg = f"{email} — {len(tramos_nuevos)} tramos añadidos"
                if tramos_solapados:
                    msg += f" ({tramos_solapados} solapados ignorados)"
                ok(msg)
            else:
                err(f"Error en horario de {email} ({r.status_code}): {r.text}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Carga grupos de Resources/ en hernaniZaintzak")
    parser.add_argument("--url",             default=DEFAULT_URL)
    parser.add_argument("--email",           default=DEFAULT_EMAIL)
    parser.add_argument("--password",        default=DEFAULT_PASSWORD)
    parser.add_argument("--solo-profesores", action="store_true")
    parser.add_argument("--solo-horarios",   action="store_true")
    args = parser.parse_args()

    todo = not any([args.solo_profesores, args.solo_horarios])

    grupos = [p.stem.replace("_profesores", "") for p in sorted(HERE.glob("*_profesores.json"))]
    print(f"\nhernaniZaintzak — Carga de Resources/")
    print(f"API: {args.url}")
    print(f"Grupos detectados: {', '.join(grupos)}")

    with httpx.Client(base_url=args.url, timeout=60) as client:
        token = login(client, args.email, args.password)
        client.headers["Authorization"] = f"Bearer {token}"

        email_to_id: dict[str, int] = {}

        if todo or args.solo_profesores:
            email_to_id = cargar_profesores(client)
        else:
            r = client.get("/api/teachers")
            if r.status_code == 200:
                for t in r.json():
                    email_to_id[t["email"]] = t["id"]

        if todo or args.solo_horarios:
            cargar_horarios(client, email_to_id)

    print("\n\033[32mCarga completada.\033[0m\n")


if __name__ == "__main__":
    main()
