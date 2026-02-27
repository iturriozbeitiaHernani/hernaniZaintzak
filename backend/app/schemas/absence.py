import datetime

from pydantic import BaseModel, model_validator


class AbsenceCreate(BaseModel):
    teacher_id: int
    fecha_inicio: datetime.date
    fecha_fin: datetime.date
    motivo: str
    descripcion: str | None = None

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
    estado: str
    notificado_jefatura: bool
    created_at: datetime.datetime
    created_by: int

    model_config = {"from_attributes": True}
