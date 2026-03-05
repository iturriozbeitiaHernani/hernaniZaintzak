import asyncio
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.absence import Absence
from app.models.substitution import Substitution
from app.models.teacher import Teacher

logger = logging.getLogger(__name__)

# Mapa tramo → horario para el cuerpo del email
_TRAMO_HORA = {
    1: "08:00 – 09:00",
    2: "09:00 – 10:00",
    3: "10:00 – 11:00",
    4: "11:25 – 12:25",
    5: "12:25 – 13:25",
    6: "13:25 – 14:25",
}


async def notificar_sustituto(substitution: Substitution, db: AsyncSession) -> None:
    """
    Notifica al sustituto por email cuando se asigna o confirma una sustitución.

    Si SMTP_HOST está vacío, la función escribe el mensaje en el log y retorna
    sin error, de modo que el flujo principal nunca se bloquea por un fallo de email.
    """
    # Cargar datos del sustituto y del docente ausente
    sustituto = await db.scalar(
        select(Teacher).where(Teacher.id == substitution.substitute_teacher_id)
    )
    if not sustituto or not sustituto.email:
        logger.warning(
            "notificar_sustituto: no se encontró email para teacher_id=%s",
            substitution.substitute_teacher_id,
        )
        return

    absence = await db.scalar(
        select(Absence).where(Absence.id == substitution.absence_id)
    )
    ausente = None
    if absence:
        ausente = await db.scalar(
            select(Teacher).where(Teacher.id == absence.teacher_id)
        )

    ausente_nombre = (
        f"{ausente.nombre} {ausente.apellidos}" if ausente else "un/a compañero/a"
    )
    hora_str = _TRAMO_HORA.get(substitution.tramo_horario, f"tramo {substitution.tramo_horario}")
    fecha_str = substitution.fecha.strftime("%A, %d de %B de %Y")
    aula_str = substitution.aula or "—"

    asunto = (
        f"[hernaniZaintzak] Guardia asignada — {substitution.fecha.strftime('%d/%m/%Y')} "
        f"tramo {substitution.tramo_horario}"
    )

    cuerpo_html = f"""\
<html>
<body style="font-family: Arial, sans-serif; color: #333;">
  <h2 style="color: #1d4ed8;">Guardia asignada</h2>
  <p>Estimado/a <strong>{sustituto.nombre} {sustituto.apellidos}</strong>,</p>
  <p>Se te ha asignado una guardia de sustitución con los siguientes datos:</p>
  <table style="border-collapse: collapse; width: 100%; max-width: 500px;">
    <tr style="background:#f3f4f6;">
      <td style="padding:8px 12px; border:1px solid #e5e7eb;"><strong>Fecha</strong></td>
      <td style="padding:8px 12px; border:1px solid #e5e7eb;">{fecha_str}</td>
    </tr>
    <tr>
      <td style="padding:8px 12px; border:1px solid #e5e7eb;"><strong>Hora</strong></td>
      <td style="padding:8px 12px; border:1px solid #e5e7eb;">{hora_str}</td>
    </tr>
    <tr style="background:#f3f4f6;">
      <td style="padding:8px 12px; border:1px solid #e5e7eb;"><strong>Curso</strong></td>
      <td style="padding:8px 12px; border:1px solid #e5e7eb;">{substitution.curso}</td>
    </tr>
    <tr>
      <td style="padding:8px 12px; border:1px solid #e5e7eb;"><strong>Asignatura</strong></td>
      <td style="padding:8px 12px; border:1px solid #e5e7eb;">{substitution.asignatura_original}</td>
    </tr>
    <tr style="background:#f3f4f6;">
      <td style="padding:8px 12px; border:1px solid #e5e7eb;"><strong>Aula</strong></td>
      <td style="padding:8px 12px; border:1px solid #e5e7eb;">{aula_str}</td>
    </tr>
    <tr>
      <td style="padding:8px 12px; border:1px solid #e5e7eb;"><strong>Ausente</strong></td>
      <td style="padding:8px 12px; border:1px solid #e5e7eb;">{ausente_nombre}</td>
    </tr>
  </table>
  <p style="margin-top:20px; font-size:12px; color:#6b7280;">
    Este mensaje ha sido generado automáticamente por hernaniZaintzak.
  </p>
</body>
</html>"""

    cuerpo_texto = (
        f"Guardia asignada\n\n"
        f"Estimado/a {sustituto.nombre} {sustituto.apellidos},\n\n"
        f"Se te ha asignado una guardia de sustitución:\n"
        f"  Fecha:      {fecha_str}\n"
        f"  Hora:       {hora_str}\n"
        f"  Curso:      {substitution.curso}\n"
        f"  Asignatura: {substitution.asignatura_original}\n"
        f"  Aula:       {aula_str}\n"
        f"  Ausente:    {ausente_nombre}\n"
    )

    # --- Fallback: sin SMTP configurado, solo log ---
    if not settings.SMTP_HOST:
        logger.info(
            "NOTIFICACIÓN [sin SMTP] → %s <%s> | %s tramo %s | %s | %s",
            f"{sustituto.nombre} {sustituto.apellidos}",
            sustituto.email,
            substitution.fecha,
            substitution.tramo_horario,
            substitution.curso,
            substitution.asignatura_original,
        )
        return

    # --- Envío real en thread para no bloquear el event loop ---
    try:
        await asyncio.to_thread(
            _enviar_smtp,
            destinatario=sustituto.email,
            asunto=asunto,
            cuerpo_html=cuerpo_html,
            cuerpo_texto=cuerpo_texto,
        )
        logger.info(
            "Email enviado a %s <%s> para sustitución id=%s",
            f"{sustituto.nombre} {sustituto.apellidos}",
            sustituto.email,
            substitution.id,
        )
    except Exception:
        logger.exception(
            "Error enviando email a %s para sustitución id=%s",
            sustituto.email,
            substitution.id,
        )


def _enviar_smtp(destinatario: str, asunto: str, cuerpo_html: str, cuerpo_texto: str) -> None:
    """Síncrono — se ejecuta en asyncio.to_thread."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = asunto
    msg["From"] = settings.SMTP_FROM or settings.SMTP_USER
    msg["To"] = destinatario

    msg.attach(MIMEText(cuerpo_texto, "plain", "utf-8"))
    msg.attach(MIMEText(cuerpo_html, "html", "utf-8"))

    if settings.SMTP_TLS:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            smtp.sendmail(msg["From"], [destinatario], msg.as_string())
    else:
        with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT) as smtp:
            smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            smtp.sendmail(msg["From"], [destinatario], msg.as_string())
