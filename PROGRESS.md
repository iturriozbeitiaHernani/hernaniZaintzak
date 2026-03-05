# PROGRESS.md — hernaniZaintzak — Seguimiento del Desarrollo

> Este fichero es la fuente de verdad del estado del proyecto.
> Al inicio de cada sesión leer este fichero. Al final de cada sesión actualizar
> las tareas completadas y escribir en "Última sesión" qué se hizo y qué quedó pendiente.

---

## Estado actual
**Fase:** 3 — Mejoras en curso
**Última sesión:** 2026-03-04
**Próximo paso:** Fase 3 continúa — reportes IA, historial por profesor

---

## Última sesión (2026-03-04)
- Notificaciones email reales al asignar/confirmar una sustitución
- `notification_service.py` reescrito: smtplib + asyncio.to_thread + HTML email
- SMTP settings en `config.py` + `.env` / `.env.example` (fallback a log si SMTP_HOST vacío)
- `confirm_substitution` en `substitutions.py` ahora llama a `notificar_sustituto`
- Firma de `notificar_sustituto(sub, db)` actualizada en todos los call sites

## Última sesión (2026-03-03)
- Navegación por días y semanas en vista Hoy y nueva vista Semana
- Filtros y fecha compartidos entre páginas via Zustand (`scheduleFilterStore`)
- Clic en día de la semana navega a vista Día con esa fecha
- Botón + icono por tramo para registrar ausencias desde la vista Día
- `NewAbsenceModal` como componente compartido con prefill de fecha y profesor
- Fixes Docker: proxy Vite apunta a `backend:8000`, polling HMR activado
- Carpeta `ejemplos/` con JSONs de datos y `cargar_datos.py` para carga masiva vía API

## Última sesión (2026-02-27)
### Backend (sesión anterior)
- Creada estructura completa de `backend/` con todos los ficheros
- ✅ Fix: DATABASE_URL cambiado de `localhost` a `postgres`
- ✅ Fix: `bcrypt==3.2.2` fijado en requirements.txt
- ✅ Migración Alembic + `alembic upgrade head` OK
- ✅ `python seed.py` OK — admin@centro.es / admin123
- ✅ Backend respondiendo en http://localhost:8000/api/health

### Frontend (esta sesión)
- ✅ Vite + React 18 + TypeScript en `frontend/`
- ✅ Tailwind CSS v4 con `@tailwindcss/vite`
- ✅ TanStack Query v5, Zustand, React Hook Form, Axios, Lucide
- ✅ `src/api/` — client.ts (JWT interceptor), auth, substitutions, absences, teachers, config
- ✅ `src/store/authStore.ts` — Zustand + persist
- ✅ `src/components/PrivateRoute.tsx` — guarda rutas + rol admin
- ✅ `src/components/Layout.tsx` — sidebar con navegación
- ✅ `src/pages/LoginPage.tsx`
- ✅ `src/pages/TodayPage.tsx` — sustituciones del día + confirmar/rechazar
- ✅ `src/pages/AbsencesPage.tsx` — listado + modal nueva ausencia
- ✅ `src/pages/SettingsPage.tsx` — configuración del centro
- ✅ `src/App.tsx` — React Router v6 con rutas anidadas
- ✅ `src/main.tsx` — QueryClientProvider + StrictMode
- ✅ `frontend/Dockerfile` — Node 20 Alpine
- ✅ `docker-compose.yml` — servicio frontend en puerto 3000
- ✅ Frontend respondiendo en http://localhost:3000
- ✅ Proxy /api → backend:8000 funcionando

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
- [x] `npx create vite@latest frontend -- --template react-ts`
- [x] Instalar: @tanstack/react-query, zustand, react-hook-form, axios, tailwindcss
- [x] Configurar proxy en `vite.config.ts` → backend :8000
- [x] `src/api/client.ts` — axios con base URL + interceptor JWT

#### 2.2 Autenticación
- [x] Página Login (email + password)
- [x] Zustand store: `useAuthStore` (token, user, login, logout)
- [x] PrivateRoute — redirige a /login si no hay token

#### 2.3 Vista principal — Hoy
- [x] Página `/today` — tabla de sustituciones del día
  - [x] Columnas: tramo, aula, ausente, sustituto, estado
  - [x] Badge de estado (propuesta/confirmada/rechazada)
  - [x] Indicador "generada por IA" con icono

#### 2.4 Gestión de ausencias
- [x] Página `/absences` — listado de ausencias
- [x] Modal "Nueva ausencia" — profesor, fecha inicio/fin, motivo
- [x] Al guardar: spinner mientras IA procesa + resultado automático

#### 2.5 Panel de propuestas IA (solo si confirmacion_requerida=True)
- [x] En `/today`: botones Confirmar / Rechazar por fila (solo si confirmacion_requerida=True)
- [x] Indicador Bot icon para propuestas IA

#### 2.6 Configuración
- [x] Página `/settings` (solo admin)
- [x] Toggle `confirmacion_requerida`
- [x] Campo `max_sustituciones_diarias_por_profesor`

---

### FASE 3 — Mejoras (post-MVP)

#### Completado en sesión 2026-03-03
- [x] Navegación por días en vista Hoy (← fecha →, picker nativo, botón "Hoy")
- [x] Vista Semana nueva (`/week`) con grid Lun-Vie, navegación por semanas, picker
- [x] Filtros ciclo/curso compartidos entre vistas Día y Semana (Zustand store)
- [x] Fecha seleccionada compartida entre vistas (al pinchar día en Semana → va a Día)
- [x] Encabezados de día en vista Semana clicables → navegan a vista Día de ese día
- [x] Registro de ausencia desde vista Día: botón general en cabecera + icono por tramo
- [x] `NewAbsenceModal` extraído como componente compartido (pre-rellena fecha y profesor)
- [x] Fix proxy Vite: `localhost:8000` → `backend:8000` (Docker networking)
- [x] Fix HMR Vite en Docker/Windows: `usePolling: true` en vite.config.ts
- [x] Carpeta `ejemplos/` con formatos de datos y script de carga masiva

#### Pendiente
- [x] Notificaciones por email real (SMTP)
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
