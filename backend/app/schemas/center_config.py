import datetime

from pydantic import BaseModel


class CenterConfigOut(BaseModel):
    id: int
    nombre_centro: str
    confirmacion_requerida: bool
    max_sustituciones_diarias_por_profesor: int
    dias_anticipacion_notificacion: int
    priorizar_misma_especialidad: bool
    considerar_carga_semanal: bool
    updated_at: datetime.datetime

    model_config = {"from_attributes": True}


class CenterConfigUpdate(BaseModel):
    nombre_centro: str | None = None
    confirmacion_requerida: bool | None = None
    max_sustituciones_diarias_por_profesor: int | None = None
    dias_anticipacion_notificacion: int | None = None
    priorizar_misma_especialidad: bool | None = None
    considerar_carga_semanal: bool | None = None
