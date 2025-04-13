# 🤖 Gemba Expedition Telegram Bot

Este bot acompaña a los participantes de Gemba Expedition durante su viaje por España, brindando acceso a la agenda, permitiendo registrar aprendizajes y consultando información mediante IA (GPT-4).

## ✨ Funcionalidades

- Consulta de agenda con lenguaje natural
- Registro de reflexiones con `/registrar`
- Respuestas inteligentes usando OpenAI
- Integración con Telegram

## ▶️ Cómo correrlo localmente

1. Cloná este repo y creá un archivo `.env` con tus claves:

```
TELEGRAM_TOKEN=tu_token
OPENAI_API_KEY=tu_clave
```

2. Instalá las dependencias:

```
pip install -r requirements.txt
```

3. Ejecutá el bot:

```
python bot.py
```

---

## 📁 Estructura del proyecto

```
gemba-bot/
├── bot.py
├── gemba_prompt.txt
├── gemba_agenda.json       # Ignorado por Git
├── registro.json           # Ignorado por Git
├── .env                    # Ignorado por Git
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 🚀 Ideas futuras

- Exportar reflexiones por usuario en CSV o PDF
- Recordatorios diarios automáticos
- Despliegue en Render o Railway
- Búsqueda semántica por embeddings (RAG)

---

💛 Construido con cariño para Gemba Expedition