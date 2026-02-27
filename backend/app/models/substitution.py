import datetime

from sqlalchemy import String, Boolean, Integer, Float, ForeignKey, Text, Date, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Substitution(Base):
    __tablename__ = "substitutions"

    id: Mapped[int] = mapped_column(primary_key=True)
    absence_id: Mapped[int] = mapped_column(ForeignKey("absences.id", ondelete="CASCADE"))
    substitute_teacher_id: Mapped[int] = mapped_column(ForeignKey("teachers.id"))
    fecha: Mapped[datetime.date] = mapped_column(Date)
    tramo_horario: Mapped[int] = mapped_column(Integer)
    curso: Mapped[str] = mapped_column(String(50))
    asignatura_original: Mapped[str] = mapped_column(String(100))
    aula: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # propuesta  → pendiente de revisión (solo si confirmacion_requerida=True)
    # confirmada → activa (directa si confirmacion_requerida=False)
    # rechazada  → descartada por jefatura
    # completada → tramo ya ejecutado
    estado: Mapped[str] = mapped_column(String(20), default="propuesta")

    # Trazabilidad IA
    ai_propuesta: Mapped[bool] = mapped_column(Boolean, default=False)
    ai_razonamiento: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_alternativas: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ai_confianza: Mapped[float | None] = mapped_column(Float, nullable=True)

    notas_admin: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.utcnow)
    confirmado_at: Mapped[datetime.datetime | None] = mapped_column(nullable=True)

    absence: Mapped["Absence"] = relationship("Absence", back_populates="substitutions")
    substitute: Mapped["Teacher"] = relationship(
        "Teacher", foreign_keys=[substitute_teacher_id]
    )
