# Importar todos los modelos para que Alembic los detecte
from app.models.user import User
from app.models.center_config import CenterConfig
from app.models.teacher import Teacher
from app.models.schedule import Schedule
from app.models.absence import Absence
from app.models.substitution import Substitution

__all__ = ["User", "CenterConfig", "Teacher", "Schedule", "Absence", "Substitution"]
