import datetime

from pydantic import BaseModel


class SubstitutionOut(BaseModel):
    id: int
    absence_id: int
    substitute_teacher_id: int
    fecha: datetime.date
    tramo_horario: int
    curso: str
    asignatura_original: str
    aula: str | None
    estado: str
    ai_propuesta: bool
    ai_razonamiento: str | None
    ai_alternativas: dict | None
    ai_confianza: float | None
    notas_admin: str | None
    created_at: datetime.datetime
    confirmado_at: datetime.datetime | None

    model_config = {"from_attributes": True}


class SubstitutionConfirm(BaseModel):
    notas_admin: str | None = None


class SubstitutionReject(BaseModel):
    motivo: str
