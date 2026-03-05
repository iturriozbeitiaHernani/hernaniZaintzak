import datetime
import logging

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.absence import Absence
from app.models.center_config import CenterConfig
from app.models.schedule import Schedule
from app.models.substitution import Substitution
from app.models.teacher import Teacher
from app.services.ai_service import generar_propuestas_sustitucion
from app.services.notification_service import notificar_sustituto

logger = logging.getLogger(__name__)


# ── Preview (síncrono, sin guardar en DB) ────────────────────────────────────────

async def preview_ausencia(
    db: AsyncSession,
    teacher_id: int,
    fecha: datetime.date,
    tramos_afectados: list[int] | None,
) -> list[dict]:
    """
    Genera propuestas de sustitución para una ausencia sin guardar nada en DB.
    Devuelve una lista de dicts con la estructura de TramoPreview.
    """
    teacher = await db.scalar(select(Teacher).where(Teacher.id == teacher_id))
    if not teacher:
        return []

    config = await db.scalar(select(CenterConfig).where(CenterConfig.id == 1))

    tramos = await _detectar_tramos(
        db, teacher.id, fecha, fecha, tramos_afectados=tramos_afectados
    )

    result = []
    for tramo in tramos:
        disponibles = await _buscar_disponibles(db, tramo, config)

        ausencia_info = {
            "motivo": "preview",
            "asignatura": tramo["asignatura"],
            "curso": tramo["curso"],
            "niveles_docente": teacher.niveles,
        }
        config_dict = {
            "priorizar_misma_especialidad": config.priorizar_misma_especialidad if config else True,
            "considerar_carga_semanal": config.considerar_carga_semanal if config else True,
            "max_sustituciones_diarias": config.max_sustituciones_diarias_por_profesor if config else 2,
        }

        propuesta = await generar_propuestas_sustitucion(ausencia_info, tramo, disponibles, config_dict)

        candidatos = [
            {
                "teacher_id": p.get("teacher_id", 0),
                "nombre": p.get("nombre", ""),
                "puntuacion": float(p.get("puntuacion", 5.0)),
                "razon_principal": p.get("razon_principal", ""),
                "pros": p.get("pros", []),
                "contras": p.get("contras", []),
                "confianza": float(p.get("confianza", 0.5)),
            }
            for p in propuesta.propuestas
        ]

        result.append({
            "tramo_horario": tramo["tramo_horario"],
            "asignatura": tramo["asignatura"],
            "aula": tramo.get("aula"),
            "propuestas": candidatos,
            "advertencias": propuesta.advertencias,
            "resumen": propuesta.resumen,
        })

    return result


# ── Crear sustituciones desde elección manual ────────────────────────────────────

async def crear_sustituciones_elegidas(absence_id: int, sustitutos: list[dict]) -> None:
    """
    Crea Substitution records directamente a partir de la elección del usuario,
    sin llamar a la IA. Estado = 'confirmada'.
    """
    async with AsyncSessionLocal() as db:
        try:
            absence = await db.scalar(select(Absence).where(Absence.id == absence_id))
            if not absence:
                return

            teacher = await db.scalar(select(Teacher).where(Teacher.id == absence.teacher_id))
            if not teacher:
                return

            dia_semana = absence.fecha_inicio.weekday()
            schedule_result = await db.execute(
                select(Schedule).where(
                    Schedule.teacher_id == teacher.id,
                    Schedule.dia_semana == dia_semana,
                )
            )
            schedule_by_tramo = {s.tramo_horario: s for s in schedule_result.scalars().all()}

            for elegido in sustitutos:
                tramo_horario = elegido["tramo_horario"]
                schedule = schedule_by_tramo.get(tramo_horario)
                if not schedule:
                    continue

                sub = Substitution(
                    absence_id=absence_id,
                    substitute_teacher_id=elegido["substitute_teacher_id"],
                    fecha=absence.fecha_inicio,
                    tramo_horario=tramo_horario,
                    curso=schedule.curso or "",
                    asignatura_original=schedule.asignatura or "",
                    aula=schedule.aula,
                    estado="confirmada",
                    ai_propuesta=True,
                    ai_razonamiento=elegido.get("razon_principal"),
                    ai_alternativas=None,
                    ai_confianza=elegido.get("ai_confianza"),
                    confirmado_at=datetime.datetime.utcnow(),
                )
                db.add(sub)

            absence.estado = "cubierta"
            await db.commit()

            # Notificar a cada sustituto
            result = await db.execute(
                select(Substitution).where(Substitution.absence_id == absence_id)
            )
            for sub in result.scalars().all():
                await notificar_sustituto(sub, db)

        except Exception as e:
            logger.error("Error en crear_sustituciones_elegidas: %s", e, exc_info=True)


async def procesar_ausencia(absence_id: int) -> None:
    """
    Punto de entrada principal. Se llama en background tras registrar una ausencia.
    Abre su propia sesión de DB porque se ejecuta fuera del ciclo de vida del request.
    """
    async with AsyncSessionLocal() as db:
        try:
            await _procesar(db, absence_id)
        except Exception as e:
            logger.error("Error fatal procesando ausencia %s: %s", absence_id, e, exc_info=True)


async def _procesar(db: AsyncSession, absence_id: int) -> None:
    # 1. Cargar ausencia, profesor y config del centro
    result = await db.execute(select(Absence).where(Absence.id == absence_id))
    absence = result.scalar_one_or_none()
    if not absence:
        logger.warning("procesar_ausencia: ausencia %s no encontrada", absence_id)
        return

    result = await db.execute(select(Teacher).where(Teacher.id == absence.teacher_id))
    teacher = result.scalar_one_or_none()
    if not teacher:
        return

    result = await db.execute(select(CenterConfig).where(CenterConfig.id == 1))
    config = result.scalar_one_or_none()
    confirmacion_requerida = config.confirmacion_requerida if config else False

    # 2. Detectar tramos de docencia afectados por la ausencia
    tramos = await _detectar_tramos(
        db, teacher.id, absence.fecha_inicio, absence.fecha_fin,
        tramos_afectados=absence.tramos_afectados,
    )
    if not tramos:
        logger.info("Ausencia %s: sin tramos de docencia afectados", absence_id)
        absence.estado = "cubierta"
        await db.commit()
        return

    sustituciones_creadas = 0

    # 3. Para cada tramo: buscar disponibles → llamar IA → guardar sustitución
    for tramo in tramos:
        disponibles = await _buscar_disponibles(db, tramo, config)
        if not disponibles:
            logger.warning(
                "Ausencia %s — tramo %s del %s: sin profesores disponibles",
                absence_id, tramo["tramo_horario"], tramo["fecha"],
            )
            continue

        ausencia_info = {
            "motivo": absence.motivo,
            "asignatura": tramo["asignatura"],
            "curso": tramo["curso"],
            "niveles_docente": teacher.niveles,
        }
        config_dict = {
            "priorizar_misma_especialidad": config.priorizar_misma_especialidad if config else True,
            "considerar_carga_semanal": config.considerar_carga_semanal if config else True,
            "max_sustituciones_diarias": config.max_sustituciones_diarias_por_profesor if config else 2,
        }

        propuesta = await generar_propuestas_sustitucion(ausencia_info, tramo, disponibles, config_dict)
        if not propuesta.propuestas:
            continue

        mejor = propuesta.propuestas[0]
        estado = "propuesta" if confirmacion_requerida else "confirmada"

        sub = Substitution(
            absence_id=absence_id,
            substitute_teacher_id=mejor["teacher_id"],
            fecha=tramo["fecha"],
            tramo_horario=tramo["tramo_horario"],
            curso=tramo["curso"],
            asignatura_original=tramo["asignatura"],
            aula=tramo.get("aula"),
            estado=estado,
            ai_propuesta=True,
            ai_razonamiento=propuesta.ai_razonamiento,
            ai_alternativas={
                "alternativas": propuesta.propuestas[1:],
                "advertencias": propuesta.advertencias,
                "resumen": propuesta.resumen,
            },
            ai_confianza=mejor.get("confianza"),
        )
        if not confirmacion_requerida:
            sub.confirmado_at = datetime.datetime.utcnow()

        db.add(sub)
        await db.flush()  # Para obtener sub.id antes de notificar

        if not confirmacion_requerida:
            await notificar_sustituto(sub, db)

        sustituciones_creadas += 1

    # 4. Actualizar estado de la ausencia
    if sustituciones_creadas == len(tramos):
        absence.estado = "cubierta"
    elif sustituciones_creadas > 0:
        absence.estado = "parcialmente_cubierta"

    await db.commit()
    logger.info(
        "Ausencia %s procesada: %d/%d tramos cubiertos",
        absence_id, sustituciones_creadas, len(tramos),
    )


async def _detectar_tramos(
    db: AsyncSession,
    teacher_id: int,
    fecha_inicio: datetime.date,
    fecha_fin: datetime.date,
    tramos_afectados: list[int] | None = None,
) -> list[dict]:
    """Devuelve los tramos de docencia (no libres) del profesor en el rango de fechas.
    Si tramos_afectados no es None, solo se incluyen esos tramos horarios concretos."""
    tramos = []
    delta = (fecha_fin - fecha_inicio).days + 1

    for i in range(delta):
        fecha = fecha_inicio + datetime.timedelta(days=i)
        dia_semana = fecha.weekday()
        if dia_semana > 4:  # Saltar fines de semana
            continue

        conditions = [
            Schedule.teacher_id == teacher_id,
            Schedule.dia_semana == dia_semana,
            Schedule.es_libre == False,
        ]
        if tramos_afectados:
            conditions.append(Schedule.tramo_horario.in_(tramos_afectados))

        result = await db.execute(select(Schedule).where(and_(*conditions)))
        for s in result.scalars().all():
            tramos.append({
                "fecha": fecha,
                "dia_semana": dia_semana,
                "tramo_horario": s.tramo_horario,
                "curso": s.curso or "",
                "asignatura": s.asignatura or "",
                "aula": s.aula,
            })

    return tramos


async def _buscar_disponibles(
    db: AsyncSession,
    tramo: dict,
    config: CenterConfig | None,
) -> list[dict]:
    """
    Busca profesores con hora libre en ese tramo que no superen el límite diario.
    Devuelve lista con perfil enriquecido para la IA.
    """
    max_diarias = config.max_sustituciones_diarias_por_profesor if config else 2
    fecha: datetime.date = tramo["fecha"]
    dia = tramo["dia_semana"]
    hora = tramo["tramo_horario"]

    # Profesores que tienen marcada esa hora como libre
    result = await db.execute(
        select(Schedule.teacher_id).where(
            and_(
                Schedule.dia_semana == dia,
                Schedule.tramo_horario == hora,
                Schedule.es_libre == True,
            )
        )
    )
    candidatos_ids = [row[0] for row in result.all()]
    if not candidatos_ids:
        return []

    disponibles = []
    monday = fecha - datetime.timedelta(days=fecha.weekday())
    friday = monday + datetime.timedelta(days=4)

    for teacher_id in candidatos_ids:
        # Verificar límite diario
        count_hoy = await db.scalar(
            select(func.count(Substitution.id)).where(
                and_(
                    Substitution.substitute_teacher_id == teacher_id,
                    Substitution.fecha == fecha,
                    Substitution.estado.in_(["propuesta", "confirmada"]),
                )
            )
        )
        if (count_hoy or 0) >= max_diarias:
            continue

        # Carga semanal (dato informativo para la IA)
        count_semana = await db.scalar(
            select(func.count(Substitution.id)).where(
                and_(
                    Substitution.substitute_teacher_id == teacher_id,
                    Substitution.fecha >= monday,
                    Substitution.fecha <= friday,
                    Substitution.estado.in_(["propuesta", "confirmada"]),
                )
            )
        )

        # Datos del profesor
        teacher = await db.scalar(
            select(Teacher).where(Teacher.id == teacher_id, Teacher.activo == True)
        )
        if not teacher:
            continue

        disponibles.append({
            "id": teacher.id,
            "nombre": f"{teacher.nombre} {teacher.apellidos}",
            "especialidades": teacher.especialidades,
            "niveles": teacher.niveles,
            "notas": teacher.notas,
            "sustituciones_semana": count_semana or 0,
        })

    return disponibles
