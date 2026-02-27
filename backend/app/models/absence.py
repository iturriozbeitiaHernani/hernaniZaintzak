import datetime

from sqlalchemy import String, Boolean, ForeignKey, Text, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Absence(Base):
    __tablename__ = "absences"

    id: Mapped[int] = mapped_column(primary_key=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("teachers.id"))
    fecha_inicio: Mapped[datetime.date] = mapped_column(Date)
    fecha_fin: Mapped[datetime.date] = mapped_column(Date)
    motivo: Mapped[str] = mapped_column(String(100))
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    estado: Mapped[str] = mapped_column(
        String(30), default="pendiente"
    )  # pendiente | cubierta | parcialmente_cubierta
    notificado_jefatura: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.utcnow)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))

    teacher: Mapped["Teacher"] = relationship(
        "Teacher", foreign_keys=[teacher_id], back_populates="absences"
    )
    substitutions: Mapped[list["Substitution"]] = relationship(
        "Substitution", back_populates="absence", cascade="all, delete-orphan"
    )
    creator: Mapped["User"] = relationship("User", foreign_keys=[created_by])
