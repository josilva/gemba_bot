import os
import openai
import json
from pathlib import Path

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Cargar claves del archivo .env
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# Cargar prompt base
with open("gemba_prompt.txt", "r", encoding="utf-8") as f:
    base_prompt = f.read()

# Cargar o iniciar registro
registro_file = "registro.json"
if Path(registro_file).exists():
    with open(registro_file, "r", encoding="utf-8") as f:
        registro = json.load(f)
else:
    registro = {}

# Funciones del bot
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "¡Hola! Soy tu asistente de Gemba Expedition. Podés escribirme para:\n"
        "- Registrar aprendizajes con /registrar\n"
        "- Hacerme preguntas con /consultar [tu pregunta]\n"
        "- O simplemente chatear conmigo 🙂"
    )

async def registrar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = str(update.message.from_user.id)
    texto = " ".join(context.args)
    if not texto:
        await update.message.reply_text("Usá /registrar seguido de tu reflexión. Ej: /registrar Hoy aprendí sobre liderazgo distribuido.")
        return
    registro.setdefault(user, []).append(texto)
    with open(registro_file, "w", encoding="utf-8") as f:
        json.dump(registro, f, indent=2, ensure_ascii=False)
    await update.message.reply_text("✅ ¡Registrado!")

async def consultar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pregunta = " ".join(context.args)
    if not pregunta:
        await update.message.reply_text("Usá /consultar seguido de tu pregunta. Ej: /consultar ¿Qué es autogestión?")
        return
    prompt = f"{base_prompt}\n\nUsuario: {pregunta}\nAsistente:"
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    await update.message.reply_text(response.choices[0].message.content.strip())

async def respuesta_libre(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje = update.message.text
    prompt = f"{base_prompt}\n\nUsuario: {mensaje}\nAsistente:"
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    await update.message.reply_text(response.choices[0].message.content.strip())

# Lanzar bot
if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("registrar", registrar))
    app.add_handler(CommandHandler("consultar", consultar))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, respuesta_libre))
    print("Bot corriendo...")
    app.run_polling()
