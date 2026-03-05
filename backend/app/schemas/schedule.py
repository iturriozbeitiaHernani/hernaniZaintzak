import datetime

from pydantic import BaseModel


class TeacherBrief(BaseModel):
    id: int
    nombre: str


class DayScheduleEntry(BaseModel):
    tramo: int
    asignatura: str | None
    aula: str | None
    titular: TeacherBrief | None   # None si el tramo no tiene profesor asignado
    ausente: bool
    motivo_ausencia: str | None
    sustituto: TeacherBrief | None
    sustitucion_id: int | None
    sustitucion_estado: str | None
    ai_propuesta: bool


class WeekDaySchedule(BaseModel):
    fecha: datetime.date
    dia_semana: int          # 0=Lunes … 4=Viernes
    tramos: list[DayScheduleEntry]
