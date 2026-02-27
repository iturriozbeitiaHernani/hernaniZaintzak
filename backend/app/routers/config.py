import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_admin
from app.models.center_config import CenterConfig
from app.models.user import User
from app.schemas.center_config import CenterConfigOut, CenterConfigUpdate

router = APIRouter()


async def _get_or_create_config(db: AsyncSession) -> CenterConfig:
    result = await db.execute(select(CenterConfig).where(CenterConfig.id == 1))
    config = result.scalar_one_or_none()
    if not config:
        config = CenterConfig(id=1)
        db.add(config)
        await db.commit()
        await db.refresh(config)
    return config


@router.get("", response_model=CenterConfigOut)
async def get_config(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await _get_or_create_config(db)


@router.put("", response_model=CenterConfigOut)
async def update_config(
    body: CenterConfigUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    config = await _get_or_create_config(db)
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(config, field, value)
    config.updated_by = admin.id
    config.updated_at = datetime.datetime.utcnow()
    await db.commit()
    await db.refresh(config)
    return config
