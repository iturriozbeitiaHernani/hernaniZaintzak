import datetime

from sqlalchemy import String, Boolean, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class CenterConfig(Base):
    __tablename__ = "center_config"

    id: Mapped[int] = mapped_column(primary_key=True, default=1)
    nombre_centro: Mapped[str] = mapped_column(String(200), default="Mi Centro Educativo")

    # Flujo de confirmación
    # False → IA asigna directamente (confirmada) y notifica sin intervención humana
    # True  → IA propone, jefatura confirma/rechaza antes de notificar
    confirmacion_requerida: Mapped[bool] = mapped_column(Boolean, default=False)

    # Límites operativos
    max_sustituciones_diarias_por_profesor: Mapped[int] = mapped_column(Integer, default=2)
    dias_anticipacion_notificacion: Mapped[int] = mapped_column(Integer, default=1)

    # Criterios de prioridad
    priorizar_misma_especialidad: Mapped[bool] = mapped_column(Boolean, default=True)
    considerar_carga_semanal: Mapped[bool] = mapped_column(Boolean, default=True)

    updated_at: Mapped[datetime.datetime] = mapped_column(
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )
    updated_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
