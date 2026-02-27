from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.absence import Absence
from app.models.user import User
from app.schemas.absence import AbsenceCreate, AbsenceUpdate, AbsenceOut
from app.services.substitution_service import procesar_ausencia

router = APIRouter()


@router.get("", response_model=list[AbsenceOut])
async def list_absences(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(select(Absence).order_by(Absence.fecha_inicio.desc()))
    return result.scalars().all()


@router.post("", response_model=AbsenceOut, status_code=status.HTTP_201_CREATED)
async def create_absence(
    body: AbsenceCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Verificar solapamiento con ausencias existentes del mismo profesor
    overlap = await db.scalar(
        select(Absence).where(
            and_(
                Absence.teacher_id == body.teacher_id,
                Absence.fecha_inicio <= body.fecha_fin,
                Absence.fecha_fin >= body.fecha_inicio,
            )
        )
    )
    if overlap:
        raise HTTPException(
            status_code=409,
            detail="Ya existe una ausencia que se solapa con ese periodo para este profesor",
        )

    absence = Absence(**body.model_dump(), created_by=user.id)
    db.add(absence)
    await db.commit()
    await db.refresh(absence)

    # Procesar sustituciones en background (no bloquea la respuesta)
    background_tasks.add_task(procesar_ausencia, absence.id)

    return absence


@router.get("/{absence_id}", response_model=AbsenceOut)
async def get_absence(
    absence_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    absence = await db.scalar(select(Absence).where(Absence.id == absence_id))
    if not absence:
        raise HTTPException(status_code=404, detail="Ausencia no encontrada")
    return absence


@router.put("/{absence_id}", response_model=AbsenceOut)
async def update_absence(
    absence_id: int,
    body: AbsenceUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    absence = await db.scalar(select(Absence).where(Absence.id == absence_id))
    if not absence:
        raise HTTPException(status_code=404, detail="Ausencia no encontrada")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(absence, field, value)
    await db.commit()
    await db.refresh(absence)
    return absence


@router.delete("/{absence_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_absence(
    absence_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    absence = await db.scalar(select(Absence).where(Absence.id == absence_id))
    if not absence:
        raise HTTPException(status_code=404, detail="Ausencia no encontrada")
    await db.delete(absence)
    await db.commit()
