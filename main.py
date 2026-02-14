import os
import asyncio
import edge_tts
import io
import logging
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# --- Render Dummy Server ---
def run_dummy_server():
    class SimpleHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Bot is Running!")
    port = int(os.environ.get('PORT', 8080))
    server = HTTPServer(('', port), SimpleHandler)
    server.serve_forever()

# --- TOKEN ---
TOKEN = "7797067340:AAFKmt4Dcat_bCiVMvElZAyeu5ahVocXLPU"

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO, handlers=[logging.StreamHandler(sys.stdout)])
logger = logging.getLogger(__name__)

# குரல் பட்டியல்கள்
VOICES = {
    "tam_girl1": "ta-IN-PallaviNeural",
    "tam_girl2": "ta-IN-KaniNeural",
    "tam_boy1": "ta-IN-ValluvarNeural",
    "tam_boy2": "ta-MY-KaniNeural",
    "tam_boy3": "ta-LK-KumarNeural",
    "eng_girl1": "en-US-AvaNeural",
    "eng_girl2": "en-US-EmmaNeural",
    "eng_boy1": "en-US-AndrewNeural",
    "eng_boy2": "en-GB-ThomasNeural",
    "eng_boy3": "en-US-BrianNeural",
    "hin_girl1": "hi-IN-SwaraNeural",
    "hin_girl2": "hi-IN-AnanyaNeural",
    "hin_boy1": "hi-IN-MadhurNeural",
    "hin_boy2": "hi-IN-SouraseniNeural",
    "hin_boy3": "hi-IN-ManoharNeural"
}

# பயனர் விருப்பத்தைச் சேமிக்க
user_settings = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("தமிழ் 🇮🇳", callback_data='lang_tam'),
         InlineKeyboardButton("English 🇺🇸", callback_data='lang_eng'),
         InlineKeyboardButton("Hindi 🇮🇳", callback_data='lang_hin')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("👋 வணக்கம்! மொழியைத் தேர்ந்தெடுக்கவும்:", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith('lang_'):
        lang = data.split('_')[1]
        buttons = []
        if lang == 'tam':
            buttons = [
                [InlineKeyboardButton("பெண் குரல் 1", callback_data='v_tam_girl1'), InlineKeyboardButton("பெண் குரல் 2", callback_data='v_tam_girl2')],
                [InlineKeyboardButton("ஆண் குரல் 1", callback_data='v_tam_boy1'), InlineKeyboardButton("ஆண் குரல் 2", callback_data='v_tam_boy2')],
                [InlineKeyboardButton("ஆண் குரல் 3", callback_data='v_tam_boy3')]
            ]
        elif lang == 'eng':
            buttons = [
                [InlineKeyboardButton("Girl 1 (Ava)", callback_data='v_eng_girl1'), InlineKeyboardButton("Girl 2 (Emma)", callback_data='v_eng_girl2')],
                [InlineKeyboardButton("Boy 1 (Andrew)", callback_data='v_eng_boy1'), InlineKeyboardButton("Boy 2 (Thomas)", callback_data='v_eng_boy2')],
                [InlineKeyboardButton("Boy 3 (Brian)", callback_data='v_eng_boy3')]
            ]
        elif lang == 'hin':
            buttons = [
                [InlineKeyboardButton("Girl 1", callback_data='v_hin_girl1'), InlineKeyboardButton("Girl 2", callback_data='v_hin_girl2')],
                [InlineKeyboardButton("Boy 1", callback_data='v_hin_boy1'), InlineKeyboardButton("Boy 2", callback_data='v_hin_boy2')],
                [InlineKeyboardButton("Boy 3", callback_data='v_hin_boy3')]
            ]
        await query.edit_message_text(f"குரலைத் தேர்ந்தெடுக்கவும் ({lang}):", reply_markup=InlineKeyboardMarkup(buttons))

    elif data.startswith('v_'):
        voice_key = data.split('_', 1)[1]
        user_settings[query.from_user.id] = VOICES[voice_key]
        await query.edit_message_text(f"✅ குரல் மாற்றப்பட்டது! இப்போது டெக்ஸ்ட் அனுப்பவும்.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_text = update.message.text
    # டிபால்ட்டாக ஒரு குரல்
    voice = user_settings.get(user_id, "ta-IN-PallaviNeural")
    
    status_msg = await update.message.reply_text("🚀 Converting to Audio...")
    try:
        communicate = edge_tts.Communicate(user_text, voice)
        audio_stream = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_stream.write(chunk["data"])
        audio_stream.seek(0)
        await update.message.reply_voice(voice=audio_stream, caption="✅ Meena TTS Multi-Voice")
        await status_msg.delete()
    except Exception as e:
        await status_msg.edit_text(f"❌ Error: {str(e)}")

async def run_bot():
    threading.Thread(target=run_dummy_server, daemon=True).start()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("🚀 Bot Started with Multi-Voice Menu...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)
    await asyncio.Event().wait()

if __name__ == '__main__':
    asyncio.run(run_bot())
