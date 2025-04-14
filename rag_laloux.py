import os
import fitz  # PyMuPDF
import tiktoken
import openai
import chromadb
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ContextTypes

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Inicializar Chroma en memoria
chroma_client = chromadb.Client()
collection = chroma_client.create_collection(name="laloux")

# Ruta al PDF
PDF_PATH = "docs/Reinventing Organizations.pdf"

def split_text(text, max_tokens=500, overlap=50):
    enc = tiktoken.encoding_for_model("gpt-3.5-turbo")
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        chunk = words[start:start + max_tokens]
        token_count = len(enc.encode(" ".join(chunk)))
        while token_count > max_tokens:
            chunk = chunk[:-1]
            token_count = len(enc.encode(" ".join(chunk)))
        chunks.append(" ".join(chunk))
        start += max_tokens - overlap
    return chunks

def preparar_laloux():
    if not os.path.exists(PDF_PATH):
        print("❌ PDF no encontrado en", PDF_PATH)
        return

    doc = fitz.open(PDF_PATH)
    full_text = ""
    for page in doc:
        full_text += page.get_text()

    chunks = split_text(full_text)
    print(f"📚 Generando embeddings para {len(chunks)} fragmentos...")
    for i, chunk in enumerate(chunks):
        embedding = openai_client.embeddings.create(
            input=chunk,
            model="text-embedding-3-small"
        ).data[0].embedding
        collection.add(documents=[chunk], embeddings=[embedding], ids=[f"chunk-{i}"])
    print("✅ Embeddings cargados para Laloux.")

def consultar_laloux(pregunta: str, k=3) -> str:
    embedding = openai_client.embeddings.create(
        input=pregunta,
        model="text-embedding-3-small"
    ).data[0].embedding
    results = collection.query(query_embeddings=[embedding], n_results=k)
    contexto = "\n---\n".join(results["documents"][0])

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