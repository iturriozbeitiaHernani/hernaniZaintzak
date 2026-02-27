from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User

router = APIRouter()


@router.get("/absences")
async def absences_report(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return {"message": "Próximamente — Fase 3"}


@router.get("/coverage")
async def coverage_report(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return {"message": "Próximamente — Fase 3"}
