# CLAUDE.md — hernaniZaintzak

## Visión del Proyecto

**hernaniZaintzak** — Aplicación web para centros educativos que automatiza la gestión de sustituciones de profesores ausentes. Cuando un docente falta, el sistema genera automáticamente propuestas de sustitución inteligentes usando Claude Opus 4.6 con pensamiento adaptativo, considerando disponibilidad, especialidad, carga de trabajo y restricciones de cada profesor.

---

## Stack Tecnológico

| Capa | Tecnología |
|------|-----------|
| Frontend | React 18 + TypeScript + Vite |
| Backend | Python 3.12 + FastAPI |
| ORM | SQLAlchemy 2.0 (async) + Alembic |
| Base de datos | PostgreSQL 16 |
| Autenticación | JWT (python-jose) + bcrypt |
| IA | Anthropic SDK (`anthropic`) — modelo `claude-opus-4-6` |
| Testing | pytest + httpx + pytest-asyncio |
| Frontend deps | TanStack Query, React Hook Form, Zustand, Tailwind CSS |

---

## Arquitectura del Proyecto

```
proyecto/
├── backend/
│   ├── app/
│   │   ├── main.py                  # Entry point FastAPI
│   │   ├── core/
│   │   │   ├── config.py            # Settings (env vars)
│   │   │   ├── database.py          # SQLAlchemy async engine
│   │   │   ├── security.py          # JWT, hashing
│   │   │   └── dependencies.py      # FastAPI deps (get_db, current_user)
│   │   ├── models/                  # SQLAlchemy ORM models
│   │   │   ├── teacher.py
│   │   │   ├── absence.py
│   │   │   ├── substitution.py
│   │   │   ├── schedule.py
│   │   │   ├── center_config.py
│   │   │   └── user.py
│   │   ├── schemas/                 # Pydantic v2 schemas (request/response)
│   │   │   ├── teacher.py
│   │   │   ├── absence.py
│   │   │   ├── substitution.py
│   │   │   ├── center_config.py
│   │   │   └── auth.py
│   │   ├── routers/                 # FastAPI routers
│   │   │   ├── auth.py
│   │   │   ├── teachers.py
│   │   │   ├── absences.py
│   │   │   ├── substitutions.py
│   │   │   ├── config.py
│   │   │   └── reports.py
│   │   ├── services/                # Business logic
│   │   │   ├── substitution_service.py   # Orquesta todo el flujo
│   │   │   ├── ai_service.py             # Integración Claude
│   │   │   └── notification_service.py   # Notificaciones (email/SMS)
│   │   └── alembic/                 # Migraciones DB
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── stores/
│   │   ├── api/                     # Clientes API (fetch wrappers)
│   │   └── types/
│   └── vite.config.ts
├── .env.example
├── docker-compose.yml
└── CLAUDE.md
```

---

## Modelos de Datos (SQLAlchemy)

### `Teacher` — Docente
```python
class Teacher(Base):
    id: int
    nombre: str
    apellidos: str
    email: str
    telefono: str | None
    especialidades: list[str]       # JSON array: ["Matemáticas", "Física"]
    niveles: list[str]              # JSON array: ["ESO", "Bachillerato"]
    max_sustituciones_semana: int   # Default: 2
    activo: bool
    notas: str | None               # Info relevante para la IA
    created_at: datetime
```

### `Schedule` — Horario semanal del docente
```python
class Schedule(Base):
    id: int
    teacher_id: int (FK)
    dia_semana: int      # 0=Lunes, 4=Viernes
    tramo_horario: int   # 1-8 (horas del día)
    curso: str           # "2ºESO-A"
    asignatura: str      # "Matemáticas"
    aula: str | None
    es_libre: bool       # True = hora libre disponible para sustituir
```

### `Absence` — Ausencia de docente
```python
class Absence(Base):
    id: int
    teacher_id: int (FK)
    fecha_inicio: date
    fecha_fin: date
    motivo: str          # "Enfermedad", "Formación", "Asunto propio", etc.
    descripcion: str | None
    estado: str          # "pendiente" | "cubierta" | "parcialmente_cubierta"
    notificado_jefatura: bool
    created_at: datetime
    created_by: int (FK → User)
```

### `Substitution` — Sustitución asignada
```python
class Substitution(Base):
    id: int
    absence_id: int (FK)
    substitute_teacher_id: int (FK)
    fecha: date
    tramo_horario: int
    curso: str
    asignatura_original: str
    aula: str | None
    estado: str          # "propuesta" | "confirmada" | "rechazada" | "completada"
    # "propuesta"  → generada por IA, pendiente de revisión de jefatura
    #                (solo cuando CenterConfig.confirmacion_requerida = True)
    # "confirmada" → activa; si confirmacion_requerida=False se asigna directamente
    # "rechazada"  → descartada por jefatura (solo con confirmacion_requerida=True)
    # "completada" → tramo horario ya ejecutado

    # Trazabilidad de IA
    ai_propuesta: bool              # ¿Fue generada por Claude?
    ai_razonamiento: str | None     # Explicación de por qué se eligió este sustituto
    ai_alternativas: dict | None    # JSON con opciones alternativas y sus pros/contras
    ai_confianza: float | None      # 0.0-1.0 score de confianza de la IA

    notas_admin: str | None
    created_at: datetime
    confirmado_at: datetime | None
```

### `CenterConfig` — Configuración del centro
Tabla de una sola fila (singleton). Controla el comportamiento global del sistema.

```python
class CenterConfig(Base):
    id: int                              # Siempre 1
    nombre_centro: str

    # Flujo de confirmación
    confirmacion_requerida: bool         # Default: False
    # Si False → las sustituciones generadas por IA pasan automáticamente
    #            a estado="confirmada" y se notifica al sustituto sin intervención.
    # Si True  → pasan a estado="propuesta" y jefatura debe confirmar/rechazar
    #            antes de que se notifique al sustituto.

    # Límites operativos
    max_sustituciones_diarias_por_profesor: int   # Default: 2
    dias_anticipacion_notificacion: int            # Default: 1 (avisar con X días)

    # Criterios de prioridad personalizables (sobreescriben los defaults de la IA)
    priorizar_misma_especialidad: bool    # Default: True
    considerar_carga_semanal: bool        # Default: True

    updated_at: datetime
    updated_by: int (FK → User)
```

**Acceso en código:** `substitution_service` debe leer `CenterConfig` antes de decidir
el estado final de cada sustitución generada. Usar caché en memoria (5 min TTL)
para no hacer query en cada ausencia.

---

## Integración con Claude (ai_service.py)

### Configuración base
```python
# app/services/ai_service.py
import anthropic
from app.core.config import settings

client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
MODEL = "claude-opus-4-6"
```

### Función principal: generar propuestas de sustitución
La IA recibe el contexto completo (ausencia, horario afectado, profesores disponibles con sus perfiles)
y devuelve propuestas ordenadas con razonamiento detallado usando **streaming + adaptive thinking**.

```python
async def generar_propuestas_sustitucion(
    ausencia: AbsenceContext,
    tramos_afectados: list[TramoHorario],
    profesores_disponibles: list[TeacherProfile],
) -> PropostaSustitucion:
    """
    Usa Claude Opus 4.6 con thinking adaptativo para generar
    las mejores propuestas de sustitución con razonamiento explicable.
    """
    prompt = _construir_prompt(ausencia, tramos_afectados, profesores_disponibles)

    razonamiento_thinking = ""
    propuesta_json = ""

    async with client.messages.stream(
        model=MODEL,
        max_tokens=8000,
        thinking={"type": "adaptive"},
        output_config={"effort": "high"},
        system=SYSTEM_PROMPT_SUSTITUCIONES,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        async for event in stream:
            if event.type == "content_block_delta":
                if event.delta.type == "thinking_delta":
                    razonamiento_thinking += event.delta.thinking
                elif event.delta.type == "text_delta":
                    propuesta_json += event.delta.text

        final = await stream.get_final_message()

    return _parsear_respuesta(propuesta_json, razonamiento_thinking)
```

### System prompt para sustituciones
```python
SYSTEM_PROMPT_SUSTITUCIONES = """
Eres un asistente experto en gestión de personal docente para centros educativos.
Tu tarea es proponer la mejor asignación de profesores sustitutos para cubrir ausencias.

CRITERIOS DE PRIORIDAD (en orden):
1. Disponibilidad real (hora libre en ese tramo)
2. Afinidad con la asignatura (misma especialidad > especialidad cercana > cualquier profesor)
3. Nivel educativo compatible (no enviar un especialista de Bachillerato a Primaria sin motivo)
4. Carga de sustituciones reciente (priorizar quien menos haya sustituido esta semana)
5. Preferencias del centro (notas del perfil del profesor)

FORMATO DE RESPUESTA: JSON válido con este esquema exacto:
{
  "propuestas": [
    {
      "teacher_id": <int>,
      "nombre": "<str>",
      "puntuacion": <float 0-10>,
      "razon_principal": "<str — 1 frase>",
      "pros": ["<str>", ...],
      "contras": ["<str>", ...],
      "confianza": <float 0-1>
    }
  ],
  "advertencias": ["<str>", ...],
  "resumen": "<str — explicación general de la propuesta>"
}

Devuelve SOLO el JSON, sin texto adicional.
""".strip()
```

### Función auxiliar: análisis de patrones de ausencia
```python
async def analizar_patrones_ausencia(
    datos_historicos: dict,
) -> AnalisisPatrones:
    """
    Analiza el historial de ausencias para detectar patrones
    y anticipar necesidades futuras. Usa effort=max para análisis profundo.
    """
    async with client.messages.stream(
        model=MODEL,
        max_tokens=4000,
        thinking={"type": "adaptive"},
        output_config={"effort": "max"},
        messages=[{
            "role": "user",
            "content": f"Analiza estos datos de ausencias del trimestre: {datos_historicos}"
        }],
    ) as stream:
        final = await stream.get_final_message()
    ...
```

---

## API Endpoints (FastAPI)

### Autenticación
```
POST /api/auth/login          → JWT token
POST /api/auth/refresh        → Nuevo token
```

### Profesores
```
GET    /api/teachers           → Listar profesores (con filtros)
POST   /api/teachers           → Crear profesor
GET    /api/teachers/{id}      → Detalle profesor + historial
PUT    /api/teachers/{id}      → Actualizar
GET    /api/teachers/{id}/schedule  → Horario semanal
PUT    /api/teachers/{id}/schedule  → Actualizar horario
```

### Ausencias
```
GET    /api/absences           → Listar ausencias (fecha, estado, profesor)
POST   /api/absences           → Registrar ausencia + DISPARA generación IA
GET    /api/absences/{id}      → Detalle + propuestas IA generadas
PUT    /api/absences/{id}      → Actualizar (estado, fechas)
DELETE /api/absences/{id}      → Cancelar ausencia
```

### Sustituciones
```
GET    /api/substitutions          → Listar (fecha, estado, filtros)
POST   /api/substitutions/generate → Generar propuestas IA para una ausencia
POST   /api/substitutions/{id}/confirm   → Confirmar propuesta
POST   /api/substitutions/{id}/reject    → Rechazar + motivo
GET    /api/substitutions/today          → Vista del día (para jefatura)
GET    /api/substitutions/week           → Vista semanal
```

### Configuración del centro
```
GET    /api/config                → Leer configuración actual
PUT    /api/config                → Actualizar configuración (solo admin)
```

### Reportes (con análisis IA)
```
GET    /api/reports/absences    → Stats ausencias por periodo/profesor
GET    /api/reports/coverage    → Tasa de cobertura de sustituciones
GET    /api/reports/ai-analysis → Análisis IA de patrones (effort=max)
```

---

## Flujo de Negocio Principal

```
1. Ausencia registrada (POST /api/absences)
   ↓
2. substitution_service detecta tramos afectados (cruza ausencia × horario)
   ↓
3. Busca profesores disponibles (hora libre en cada tramo afectado)
   ↓
4. ai_service.generar_propuestas_sustitucion() — streaming a Claude
   ↓
5. Lee CenterConfig.confirmacion_requerida
   ↓
   ┌─────────────────────────────┬──────────────────────────────────────────┐
   │ confirmacion_requerida=False│ confirmacion_requerida=True              │
   │ (comportamiento por defecto)│                                          │
   ├─────────────────────────────┼──────────────────────────────────────────┤
   │ Se guarda la mejor propuesta│ Se guardan todas las propuestas          │
   │ directamente como           │ en DB con estado="propuesta"             │
   │ estado="confirmada"         │                                          │
   │             ↓               │             ↓                            │
   │ notification_service notifica│ Jefatura revisa en UI (ve razonamiento IA│
   │ al sustituto inmediatamente  │ pros/contras de cada candidato)          │
   │             ↓               │             ↓                            │
   │             -               │ Confirma/rechaza (POST .../confirm|reject)│
   │                             │             ↓                            │
   │                             │ notification_service notifica al sustituto│
   └─────────────────────────────┴──────────────────────────────────────────┘
   ↓
6. Al finalizar el día, sustituciones confirmadas pasan a estado="completada"
```

**Regla clave:** el campo `CenterConfig.confirmacion_requerida` es el único punto
de decisión. `substitution_service` lo lee al finalizar la generación IA y
decide el estado inicial. Nunca hay lógica de confirmación dispersa por el código.

---

## Variables de Entorno (.env)

```env
# Base de datos
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/sustituciones_db

# Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# JWT
JWT_SECRET_KEY=<clave-aleatoria-larga>
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=480

# App
ENVIRONMENT=development
CORS_ORIGINS=http://localhost:5173

# Notificaciones (opcional fase inicial)
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
```

---

## Convenciones de Código

### Backend (Python)
- **Python 3.12+** — usar `X | Y` para Union types, `match/case` donde aplique
- **Async por defecto** — todos los endpoints FastAPI son `async def`, SQLAlchemy con `asyncpg`
- **Pydantic v2** — para schemas de request/response, validaciones estrictas
- **No usar `Any`** — tipar correctamente todo
- **Errores HTTP** — usar `HTTPException` con códigos semánticos (422 para validación, 409 para conflictos)
- **Logging** — usar `structlog` o `logging` estándar, nunca `print()`

### Frontend (React + TypeScript)
- **Componentes funcionales** únicamente, sin clases
- **TanStack Query** para toda la gestión de estado del servidor
- **Zustand** solo para estado UI local (modales, filtros activos, etc.)
- **React Hook Form** para todos los formularios
- **Tailwind CSS** para estilos — sin CSS módulos ni styled-components
- Los tipos del frontend se generan o sincronizan con los schemas Pydantic del backend

### IA / Claude
- Siempre usar **streaming** para las llamadas a Claude (respuestas pueden ser largas)
- Usar `thinking: {"type": "adaptive"}` en todas las llamadas a Opus 4.6
- Usar `output_config: {"effort": "high"}` para propuestas de sustitución
- Usar `output_config: {"effort": "max"}` para análisis profundos de patrones
- Guardar siempre `ai_razonamiento` (thinking) y `ai_alternativas` en DB para auditoría
- **No usar `budget_tokens`** — está deprecado en Opus 4.6
- **No usar prefills** — devuelven error 400 en Opus 4.6; usar system prompt + output_config.format

---

## Instalación y Puesta en Marcha

```bash
# 1. Clonar e instalar dependencias backend
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. Levantar PostgreSQL con Docker
docker compose up -d postgres

# 3. Migraciones
alembic upgrade head

# 4. Arrancar backend
uvicorn app.main:app --reload --port 8000

# 5. Frontend
cd ../frontend
npm install
npm run dev  # → http://localhost:5173
```

---

## Pruebas

```bash
# Backend
pytest tests/ -v --asyncio-mode=auto

# Un endpoint específico
pytest tests/test_substitutions.py::test_generate_proposals -v

# Frontend
npm run test
```

---

## Fases de Desarrollo Sugeridas

### Fase 1 — Core Backend (MVP)
- [ ] Modelos DB + migraciones Alembic
- [ ] CRUD Teachers + Schedule
- [ ] CRUD Absences
- [ ] `ai_service.py` — generación de propuestas con Claude
- [ ] Endpoint `POST /api/absences` que dispara la IA
- [ ] Endpoint de confirmación/rechazo de propuestas

### Fase 2 — Frontend MVP
- [ ] Login (JWT)
- [ ] Vista de ausencias del día/semana
- [ ] Formulario de registro de ausencia
- [ ] Panel de propuestas IA con razonamiento visible
- [ ] Acción de confirmar/rechazar sustitución

### Fase 3 — Funcionalidades avanzadas
- [ ] Notificaciones por email al sustituto
- [ ] Panel de reportes con análisis IA de patrones
- [ ] Importación masiva de horarios (Excel/CSV)
- [ ] Historial de sustituciones por profesor
- [ ] App móvil básica (PWA)

---

## Notas Importantes para el Desarrollo

1. **Trazabilidad IA**: Siempre guardar el `ai_razonamiento` (bloque thinking de Claude) en base de datos. Esto es clave para que la jefatura entienda *por qué* se propone un sustituto concreto y para auditorías futuras.

2. **Streaming en frontend**: Los endpoints que llaman a Claude deben usar Server-Sent Events (SSE) o WebSocket para mostrar el progreso en tiempo real. No bloquear esperando la respuesta completa.

3. **Fallback sin IA**: Si la llamada a Claude falla (timeout, rate limit), el sistema debe poder mostrar candidatos básicos ordenados por criterios simples (disponibilidad + especialidad) sin IA, indicando que es una sugerencia automática sin análisis inteligente.

4. **Idempotencia**: Registrar una ausencia dos veces debe dar error 409, no crear duplicados.

5. **Confirmación condicional**: El flujo de confirmación está controlado exclusivamente por `CenterConfig.confirmacion_requerida`. Cuando es `False`, el sistema es totalmente autónomo: la IA elige, asigna y notifica sin intervención humana. Los endpoints `POST .../confirm` y `POST .../reject` deben devolver `403` si `confirmacion_requerida=False` para evitar confusiones. La configuración es accesible solo por administradores.

6. **Datos sensibles**: No enviar datos personales innecesarios a la API de Anthropic. Pseudonimizar si es posible (usar `teacher_id` en lugar de nombres completos en el prompt, resolver los nombres en el backend tras recibir la respuesta).
