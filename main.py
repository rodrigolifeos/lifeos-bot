"""
Life OS Bot — Punto de entrada principal
"""
import logging
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from dotenv import load_dotenv
import os

from handlers.commands import cmd_hoy, cmd_score, cmd_gastos, cmd_pomodoro, cmd_start
from handlers.messages import handle_message, handle_photo

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("Falta TELEGRAM_BOT_TOKEN en el .env")

    app = ApplicationBuilder().token(token).build()

    # Comandos
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("hoy", cmd_hoy))
    app.add_handler(CommandHandler("score", cmd_score))
    app.add_handler(CommandHandler("gastos", cmd_gastos))
    app.add_handler(CommandHandler("pomodoro", cmd_pomodoro))

    # Mensajes de texto libres → procesados por Claude
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Fotos → Claude analiza calorías
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    print("🚀 Life OS Bot corriendo...")
    app.run_polling()

if __name__ == "__main__":
    main()
