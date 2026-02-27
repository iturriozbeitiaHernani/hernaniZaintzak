from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.teacher import Teacher
from app.models.schedule import Schedule
from app.models.user import User
from app.schemas.teacher import TeacherCreate, TeacherUpdate, TeacherOut, ScheduleEntry, ScheduleOut

router = APIRouter()


@router.get("", response_model=list[TeacherOut])
async def list_teachers(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(select(Teacher).order_by(Teacher.apellidos, Teacher.nombre))
    return result.scalars().all()


@router.post("", response_model=TeacherOut, status_code=status.HTTP_201_CREATED)
async def create_teacher(
    body: TeacherCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    existing = await db.scalar(select(Teacher).where(Teacher.email == body.email))
    if existing:
        raise HTTPException(status_code=409, detail="Ya existe un profesor con ese email")
    teacher = Teacher(**body.model_dump())
    db.add(teacher)
    await db.commit()
    await db.refresh(teacher)
    return teacher


@router.get("/{teacher_id}", response_model=TeacherOut)
async def get_teacher(
    teacher_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    teacher = await db.scalar(select(Teacher).where(Teacher.id == teacher_id))
    if not teacher:
        raise HTTPException(status_code=404, detail="Profesor no encontrado")
    return teacher


@router.put("/{teacher_id}", response_model=TeacherOut)
async def update_teacher(
    teacher_id: int,
    body: TeacherUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    teacher = await db.scalar(select(Teacher).where(Teacher.id == teacher_id))
    if not teacher:
        raise HTTPException(status_code=404, detail="Profesor no encontrado")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(teacher, field, value)
    await db.commit()
    await db.refresh(teacher)
    return teacher


@router.get("/{teacher_id}/schedule", response_model=list[ScheduleOut])
async def get_schedule(
    teacher_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    teacher = await db.scalar(select(Teacher).where(Teacher.id == teacher_id))
    if not teacher:
        raise HTTPException(status_code=404, detail="Profesor no encontrado")
    result = await db.execute(
        select(Schedule)
        .where(Schedule.teacher_id == teacher_id)
        .order_by(Schedule.dia_semana, Schedule.tramo_horario)
    )
    return result.scalars().all()


@router.put("/{teacher_id}/schedule", response_model=list[ScheduleOut])
async def update_schedule(
    teacher_id: int,
    entries: list[ScheduleEntry],
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    teacher = await db.scalar(select(Teacher).where(Teacher.id == teacher_id))
    if not teacher:
        raise HTTPException(status_code=404, detail="Profesor no encontrado")

    # Reemplazar horario completo
    existing = await db.execute(select(Schedule).where(Schedule.teacher_id == teacher_id))
    for s in existing.scalars().all():
        await db.delete(s)

    new_entries = [Schedule(teacher_id=teacher_id, **e.model_dump()) for e in entries]
    db.add_all(new_entries)
    await db.commit()

    result = await db.execute(
        select(Schedule)
        .where(Schedule.teacher_id == teacher_id)
        .order_by(Schedule.dia_semana, Schedule.tramo_horario)
    )
    return result.scalars().all()
