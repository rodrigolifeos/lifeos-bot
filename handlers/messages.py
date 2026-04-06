"""
Handler de mensajes libres — Claude interpreta texto y fotos
"""
import logging
import httpx
import base64
from telegram import Update
from telegram.ext import ContextTypes
from services.claude_service import interpretar_mensaje
from services.db_service import (
    guardar_comida, guardar_gasto, guardar_entrenamiento,
    guardar_tarea
)

logger = logging.getLogger(__name__)

EMOJIS = {
    "comida": "🥗",
    "gasto": "💸",
    "entrenamiento": "💪",
    "tarea": "✅",
    "evento_calendario": "📅",
    "consulta": "🤖",
    "desconocido": "🤔"
}


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    texto = update.message.text

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="typing"
    )

    try:
        resultado = interpretar_mensaje(texto)
        await _procesar_resultado(update, context, user_id, resultado)
    except Exception as e:
        logger.error(f"Error procesando mensaje: {e}")
        await update.message.reply_text(
            "Ups, algo salió mal procesando eso 😅 Intentá de nuevo."
        )


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="typing"
    )

    try:
        # Obtener la foto en mejor calidad
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)

        # Descargar la imagen
        async with httpx.AsyncClient() as client:
            response = await client.get(file.file_path)
            image_data = base64.standard_b64encode(response.content).decode("utf-8")

        # Enviar a Claude con visión
        import anthropic
        import os
        claude = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

        caption = update.message.caption or "¿Qué comida es esta y cuántas calorías tiene aproximadamente?"

        response = claude.messages.create(
            model="claude-opus-4-5",
            max_tokens=600,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": image_data
                        }
                    },
                    {
                        "type": "text",
                        "text": f"""Analizá esta foto de comida y respondé SOLO con un JSON así:
{{
  "tipo": "comida",
  "datos": {{
    "descripcion": "nombre del plato",
    "calorias_estimadas": número,
    "proteinas_g": número,
    "carbohidratos_g": número,
    "grasas_g": número,
    "momento": "almuerzo"
  }},
  "respuesta": "descripción amigable en español argentino de lo que ves y las calorías estimadas"
}}

Nota del usuario: {caption}
Si no es comida, igual devolvé el JSON con tipo "desconocido" y una respuesta explicando que no reconocés comida en la imagen."""
                    }
                ]
            }]
        )

        import json
        texto_respuesta = response.content[0].text.strip()
        if texto_respuesta.startswith("```"):
            texto_respuesta = texto_respuesta.split("```")[1]
            if texto_respuesta.startswith("json"):
                texto_respuesta = texto_respuesta[4:]

        resultado = json.loads(texto_respuesta)
        await _procesar_resultado(update, context, user_id, resultado)

    except Exception as e:
        logger.error(f"Error procesando foto: {e}")
        await update.message.reply_text(
            "No pude analizar la foto 😅 Intentá con una foto más clara o escribí la comida manualmente."
        )


async def _procesar_resultado(update, context, user_id, resultado):
    tipo = resultado.get("tipo", "desconocido")
    datos = resultado.get("datos", {})
    respuesta = resultado.get("respuesta", "Registrado 👍")

    guardado = False
    extra = ""

    if tipo == "comida":
        guardar_comida(user_id, datos)
        guardado = True
        cals = datos.get("calorias_estimadas", "?")
        prot = datos.get("proteinas_g", "?")
        extra = f"\n_~{cals} kcal · {prot}g proteína_"

    elif tipo == "gasto":
        guardar_gasto(user_id, datos)
        guardado = True
        monto = datos.get("monto", "?")
        cat = datos.get("categoria", "otro")
        extra = f"\n_${monto:,} · {cat}_"

    elif tipo == "entrenamiento":
        guardar_entrenamiento(user_id, datos)
        guardado = True
        series = datos.get("series")
        reps = datos.get("repeticiones")
        peso = datos.get("peso_kg")
        if series and reps:
            extra = f"\n_{series}x{reps}" + (f" · {peso}kg_" if peso else "_")

    elif tipo == "tarea":
        guardar_tarea(user_id, datos)
        guardado = True
        prioridad = datos.get("prioridad", "media")
        icons = {"alta": "🔴", "media": "🟡", "baja": "🟢"}
        extra = f"\n_{icons.get(prioridad, '')} Prioridad {prioridad}_"

    elif tipo == "evento_calendario":
        extra = "\n_⚠️ Google Calendar se integra en la Fase 2_"

    emoji = EMOJIS.get(tipo, "📝")
    mensaje_final = f"{emoji} {respuesta}{extra}"

    await update.message.reply_text(mensaje_final, parse_mode="Markdown")
