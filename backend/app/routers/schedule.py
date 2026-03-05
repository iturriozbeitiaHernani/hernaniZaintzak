import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.absence import Absence
from app.models.schedule import Schedule
from app.models.substitution import Substitution
from app.models.teacher import Teacher
from app.models.user import User
from app.schemas.schedule import DayScheduleEntry, TeacherBrief, WeekDaySchedule

router = APIRouter()


@router.get("/cursos", response_model=list[str])
async def get_cursos(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Lista todos los cursos/clases que tienen horario configurado."""
    result = await db.execute(
        select(Schedule.curso)
        .distinct()
        .where(Schedule.curso.is_not(None), Schedule.es_libre == False)
        .order_by(Schedule.curso)
    )
    return [r[0] for r in result.all()]


# ─── Helper interno ────────────────────────────────────────────────────────────

async def _get_day_entries(
    db: AsyncSession,
    fecha: datetime.date,
    curso: str,
) -> list[DayScheduleEntry]:
    """Devuelve los tramos de un curso para una fecha concreta."""
    dia_semana = fecha.weekday()  # 0=Lunes, 4=Viernes

    result = await db.execute(
        select(Schedule, Teacher)
        .outerjoin(Teacher, Schedule.teacher_id == Teacher.id)
        .where(
            Schedule.curso == curso,
            Schedule.dia_semana == dia_semana,
        )
        .order_by(Schedule.tramo_horario)
    )
    rows = result.all()

    entries: list[DayScheduleEntry] = []
    for schedule, teacher in rows:
        sustituto: TeacherBrief | None = None
        sustitucion_id: int | None = None
        sustitucion_estado: str | None = None
        ai_propuesta = False
        motivo_ausencia: str | None = None
        absence = None

        if teacher:
            absence = await db.scalar(
                select(Absence).where(
                    Absence.teacher_id == teacher.id,
                    Absence.fecha_inicio <= fecha,
                    Absence.fecha_fin >= fecha,
                )
            )
            if absence:
                motivo_ausencia = absence.motivo
                sub_row = await db.execute(
                    select(Substitution, Teacher)
                    .join(Teacher, Substitution.substitute_teacher_id == Teacher.id)
                    .where(
                        Substitution.absence_id == absence.id,
                        Substitution.tramo_horario == schedule.tramo_horario,
                        Substitution.fecha == fecha,
                    )
                )
                sub_result = sub_row.first()
                if sub_result:
                    sub, sub_teacher = sub_result
                    sustituto = TeacherBrief(
                        id=sub_teacher.id,
                        nombre=f"{sub_teacher.nombre} {sub_teacher.apellidos}",
                    )
                    sustitucion_id = sub.id
                    sustitucion_estado = sub.estado
                    ai_propuesta = sub.ai_propuesta

        entries.append(
            DayScheduleEntry(
                tramo=schedule.tramo_horario,
                asignatura=schedule.asignatura,
                aula=schedule.aula,
                titular=TeacherBrief(
                    id=teacher.id,
                    nombre=f"{teacher.nombre} {teacher.apellidos}",
                ) if teacher else None,
                ausente=absence is not None,
                motivo_ausencia=motivo_ausencia,
                sustituto=sustituto,
                sustitucion_id=sustitucion_id,
                sustitucion_estado=sustitucion_estado,
                ai_propuesta=ai_propuesta,
            )
        )

    return entries


# ─── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/day", response_model=list[DayScheduleEntry])
async def get_day_schedule(
    fecha: datetime.date = Query(..., description="Fecha en formato YYYY-MM-DD"),
    curso: str = Query(..., description="Nombre del curso, ej: 2ºESO-A"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Devuelve el horario completo de una clase para un día concreto."""
    return await _get_day_entries(db, fecha, curso)


@router.get("/week", response_model=list[WeekDaySchedule])
async def get_week_schedule(
    fecha: datetime.date = Query(..., description="Cualquier día de la semana"),
    curso: str = Query(..., description="Nombre del curso, ej: 2ºESO-A"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Devuelve el horario de una clase para los 5 días laborables de la semana
    que contiene 'fecha'. Útil para la vista semanal del panel de jefatura.
    """
    monday = fecha - datetime.timedelta(days=fecha.weekday())
    days = [monday + datetime.timedelta(days=i) for i in range(5)]

    result = []
    for day in days:
        tramos = await _get_day_entries(db, day, curso)
        result.append(WeekDaySchedule(fecha=day, dia_semana=day.weekday(), tramos=tramos))

    return result
