from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import auth, teachers, absences, substitutions, config, reports, schedule

app = FastAPI(
    title="hernaniZaintzak API",
    description="Gestión inteligente de sustituciones docentes con Claude Opus 4.6",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(teachers.router, prefix="/api/teachers", tags=["teachers"])
app.include_router(absences.router, prefix="/api/absences", tags=["absences"])
app.include_router(substitutions.router, prefix="/api/substitutions", tags=["substitutions"])
app.include_router(config.router, prefix="/api/config", tags=["config"])
app.include_router(reports.router, prefix="/api/reports", tags=["reports"])
app.include_router(schedule.router, prefix="/api/schedule", tags=["schedule"])


@app.get("/api/health", tags=["health"])
async def health():
    return {"status": "ok", "version": "1.0.0"}
