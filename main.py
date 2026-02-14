import os
import asyncio
import edge_tts
import io
import logging
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# --- Render-க்கான டமி சர்வர் (பாட் நிற்காமல் இருக்க) ---
def run_dummy_server():
    class SimpleHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Bot is Running!")
    
    port = int(os.environ.get('PORT', 8080))
    server = HTTPServer(('', port), SimpleHandler)
    server.serve_forever()

# --- உங்கள் டோக்கனை இங்கே சரியாகக் கொடுக்கவும் ---
TOKEN = "7797067340:AAFKmt4Dcat_bCiVMvElZAyeu5ahVocXLPU"

# லாகிங் செட்டப்
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("✅ Start command received!")
    await update.message.reply_text("👋 பாட் தயாராக உள்ளது! டெக்ஸ்டை அனுப்பவும்.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    logger.info(f"📩 மெசேஜ் வந்துள்ளது: {user_text[:30]}...")
    status_msg = await update.message.reply_text("🚀 கன்வெர்ட் ஆகிறது...")

    try:
        is_tamil = any('\u0b80' <= char <= '\u0bff' for char in user_text)
        voice = "ta-IN-PallaviNeural" if is_tamil else "en-US-AndrewNeural"
        communicate = edge_tts.Communicate(user_text, voice, rate="+10%")
        audio_stream = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_stream.write(chunk["data"])
        audio_stream.seek(0)
        await update.message.reply_voice(voice=audio_stream, caption="✅ Meena TTS Output")
        await status_msg.delete()
    except Exception as e:
        logger.error(f"❌ பிழை: {str(e)}")
        await status_msg.edit_text(f"❌ பிழை: {str(e)}")

async def run_bot():
    # டமி சர்வரைத் தொடங்குகிறது (Render-க்காக)
    threading.Thread(target=run_dummy_server, daemon=True).start()
    
    app = ApplicationBuilder().token(TOKEN).connect_timeout(40).read_timeout(40).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("🚀 பாட் ஸ்டார்ட் ஆகிறது...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)
    await asyncio.Event().wait()

if __name__ == '__main__':
    asyncio.run(run_bot())
