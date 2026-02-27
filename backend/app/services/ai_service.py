import json
import logging
from dataclasses import dataclass, field

import anthropic

from app.core.config import settings

logger = logging.getLogger(__name__)

client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
MODEL = "claude-opus-4-6"

SYSTEM_PROMPT = """
Eres un asistente experto en gestión de personal docente para centros educativos.
Tu tarea es proponer la mejor asignación de profesores sustitutos para cubrir ausencias.

CRITERIOS DE PRIORIDAD (en orden):
1. Disponibilidad real (hora libre en ese tramo)
2. Afinidad con la asignatura (misma especialidad > especialidad cercana > cualquier profesor)
3. Nivel educativo compatible (no enviar a un especialista de Bachillerato a Primaria sin motivo)
4. Carga de sustituciones reciente (priorizar quien menos haya sustituido esta semana)
5. Preferencias del centro (notas del perfil del profesor)

FORMATO DE RESPUESTA: JSON válido con este esquema exacto, sin texto adicional:
{
  "propuestas": [
    {
      "teacher_id": <int>,
      "nombre": "<str>",
      "puntuacion": <float 0-10>,
      "razon_principal": "<str — 1 frase>",
      "pros": ["<str>"],
      "contras": ["<str>"],
      "confianza": <float 0-1>
    }
  ],
  "advertencias": ["<str>"],
  "resumen": "<str>"
}
""".strip()


@dataclass
class PropuestaSustitucion:
    propuestas: list[dict]
    advertencias: list[str]
    resumen: str
    ai_razonamiento: str = field(default="")


async def generar_propuestas_sustitucion(
    ausencia_info: dict,
    tramo: dict,
    profesores_disponibles: list[dict],
    config: dict,
) -> PropuestaSustitucion:
    """
    Llama a Claude Opus 4.6 con adaptive thinking para generar propuestas
    de sustitución ordenadas con razonamiento explicable.
    Incluye fallback automático si Claude no está disponible.
    """
    prompt = (
        f"Ausencia: {json.dumps(ausencia_info, ensure_ascii=False)}\n"
        f"Tramo a cubrir: {json.dumps(tramo, ensure_ascii=False)}\n"
        f"Profesores disponibles: {json.dumps(profesores_disponibles, ensure_ascii=False)}\n"
        f"Configuración del centro: {json.dumps(config, ensure_ascii=False)}\n\n"
        "Genera las propuestas de sustitución."
    )

    razonamiento = ""
    respuesta_json = ""

    try:
        async with client.messages.stream(
            model=MODEL,
            max_tokens=8000,
            thinking={"type": "adaptive"},
            output_config={"effort": "high"},
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            async for event in stream:
                if event.type == "content_block_delta":
                    if event.delta.type == "thinking_delta":
                        razonamiento += event.delta.thinking
                    elif event.delta.type == "text_delta":
                        respuesta_json += event.delta.text
            await stream.get_final_message()

        data = json.loads(respuesta_json)
        return PropuestaSustitucion(
            propuestas=data.get("propuestas", []),
            advertencias=data.get("advertencias", []),
            resumen=data.get("resumen", ""),
            ai_razonamiento=razonamiento,
        )

    except Exception as e:
        logger.error("Error en ai_service.generar_propuestas_sustitucion: %s — activando fallback", e)
        return _fallback(profesores_disponibles)


def _fallback(profesores_disponibles: list[dict]) -> PropuestaSustitucion:
    """Fallback sin IA: ordena por carga semanal."""
    ordenados = sorted(profesores_disponibles, key=lambda p: p.get("sustituciones_semana", 0))
    return PropuestaSustitucion(
        propuestas=[
            {
                "teacher_id": p["id"],
                "nombre": p["nombre"],
                "puntuacion": 5.0,
                "razon_principal": "Seleccionado por disponibilidad (modo fallback — IA no disponible)",
                "pros": ["Tiene hora libre en este tramo"],
                "contras": ["Propuesta generada sin análisis inteligente"],
                "confianza": 0.4,
            }
            for p in ordenados[:3]
        ],
        advertencias=["IA no disponible — propuesta generada por criterio básico de disponibilidad"],
        resumen="Propuesta automática sin análisis inteligente",
        ai_razonamiento="",
    )
