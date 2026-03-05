"""
generar_jsons.py — Genera JSON de carga a partir de ficheros .md de Resources.

Uso:
    python generar_jsons.py              # procesa todos los .md de esta carpeta
    python generar_jsons.py 1MSS2.md     # procesa solo ese fichero

Tipos de fichero soportados:
    calendario.md   -> calendario.json  (festivos + vacaciones)
    {GRUPO}.md      -> {GRUPO}_profesores.json + {GRUPO}_horarios.json

Formato de calendario.md:
    ## Festivos    -> tabla con columnas: Fecha, Descripcion, Confirmado
    ## Vacaciones  -> tabla con columnas: Inicio, Fin, Descripcion

Formato de ficheros de grupo (ej. 1MSS2.md):
    ## Profesores       -> tabla: Nombre, Apellidos, Email, Especialidades, Max sust/semana, Notas
    ## Horario semanal  -> tabla: Dia, Tramo, Asignatura, Email, Aula
"""

import json
import re
import sys
from pathlib import Path


MD_IGNORADOS = {"README"}
MD_CALENDARIO = "calendario"


def parse_tabla_md(lineas: list[str]) -> list[dict]:
    """Parsea una tabla markdown y devuelve lista de dicts."""
    filas = []
    cabeceras = None
    for linea in lineas:
        linea = linea.strip()
        if not linea.startswith("|"):
            break
        celdas = [c.strip() for c in linea.split("|")[1:-1]]
        if cabeceras is None:
            cabeceras = celdas
        elif re.match(r"^[\s|:\-]+$", linea):
            continue  # fila separadora
        else:
            filas.append(dict(zip(cabeceras, celdas)))
    return filas


def extraer_secciones(contenido: str) -> dict[str, list[str]]:
    """Divide el markdown en secciones ## y devuelve {nombre: [líneas]}."""
    secciones: dict[str, list[str]] = {}
    seccion_actual = None
    lineas_actuales: list[str] = []

    for linea in contenido.splitlines():
        if linea.startswith("## "):
            if seccion_actual is not None:
                secciones[seccion_actual] = lineas_actuales
            seccion_actual = linea[3:].strip()
            lineas_actuales = []
        else:
            lineas_actuales.append(linea)

    if seccion_actual is not None:
        secciones[seccion_actual] = lineas_actuales

    return secciones


def primera_tabla(lineas: list[str]) -> int | None:
    return next((i for i, l in enumerate(lineas) if l.strip().startswith("|")), None)


# ── Calendario ────────────────────────────────────────────────────────────────

def generar_calendario(md_path: Path) -> None:
    contenido = md_path.read_text(encoding="utf-8")
    secciones = extraer_secciones(contenido)

    # Resumen del curso
    resumen = {}
    lineas_res = secciones.get("Resumen del curso", [])
    idx = primera_tabla(lineas_res)
    if idx is not None:
        for fila in parse_tabla_md(lineas_res[idx:]):
            clave = fila.get("Campo", "").strip()
            valor = fila.get("Valor", "").strip()
            if clave == "Inicio curso":
                resumen["inicio_curso"] = valor
            elif clave == "Fin curso":
                resumen["fin_curso"] = valor
            elif clave == "Total dias lectivos":
                try:
                    resumen["dias_lectivos"] = int(valor)
                except ValueError:
                    pass

    # Festivos
    festivos = []
    lineas_fes = secciones.get("Festivos", [])
    idx = primera_tabla(lineas_fes)
    if idx is not None:
        for fila in parse_tabla_md(lineas_fes[idx:]):
            fecha = fila.get("Fecha", "").strip()
            if not fecha or not re.match(r"\d{4}-\d{2}-\d{2}", fecha):
                continue
            festivos.append({
                "fecha": fecha,
                "descripcion": fila.get("Descripcion", "").strip(),
                "confirmado": fila.get("Confirmado", "pendiente").strip() == "si",
            })

    # Vacaciones
    vacaciones = []
    lineas_vac = secciones.get("Vacaciones", [])
    idx = primera_tabla(lineas_vac)
    if idx is not None:
        for fila in parse_tabla_md(lineas_vac[idx:]):
            inicio = fila.get("Inicio", "").strip()
            fin = fila.get("Fin", "").strip()
            if not inicio or not fin:
                continue
            vacaciones.append({
                "inicio": inicio,
                "fin": fin,
                "descripcion": fila.get("Descripcion", "").strip(),
            })

    calendario_json = {
        **resumen,
        "festivos": festivos,
        "vacaciones": vacaciones,
    }

    ruta = md_path.parent / "calendario.json"
    ruta.write_text(json.dumps(calendario_json, ensure_ascii=False, indent=2), encoding="utf-8")

    n_conf = sum(1 for f in festivos if f["confirmado"])
    n_pend = len(festivos) - n_conf
    print(f"  OK calendario.json  -  {len(festivos)} festivos ({n_conf} confirmados, {n_pend} pendientes), {len(vacaciones)} periodos de vacaciones")


# ── Grupos (profesores + horarios) ────────────────────────────────────────────

def generar_grupo(md_path: Path) -> None:
    grupo = md_path.stem
    contenido = md_path.read_text(encoding="utf-8")
    secciones = extraer_secciones(contenido)

    # Profesores
    profesores_json: list[dict] = []
    lineas_prof = secciones.get("Profesores", [])
    idx = primera_tabla(lineas_prof)
    if idx is not None:
        for fila in parse_tabla_md(lineas_prof[idx:]):
            esp_raw = fila.get("Especialidades", "")
            especialidades = [e.strip() for e in esp_raw.split(",") if e.strip()]
            try:
                max_sust = int(fila.get("Max sust/semana", "2").strip())
            except ValueError:
                max_sust = 2
            profesores_json.append({
                "nombre": fila["Nombre"].strip(),
                "apellidos": fila["Apellidos"].strip(),
                "email": fila["Email"].strip(),
                "telefono": None,
                "especialidades": especialidades,
                "niveles": ["FP"],
                "max_sustituciones_semana": max_sust,
                "notas": fila.get("Notas", "").strip() or None,
            })

    # Horarios
    horarios_json: dict[str, list[dict]] = {}
    lineas_hor = secciones.get("Horario semanal", [])
    idx = primera_tabla(lineas_hor)
    if idx is not None:
        for fila in parse_tabla_md(lineas_hor[idx:]):
            email = fila["Email"].strip()
            if not email:
                continue
            if email not in horarios_json:
                horarios_json[email] = []
            horarios_json[email].append({
                "dia_semana": int(fila["Dia"].strip()),
                "tramo_horario": int(fila["Tramo"].strip()),
                "curso": grupo,
                "asignatura": fila["Asignatura"].strip(),
                "aula": fila["Aula"].strip() or None,
                "es_libre": False,
            })

    directorio = md_path.parent
    ruta_prof = directorio / f"{grupo}_profesores.json"
    ruta_hor = directorio / f"{grupo}_horarios.json"

    ruta_prof.write_text(json.dumps(profesores_json, ensure_ascii=False, indent=2), encoding="utf-8")
    ruta_hor.write_text(json.dumps(horarios_json, ensure_ascii=False, indent=2), encoding="utf-8")

    total_tramos = sum(len(v) for v in horarios_json.values())
    print(f"  OK {ruta_prof.name}  -  {len(profesores_json)} profesores")
    print(f"  OK {ruta_hor.name}   -  {total_tramos} tramos, {len(horarios_json)} profesores con horario")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    base = Path(__file__).parent

    if len(sys.argv) > 1:
        md_files = [base / sys.argv[1]]
    else:
        md_files = [
            f for f in sorted(base.glob("*.md"))
            if f.stem not in MD_IGNORADOS
        ]

    if not md_files:
        print("No se encontraron ficheros .md para procesar.")
        sys.exit(1)

    for md_file in md_files:
        if not md_file.exists():
            print(f"[ERROR] No existe: {md_file}")
            continue
        print(f"\nProcesando {md_file.name} ...")
        if md_file.stem == MD_CALENDARIO:
            generar_calendario(md_file)
        else:
            generar_grupo(md_file)

    print("\nListo.")


if __name__ == "__main__":
    main()
