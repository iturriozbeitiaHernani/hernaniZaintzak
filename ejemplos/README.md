# Ejemplos de datos — hernaniZaintzak

Carpeta con los formatos de entrada de cada entidad y un script para cargarlos en el sistema.

```
ejemplos/
├── profesores.json     ← Profesores (perfil + especialidades)
├── horarios.json       ← Horario semanal de cada profesor
├── ausencias.json      ← Ausencias de ejemplo (para pruebas)
├── config.json         ← Configuración del centro
└── cargar_datos.py     ← Script de carga masiva vía API
```

---

## Carga automática (recomendada)

El script `cargar_datos.py` llama a la API y carga todos los ficheros de una vez.
Requiere que el backend esté corriendo (`http://localhost:8000`).

```bash
# Instalar dependencia (solo la primera vez)
pip install httpx

# Cargar todo
python cargar_datos.py

# Cargar solo profesores y horarios
python cargar_datos.py --solo-profesores
python cargar_datos.py --solo-horarios

# Contra otro servidor / con otras credenciales
python cargar_datos.py --url http://mi-servidor:8000 --email admin@centro.es --password mipass
```

**Opciones disponibles:**

| Flag | Descripción |
|------|-------------|
| `--url` | URL base de la API (por defecto: `http://localhost:8000`) |
| `--email` | Email del admin (por defecto: `admin@centro.es`) |
| `--password` | Contraseña del admin (por defecto: `admin123`) |
| `--solo-profesores` | Solo carga `profesores.json` |
| `--solo-horarios` | Solo carga `horarios.json` |
| `--solo-ausencias` | Solo carga `ausencias.json` |
| `--solo-config` | Solo carga `config.json` |

---

## Referencia de formatos

### `profesores.json` — Array de profesores

Cada elemento es un objeto `TeacherCreate`:

```json
{
  "nombre":                    "Amaia",
  "apellidos":                 "Etxeberria Zubiaurre",
  "email":                     "amaia@ikastola.eus",      ← único, clave de identificación
  "telefono":                  "688001001",               ← opcional
  "especialidades":            ["Matemáticas", "Física"], ← lista de especialidades
  "niveles":                   ["ESO", "Bachillerato"],   ← niveles que puede impartir
  "max_sustituciones_semana":  3,                         ← límite semanal de guardias
  "notas":                     "Texto libre para la IA"   ← opcional, influye en decisiones IA
}
```

**Valores habituales para `niveles`:** `"Infantil"`, `"Primaria"`, `"ESO"`, `"Bachillerato"`, `"FP"`

**El email no puede repetirse.** Si ya existe un profesor con ese email, el script lo omite.

---

### `horarios.json` — Horario semanal por profesor

Objeto cuya clave es el **email del profesor** y el valor es un array de tramos:

```json
{
  "amaia@ikastola.eus": [
    {
      "dia_semana":    0,             ← 0=Lunes  1=Martes  2=Miércoles  3=Jueves  4=Viernes
      "tramo_horario": 1,             ← 1=08:00  2=09:00  3=10:00  4=11:25  5=12:25  6=13:25
      "curso":         "2ºBACH-A",   ← nombre del grupo (null si es hora libre)
      "asignatura":    "Matemáticas", ← materia impartida (null si es hora libre)
      "aula":          "A01",         ← aula (null si es hora libre)
      "es_libre":      false          ← true = hora disponible para sustituciones
    },
    {
      "dia_semana":    0,
      "tramo_horario": 3,
      "curso":         null,
      "asignatura":    null,
      "aula":          null,
      "es_libre":      true           ← esta hora puede ser asignada como guardia
    }
  ]
}
```

**Horario de tramos del centro:**

| Tramo | Hora |
|-------|------|
| 1 | 08:00 – 09:00 |
| 2 | 09:00 – 10:00 |
| 3 | 10:00 – 11:00 |
| — | 11:00 – 11:25 (recreo) |
| 4 | 11:25 – 12:25 |
| 5 | 12:25 – 13:25 |
| 6 | 13:25 – 14:25 |

**Importante:** El horario se reemplaza completo cada vez que se carga. Solo es necesario incluir los tramos con actividad; los no incluidos simplemente no existen.

---

### `ausencias.json` — Ausencias de ejemplo

Cada elemento usa `teacher_email` (el script lo convierte al `teacher_id` internamente):

```json
{
  "teacher_email": "amaia@ikastola.eus",
  "fecha_inicio":  "2026-03-10",   ← formato YYYY-MM-DD
  "fecha_fin":     "2026-03-10",   ← igual que inicio para ausencias de un día
  "motivo":        "Enfermedad"    ← texto libre (Enfermedad, Formación, Asunto propio…)
}
```

Al registrar una ausencia, el sistema **lanza automáticamente la IA** para generar propuestas de sustitución para todos los tramos afectados.

---

### `config.json` — Configuración del centro

```json
{
  "nombre_centro":                        "Ikastola Hernani",
  "confirmacion_requerida":               false,
  "max_sustituciones_diarias_por_profesor": 2,
  "dias_anticipacion_notificacion":       1,
  "priorizar_misma_especialidad":         true,
  "considerar_carga_semanal":             true
}
```

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `confirmacion_requerida` | bool | `false` → la IA asigna directamente. `true` → jefatura debe aprobar cada propuesta |
| `max_sustituciones_diarias_por_profesor` | int | Techo de guardias por docente en un día |
| `dias_anticipacion_notificacion` | int | Días de antelación para avisar al sustituto |
| `priorizar_misma_especialidad` | bool | La IA prioriza docentes de la misma especialidad |
| `considerar_carga_semanal` | bool | La IA tiene en cuenta cuántas guardias lleva cada profesor |

---

## Carga manual con curl

Si prefieres llamar a la API directamente:

```bash
# 1. Login (guarda el token)
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@centro.es","password":"admin123"}' \
  | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# 2. Crear un profesor
curl -X POST http://localhost:8000/api/teachers \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Amaia",
    "apellidos": "Etxeberria Zubiaurre",
    "email": "amaia@ikastola.eus",
    "especialidades": ["Matemáticas"],
    "niveles": ["ESO"],
    "max_sustituciones_semana": 2
  }'

# 3. Cargar su horario (reemplaza el horario completo)
curl -X PUT http://localhost:8000/api/teachers/1/schedule \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '[
    {"dia_semana": 0, "tramo_horario": 1, "curso": "2ºESO-A", "asignatura": "Matemáticas", "aula": "A01", "es_libre": false},
    {"dia_semana": 0, "tramo_horario": 2, "curso": null, "asignatura": null, "aula": null, "es_libre": true}
  ]'

# 4. Registrar una ausencia (dispara la IA automáticamente)
curl -X POST http://localhost:8000/api/absences \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "teacher_id": 1,
    "fecha_inicio": "2026-03-10",
    "fecha_fin": "2026-03-10",
    "motivo": "Enfermedad"
  }'

# 5. Ver las sustituciones generadas
curl http://localhost:8000/api/substitutions/today \
  -H "Authorization: Bearer $TOKEN"
```

---

## Notas

- Los campos que empiezan por `_` en los JSON son comentarios y son ignorados por el script.
- El script es **idempotente**: si un profesor ya existe (mismo email) lo omite y sigue; no crea duplicados.
- Los horarios **sí se reemplazan** completamente: si vuelves a ejecutar `--solo-horarios`, el horario anterior se sobrescribe con el del JSON.
- Las ausencias pueden devolver `409` si ya existe una con fechas solapadas para el mismo profesor.
