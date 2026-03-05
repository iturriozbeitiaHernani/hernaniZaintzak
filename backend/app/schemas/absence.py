import datetime

from pydantic import BaseModel, model_validator


# ── Preview (sin guardar) ───────────────────────────────────────────────────────

class AbsencePreviewRequest(BaseModel):
    teacher_id: int
    fecha: datetime.date
    tramos_afectados: list[int] | None = None


class CandidatoPropuesto(BaseModel):
    teacher_id: int
    nombre: str
    puntuacion: float
    razon_principal: str
    pros: list[str]
    contras: list[str]
    confianza: float


class TramoPreview(BaseModel):
    tramo_horario: int
    asignatura: str
    aula: str | None
    propuestas: list[CandidatoPropuesto]
    advertencias: list[str]
    resumen: str


class AbsencePreviewResponse(BaseModel):
    tramos: list[TramoPreview]


# ── Creación ────────────────────────────────────────────────────────────────────

class SustitutoElegido(BaseModel):
    """Sustituto elegido por jefatura para un tramo concreto."""
    tramo_horario: int
    substitute_teacher_id: int
    razon_principal: str | None = None
    ai_confianza: float | None = None


class AbsenceCreate(BaseModel):
    teacher_id: int
    fecha_inicio: datetime.date
    fecha_fin: datetime.date
    motivo: str = ""
    descripcion: str | None = None
    tramos_afectados: list[int] | None = None
    # Si se incluye, se crean las sustituciones directamente sin esperar la IA en background.
    sustitutos_elegidos: list[SustitutoElegido] | None = None

    @model_validator(mode="after")
    def validate_dates(self) -> "AbsenceCreate":
        if self.fecha_fin < self.fecha_inicio:
            raise ValueError("fecha_fin debe ser >= fecha_inicio")
        return self


class AbsenceUpdate(BaseModel):
    fecha_inicio: datetime.date | None = None
    fecha_fin: datetime.date | None = None
    motivo: str | None = None
    descripcion: str | None = None
    estado: str | None = None


class AbsenceOut(BaseModel):
    id: int
    teacher_id: int
    fecha_inicio: datetime.date
    fecha_fin: datetime.date
    motivo: str
    descripcion: str | None
    tramos_afectados: list[int] | None
    estado: str
    notificado_jefatura: bool
    created_at: datetime.datetime
    created_by: int

    model_config = {"from_attributes": True}
