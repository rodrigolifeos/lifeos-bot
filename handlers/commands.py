"""
Handlers de comandos del bot
"""
import asyncio
from telegram import Update
from telegram.ext import ContextTypes
from services.db_service import (
    obtener_datos_dia, obtener_gastos_semana,
    obtener_comidas_hoy, obtener_entrenamientos_hoy, obtener_tareas_hoy
)
from services.claude_service import generar_resumen_dia, calcular_life_score


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nombre = update.effective_user.first_name
    msg = f"""👋 Hola {nombre}\\! Soy tu *Life OS*\\.

Hablame en lenguaje natural y yo registro todo automáticamente:

🥗 *Comidas* → "comí pollo con arroz"
💸 *Gastos* → "gasté 5000 en el super"
💪 *Ejercicio* → "hice 4x10 sentadillas"
✅ *Tareas* → "tengo que llamar al contador"
📅 *Eventos* → "mañana reunión a las 10"

*Comandos disponibles:*
/hoy \\- Resumen del día
/score \\- Tu Life Score
/gastos \\- Gastos de la semana
/pomodoro \\- Timer 25 min

¡Empecemos\\! 🚀"""

    await update.message.reply_text(msg, parse_mode="MarkdownV2")


async def cmd_hoy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    datos = obtener_datos_dia(user_id)
    comidas = datos["comidas"]
    gastos = datos["gastos"]
    entrenamientos = datos["entrenamientos"]
    tareas = datos["tareas"]

    # Resumen de comidas
    total_cals = sum(c.get("calorias_estimadas", 0) or 0 for c in comidas)
    lineas_comidas = f"🥗 *Comidas* ({len(comidas)} registros · ~{total_cals} kcal)"
    if comidas:
        for c in comidas[-3:]:
            lineas_comidas += f"\n  • {c['descripcion']}"

    # Resumen de gastos
    total_gastos = sum(g.get("monto", 0) or 0 for g in gastos)
    lineas_gastos = f"💸 *Gastos* (${total_gastos:,.0f})"
    if gastos:
        for g in gastos[-3:]:
            lineas_gastos += f"\n  • {g['descripcion']} — ${g['monto']:,.0f}"

    # Resumen de entrenamientos
    lineas_entreno = f"💪 *Entrenamiento* ({len(entrenamientos)} ejercicios)"
    if entrenamientos:
        for e in entrenamientos[-3:]:
            lineas_entreno += f"\n  • {e['ejercicio']}"

    # Resumen de tareas
    completadas = sum(1 for t in tareas if t.get("completada"))
    lineas_tareas = f"✅ *Tareas* ({completadas}/{len(tareas)} completadas)"
    if tareas:
        for t in tareas:
            check = "✓" if t.get("completada") else "○"
            lineas_tareas += f"\n  {check} {t['titulo']}"

    score = calcular_life_score(datos)
    score_emoji = "🔥" if score >= 80 else "⚡" if score >= 50 else "💤"

    msg = f"""📊 *Resumen de hoy*

{lineas_comidas}

{lineas_gastos}

{lineas_entreno}

{lineas_tareas}

{score_emoji} *Life Score: {score}/100*"""

    await update.message.reply_text(msg, parse_mode="Markdown")


async def cmd_score(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    datos = obtener_datos_dia(user_id)
    score = calcular_life_score(datos)
    resumen = generar_resumen_dia(datos)

    barra = _barra_progreso(score)
    msg = f"🎯 *Life Score del día: {score}/100*\n{barra}\n\n{resumen}"

    await update.message.reply_text(msg, parse_mode="Markdown")


async def cmd_gastos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    gastos = obtener_gastos_semana(user_id)

    if not gastos:
        await update.message.reply_text("No registraste gastos esta semana 📭")
        return

    total = sum(g.get("monto", 0) or 0 for g in gastos)

    # Agrupar por categoría
    por_cat = {}
    for g in gastos:
        cat = g.get("categoria", "otro")
        por_cat[cat] = por_cat.get(cat, 0) + (g.get("monto", 0) or 0)

    lineas = "\n".join(
        f"  • {cat}: ${monto:,.0f}"
        for cat, monto in sorted(por_cat.items(), key=lambda x: -x[1])
    )

    msg = f"""💸 *Gastos de los últimos 7 días*

{lineas}

💰 *Total: ${total:,.0f}*
📊 {len(gastos)} registros"""

    await update.message.reply_text(msg, parse_mode="Markdown")


async def cmd_pomodoro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🍅 *Pomodoro iniciado\\!* 25 minutos de foco total\\.\n\n"
        "Cerrá las redes sociales, apagá notificaciones y a laburar 💪",
        parse_mode="MarkdownV2"
    )

    # Esperar 25 minutos en background
    async def _timer():
        await asyncio.sleep(25 * 60)
        await update.message.reply_text(
            "⏰ *¡Se terminó el Pomodoro\\!* 25 minutos completados\\.\n\n"
            "Tomá 5 minutos de descanso y después seguimos 🚀",
            parse_mode="MarkdownV2"
        )

    asyncio.create_task(_timer())


def _barra_progreso(score: int) -> str:
    """Genera una barra de progreso visual con el score."""
    llenos = score // 10
    vacios = 10 - llenos
    return "█" * llenos + "░" * vacios + f" {score}%"
