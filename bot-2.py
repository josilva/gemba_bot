import os
import openai
import json
import re
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from pathlib import Path

# Cargar .env
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# Cargar prompt base
with open("gemba_prompt.txt", "r", encoding="utf-8") as f:
    base_prompt = f.read()

# Cargar agenda
with open("gemba_agenda.json", "r", encoding="utf-8") as f:
    agenda = json.load(f)

# 🧠 Detectar fecha desde el mensaje
def normalizar_fecha(mensaje: str):
    mensaje = mensaje.lower()

    hoy = datetime.now()
    if "hoy" in mensaje:
        return hoy.strftime("%Y-%m-%d")
    if "mañana" in mensaje:
        return (hoy + timedelta(days=1)).strftime("%Y-%m-%d")
    if "pasado mañana" in mensaje:
        return (hoy + timedelta(days=2)).strftime("%Y-%m-%d")

    match = re.search(r"(\d{1,2})[\/\-](\d{1,2})", mensaje)
    if match:
        d, m = match.groups()
        return f"2025-{int(m):02d}-{int(d):02d}"

    match2 = re.search(r"(\d{1,2})\s+de\s+(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)", mensaje)
    if match2:
        dia, mes_nombre = match2.groups()
        meses = {'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4, 'mayo': 5,
                 'junio': 6, 'julio': 7, 'agosto': 8, 'septiembre': 9,
                 'octubre': 10, 'noviembre': 11, 'diciembre': 12}
        mes_num = meses.get(mes_nombre)
        return f"2025-{mes_num:02d}-{int(dia):02d}"

    return None

# 🧠 Detectar intención: lugar o actividades
def detectar_intencion(mensaje: str):
    mensaje = mensaje.lower()
    if any(palabra in mensaje for palabra in ["dónde", "direccion", "dirección", "lugar", "cómo llego"]):
        return "lugar"
    if any(palabra in mensaje for palabra in ["hora", "horario", "actividad", "qué hay", "que hay", "hacemos"]):
        return "actividad"
    return "desconocida"

# 📍 Responder solo direcciones
def responder_lugares(fecha: str):
    if fecha in agenda:
        actividades = agenda[fecha]
        respuesta = f"📍 Lugares para el {fecha}:\n"
        for act in actividades:
            if act['direccion']:
                respuesta += f"• {act['actividad']}\n  {act['direccion']}\n"
            if act['maps']:
                respuesta += f"  🗺️ {act['maps']}\n"
        return respuesta or "No encontré lugares para esa fecha."
    else:
        return f"No encontré actividades programadas para el {fecha}."

# 🕐 Responder actividades completas
def responder_agenda(fecha: str):
    if fecha in agenda:
        actividades = agenda[fecha]
        respuesta = f"📅 Actividades para el {fecha}:\n"
        for act in actividades:
            respuesta += f"🕐 {act['hora']} – {act['actividad']}\n"
            if act['direccion']:
                respuesta += f"📍 {act['direccion']}\n"
            if act['maps']:
                respuesta += f"🗺️ {act['maps']}\n"
            respuesta += "\n"
        return respuesta
    else:
        return f"No encontré actividades programadas para el {fecha}."

# Comandos
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
    """¡Hola! Soy tu asistente de Gemba Expedition. Podés escribirme para:
- Registrar aprendizajes con /registrar
- Hacerme preguntas o consultar la agenda
- O simplemente chatear conmigo 🙂"""
)


async def registrar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = str(update.message.from_user.id)
    texto = " ".join(context.args)
    if not texto:
        await update.message.reply_text("Usá /registrar seguido de tu reflexión.")
        return
    with open("registro.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    data.setdefault(user, []).append(texto)
    with open("registro.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    await update.message.reply_text("✅ ¡Registrado!")

async def respuesta_general(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje = update.message.text
    posible_fecha = normalizar_fecha(mensaje)
    intencion = detectar_intencion(mensaje)

    if posible_fecha:
        if intencion == "lugar":
            await update.message.reply_text(responder_lugares(posible_fecha))
            return
        if intencion == "actividad":
            await update.message.reply_text(responder_agenda(posible_fecha))
            return

    # Si no se detecta intención ni fecha → IA
    prompt = f"{base_prompt}\n\nUsuario: {mensaje}\nAsistente:"
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    await update.message.reply_text(response.choices[0].message.content.strip())

if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("registrar", registrar))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, respuesta_general))
    print("Bot corriendo con lógica híbrida mejorada...")
    app.run_polling()
