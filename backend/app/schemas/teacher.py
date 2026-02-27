import datetime

from pydantic import BaseModel, EmailStr


class TeacherCreate(BaseModel):
    nombre: str
    apellidos: str
    email: EmailStr
    telefono: str | None = None
    especialidades: list[str] = []
    niveles: list[str] = []
    max_sustituciones_semana: int = 2
    notas: str | None = None


class TeacherUpdate(BaseModel):
    nombre: str | None = None
    apellidos: str | None = None
    email: EmailStr | None = None
    telefono: str | None = None
    especialidades: list[str] | None = None
    niveles: list[str] | None = None
    max_sustituciones_semana: int | None = None
    activo: bool | None = None
    notas: str | None = None


class TeacherOut(BaseModel):
    id: int
    nombre: str
    apellidos: str
    email: str
    telefono: str | None
    especialidades: list[str]
    niveles: list[str]
    max_sustituciones_semana: int
    activo: bool
    notas: str | None
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class ScheduleEntry(BaseModel):
    dia_semana: int       # 0-4
    tramo_horario: int    # 1-8
    curso: str | None = None
    asignatura: str | None = None
    aula: str | None = None
    es_libre: bool = False


class ScheduleOut(ScheduleEntry):
    id: int
    teacher_id: int

    model_config = {"from_attributes": True}
