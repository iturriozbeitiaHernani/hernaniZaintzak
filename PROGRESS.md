# PROGRESS.md — hernaniZaintzak — Seguimiento del Desarrollo

> Este fichero es la fuente de verdad del estado del proyecto.
> Al inicio de cada sesión leer este fichero. Al final de cada sesión actualizar
> las tareas completadas y escribir en "Última sesión" qué se hizo y qué quedó pendiente.

---

## Estado actual
**Fase:** 1 — Backend COMPLETO y funcionando ✅
**Última sesión:** 2026-02-27
**Próximo paso:** Fase 2 — Frontend React + Vite + TypeScript

---

## Última sesión (2026-02-27)
- Creada estructura completa de `backend/` con todos los ficheros
- `requirements.txt`, `.env.example`, `docker-compose.yml`
- `app/core/`: config, database (async), security (JWT+bcrypt), dependencies
- `app/models/`: User, CenterConfig, Teacher, Schedule, Absence, Substitution
- `app/schemas/`: auth, center_config, teacher, absence, substitution
- `app/routers/`: auth, teachers, absences, substitutions, config, reports
- `app/services/`: ai_service (Claude Opus 4.6 + adaptive thinking + fallback), substitution_service (flujo completo), notification_service (stub)
- `app/main.py` + `seed.py`
- `alembic/env.py` configurado para async + autogenerate
- ✅ Verificado: todos los imports OK, 26 rutas registradas
- ✅ Fix: DATABASE_URL cambiado de `localhost` a `postgres` (nombre servicio Docker)
- ✅ Fix: `bcrypt==3.2.2` fijado en requirements.txt (incompatibilidad passlib 1.7.4 + bcrypt>=4)
- ✅ Migración `alembic revision --autogenerate -m "initial"` + `alembic upgrade head` OK
- ✅ `python seed.py` OK — admin@centro.es / admin123
- ✅ Backend respondiendo en http://localhost:8000/api/health
- ✅ Nombre del proyecto: hernaniZaintzak

---

## MVP — Lista de tareas

### FASE 1 — Backend base

#### 1.1 Setup del proyecto
- [x] Crear `backend/` con estructura de carpetas según CLAUDE.md
- [x] `requirements.txt` con todas las dependencias
- [x] `backend/app/core/config.py` — Settings con pydantic-settings (lee .env)
- [x] `backend/app/core/database.py` — Engine async + SessionLocal
- [x] `backend/app/main.py` — App FastAPI con CORS configurado
- [x] `.env` y `.env.example`
- [x] `docker-compose.yml` con PostgreSQL

#### 1.2 Modelos y migraciones
- [x] `models/user.py`
- [x] `models/center_config.py`
- [x] `models/teacher.py`
- [x] `models/schedule.py`
- [x] `models/absence.py`
- [x] `models/substitution.py`
- [x] Configurar Alembic (`alembic init`, `env.py` async + autogenerate)
- [x] Primera migración: `alembic revision --autogenerate -m "initial"`
- [x] `alembic upgrade head` funciona sin errores

#### 1.3 Autenticación
- [x] `core/security.py` — hash password, crear/verificar JWT
- [x] `core/dependencies.py` — `get_db`, `get_current_user`, `require_admin`
- [x] `routers/auth.py` — POST /api/auth/login
- [x] `seed.py` — usuario admin + CenterConfig por defecto

#### 1.4 CRUD Profesores y Horarios
- [x] `routers/teachers.py` — GET/POST/PUT /api/teachers, GET/PUT schedule
- [x] Validación: no duplicar email de profesor (409)

#### 1.5 Configuración del centro
- [x] `routers/config.py` — GET/PUT /api/config
- [x] Auto-crea CenterConfig si no existe

#### 1.6 Registro de ausencias
- [x] `routers/absences.py` — GET/POST/PUT/DELETE /api/absences
- [x] Al POST: validar solapamiento (409) + dispara IA en background

#### 1.7 Servicio de IA
- [x] `services/ai_service.py` — Claude Opus 4.6 + adaptive thinking + streaming
- [x] Parseo JSON de respuesta
- [x] Fallback sin IA automático

#### 1.8 Servicio de sustituciones (núcleo)
- [x] `services/substitution_service.py` — flujo completo
- [x] Lee `CenterConfig.confirmacion_requerida` → decide estado
- [x] `routers/substitutions.py` — today/week/confirm/reject
- [x] confirm/reject devuelven 403 si confirmacion_requerida=False

#### 1.9 Notificaciones (mínimo viable)
- [x] `services/notification_service.py` — log a consola

---

### FASE 2 — Frontend MVP

#### 2.1 Setup
- [ ] `npx create vite@latest frontend -- --template react-ts`
- [ ] Instalar: @tanstack/react-query, zustand, react-hook-form, axios, tailwindcss
- [ ] Configurar proxy en `vite.config.ts` → backend :8000
- [ ] `src/api/client.ts` — axios con base URL + interceptor JWT

#### 2.2 Autenticación
- [ ] Página Login (email + password)
- [ ] Zustand store: `useAuthStore` (token, user, login, logout)
- [ ] PrivateRoute — redirige a /login si no hay token

#### 2.3 Vista principal — Hoy
- [ ] Página `/today` — tabla de sustituciones del día
  - [ ] Columnas: tramo, aula, curso, ausente, sustituto, estado
  - [ ] Badge de estado (propuesta/confirmada/rechazada)
  - [ ] Indicador "generada por IA" con icono

#### 2.4 Gestión de ausencias
- [ ] Página `/absences` — listado con filtro por fecha y profesor
- [ ] Modal "Nueva ausencia" — profesor, fecha inicio/fin, motivo
- [ ] Al guardar: spinner mientras IA procesa + resultado automático

#### 2.5 Panel de propuestas IA (solo si confirmacion_requerida=True)
- [ ] En el detalle de ausencia: lista de propuestas ordenadas por puntuación
- [ ] Mostrar para cada candidato: nombre, puntuación, razón principal, pros/contras
- [ ] Botón Confirmar / Rechazar por tramo
- [ ] Mostrar razonamiento completo de la IA (colapsable)

#### 2.6 Configuración
- [ ] Página `/settings` (solo admin)
- [ ] Toggle `confirmacion_requerida`
- [ ] Campo `max_sustituciones_diarias_por_profesor`

---

### FASE 3 — Mejoras (post-MVP)
- [ ] Notificaciones por email real (SMTP)
- [ ] Importación de horarios desde Excel/CSV
- [ ] Página de reportes con análisis IA de patrones
- [ ] Historial de sustituciones por profesor
- [ ] Tests automáticos (pytest + React Testing Library)
- [ ] PWA básica

---

## Decisiones tomadas
| Fecha | Decisión | Motivo |
|-------|----------|--------|
| 2026-02-27 | Stack: FastAPI + React + PostgreSQL | Preferencia del usuario |
| 2026-02-27 | Modelo: claude-opus-4-6 + adaptive thinking | Requerimiento explícito |
| 2026-02-27 | confirmacion_requerida en CenterConfig | Flujo flexible por centro |
| 2026-02-27 | Fallback sin IA obligatorio | Resiliencia ante fallos de API |

---

## Problemas encontrados
_(vacío — desarrollo no iniciado)_
