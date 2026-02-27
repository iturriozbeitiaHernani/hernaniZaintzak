import datetime

from sqlalchemy import String, Boolean, Integer, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Teacher(Base):
    __tablename__ = "teachers"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100))
    apellidos: Mapped[str] = mapped_column(String(200))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    telefono: Mapped[str | None] = mapped_column(String(20), nullable=True)
    especialidades: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    niveles: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    max_sustituciones_semana: Mapped[int] = mapped_column(Integer, default=2)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    notas: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.utcnow)

    schedule: Mapped[list["Schedule"]] = relationship(
        "Schedule", back_populates="teacher", cascade="all, delete-orphan"
    )
    absences: Mapped[list["Absence"]] = relationship(
        "Absence", foreign_keys="Absence.teacher_id", back_populates="teacher"
    )
