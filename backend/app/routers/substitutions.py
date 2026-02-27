import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.center_config import CenterConfig
from app.models.substitution import Substitution
from app.models.user import User
from app.schemas.substitution import SubstitutionOut, SubstitutionConfirm, SubstitutionReject

router = APIRouter()


async def _require_confirmacion(db: AsyncSession) -> None:
    """Devuelve 403 si el centro no tiene confirmación manual activada."""
    config = await db.scalar(select(CenterConfig).where(CenterConfig.id == 1))
    if not config or not config.confirmacion_requerida:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El centro tiene la confirmación automática activa (confirmacion_requerida=False). "
                   "Las sustituciones se confirman sin intervención manual.",
        )


@router.get("/today", response_model=list[SubstitutionOut])
async def get_today(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    today = datetime.date.today()
    result = await db.execute(
        select(Substitution)
        .where(Substitution.fecha == today)
        .order_by(Substitution.tramo_horario)
    )
    return result.scalars().all()


@router.get("/week", response_model=list[SubstitutionOut])
async def get_week(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    today = datetime.date.today()
    monday = today - datetime.timedelta(days=today.weekday())
    friday = monday + datetime.timedelta(days=4)
    result = await db.execute(
        select(Substitution)
        .where(and_(Substitution.fecha >= monday, Substitution.fecha <= friday))
        .order_by(Substitution.fecha, Substitution.tramo_horario)
    )
    return result.scalars().all()


@router.get("", response_model=list[SubstitutionOut])
async def list_substitutions(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Substitution).order_by(Substitution.fecha.desc(), Substitution.tramo_horario)
    )
    return result.scalars().all()


@router.post("/{sub_id}/confirm", response_model=SubstitutionOut)
async def confirm_substitution(
    sub_id: int,
    body: SubstitutionConfirm,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    await _require_confirmacion(db)

    sub = await db.scalar(select(Substitution).where(Substitution.id == sub_id))
    if not sub:
        raise HTTPException(status_code=404, detail="Sustitución no encontrada")
    if sub.estado != "propuesta":
        raise HTTPException(
            status_code=409,
            detail=f"No se puede confirmar una sustitución en estado '{sub.estado}'",
        )

    sub.estado = "confirmada"
    sub.confirmado_at = datetime.datetime.utcnow()
    if body.notas_admin:
        sub.notas_admin = body.notas_admin

    await db.commit()
    await db.refresh(sub)
    return sub


@router.post("/{sub_id}/reject", response_model=SubstitutionOut)
async def reject_substitution(
    sub_id: int,
    body: SubstitutionReject,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    await _require_confirmacion(db)

    sub = await db.scalar(select(Substitution).where(Substitution.id == sub_id))
    if not sub:
        raise HTTPException(status_code=404, detail="Sustitución no encontrada")
    if sub.estado != "propuesta":
        raise HTTPException(
            status_code=409,
            detail=f"No se puede rechazar una sustitución en estado '{sub.estado}'",
        )

    sub.estado = "rechazada"
    sub.notas_admin = body.motivo
    await db.commit()
    await db.refresh(sub)
    return sub
