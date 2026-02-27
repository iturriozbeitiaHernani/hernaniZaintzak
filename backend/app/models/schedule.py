from sqlalchemy import Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Schedule(Base):
    __tablename__ = "schedules"

    id: Mapped[int] = mapped_column(primary_key=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("teachers.id", ondelete="CASCADE"))
    dia_semana: Mapped[int] = mapped_column(Integer)   # 0=Lunes … 4=Viernes
    tramo_horario: Mapped[int] = mapped_column(Integer)  # 1-8
    curso: Mapped[str | None] = mapped_column(String(50), nullable=True)
    asignatura: Mapped[str | None] = mapped_column(String(100), nullable=True)
    aula: Mapped[str | None] = mapped_column(String(50), nullable=True)
    es_libre: Mapped[bool] = mapped_column(Boolean, default=False)

    teacher: Mapped["Teacher"] = relationship("Teacher", back_populates="schedule")
