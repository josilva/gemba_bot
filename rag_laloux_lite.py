import os
import fitz  # PyMuPDF
import openai
import numpy as np
from telegram import Update
from telegram.ext import ContextTypes
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)

# En memoria
embedding_store = []

# Ruta al PDF
PDF_PATH = "docs/Reinventing Organizations.pdf"

# Chunking básico por palabras
def split_text(text, max_words=150, overlap=30):
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        chunk = words[start:start + max_words]
        chunks.append(" ".join(chunk))
        start += max_words - overlap
    return chunks

# Cosine similarity
def cosine_similarity(a, b):
    a, b = np.array(a), np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

# Inicializar y generar embeddings
def preparar_laloux():
    if not os.path.exists(PDF_PATH):
        print("❌ PDF no encontrado en", PDF_PATH)
        return

    doc = fitz.open(PDF_PATH)
    full_text = ""
    for page in doc:
        full_text += page.get_text()

    chunks = split_text(full_text)
    print(f"📚 Procesando {len(chunks)} fragmentos...")

    for i, chunk in enumerate(chunks):
        embedding = openai_client.embeddings.create(
            input=chunk,
            model="text-embedding-3-small"
        ).data[0].embedding
        embedding_store.append({"text": chunk, "embedding": embedding})

    print("✅ Embeddings listos (modo memoria).")

# Consultar RAG con similaridad manual
def consultar_laloux(pregunta, k=3):
    pregunta_embedding = openai_client.embeddings.create(
        input=pregunta,
        model="text-embedding-3-small"
    ).data[0].embedding

    # Calcular similitud con cada chunk
    scored_chunks = [
        (cosine_similarity(pregunta_embedding, item["embedding"]), item["text"])
        for item in embedding_store
    ]
    top_chunks = sorted(scored_chunks, key=lambda x: x[0], reverse=True)[:k]
    contexto = "\n---\n".join(chunk[1] for chunk in top_chunks)

    # Responder con GPT-4
    response = openai_client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Usá el siguiente contexto del libro 'Reinventing Organizations' para responder de forma clara y concreta."},
            {"role": "user", "content": f"Contexto:\n{contexto}\n\nPregunta: {pregunta}"}
        ],
        temperature=0.3
    )
    return response.choices[0].message.content.strip()

# Handler para el bot
async def responder_laloux(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pregunta = " ".join(context.args)
    if not pregunta:
        await update.message.reply_text("📘 Usá el comando así: /laloux ¿Qué son las organizaciones teal?")
        return

    await update.message.reply_text("🔍 Buscando en el libro...")

    respuesta = consultar_laloux(pregunta)
    await update.message.reply_text(respuesta)