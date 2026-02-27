import logging

from app.models.substitution import Substitution

logger = logging.getLogger(__name__)


async def notificar_sustituto(substitution: Substitution) -> None:
    """
    Fase 1: log a consola.
    Fase 3: enviar email real via SMTP.
    """
    logger.info(
        "NOTIFICACIÓN [stub] → Sustitución confirmada: id=%s | sustituto_id=%s | fecha=%s | tramo=%s | curso=%s",
        substitution.id,
        substitution.substitute_teacher_id,
        substitution.fecha,
        substitution.tramo_horario,
        substitution.curso,
    )
