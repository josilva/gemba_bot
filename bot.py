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

# Cargar calendario
with open("agenda/gemba_agenda.json", "r", encoding="utf-8") as f:
    agenda = json.load(f)

def generar_contexto_agenda(agenda):
    texto = "Esta es la agenda de visitas programadas:\n\n"
    for fecha in sorted(agenda.keys()):
        texto += f"📅 {fecha}\n"
        for act in agenda[fecha]:
            texto += f"  - {act['hora']}: {act['actividad']}\n"
            if act["direccion"]:
                texto += f"    Dirección: {act['direccion']}\n"
            if act["maps"]:
                texto += f"    Maps: {act['maps']}\n"
        texto += "\n"
    return texto.strip()

agenda_contexto = generar_contexto_agenda(agenda)


# Detección mejorada de fechas
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

def detectar_intencion(mensaje: str):
    mensaje = mensaje.lower()
    if any(p in mensaje for p in ["dónde", "direccion", "dirección", "lugar", "cómo llego"]):
        return "lugar"
    if any(p in mensaje for p in ["hora", "horario", "actividad", "qué hay", "que hay", "hacemos"]):
        return "actividad"
    return "desconocida"

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

    # Detectar si es una consulta estructurada
    if posible_fecha:
        if intencion == "lugar":
            await update.message.reply_text(responder_lugares(posible_fecha))
            return
        elif intencion == "actividad":
            await update.message.reply_text(responder_agenda(posible_fecha))
            return

    # Opción B – si no hay fecha ni intención, le pasamos directamente el mensaje
    if not posible_fecha and intencion == "desconocida":
        prompt_con_agenda = mensaje
    else:
        prompt_con_agenda = f"{base_prompt}\n\n{agenda_contexto}\n\nUsuario: {mensaje}\nAsistente:"

    response = openai.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": base_prompt},
        {"role": "user", "content": agenda_contexto},
        {"role": "user", "content": mensaje}
    ],
    temperature=0.3
    )

    await update.message.reply_text(response.choices[0].message.content.strip())


if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("registrar", registrar))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, respuesta_general))
    print("Bot corriendo con lógica refinada...")
    app.run_polling()
