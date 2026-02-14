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

# --- Render Dummy Server (பாட்டை எப்போதும் ஓட வைக்க) ---
def run_dummy_server():
    class SimpleHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Bot is Running!")
    port = int(os.environ.get('PORT', 8080))
    server = HTTPServer(('', port), SimpleHandler)
    server.serve_forever()

# --- உங்கள் டோக்கனை இங்கே கொடுக்கவும் ---
TOKEN = "7797067340:AAFKmt4Dcat_bCiVMvElZAyeu5ahVocXLPU"

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO, handlers=[logging.StreamHandler(sys.stdout)])
logger = logging.getLogger(__name__)

# 🎙️ 15 குரல்கள் (தமிழ், ஆங்கிலம், ஹிந்தி)
VOICES = {
    "tam_g1": "ta-IN-PallaviNeural", "tam_g2": "ta-IN-KaniNeural",
    "tam_b1": "ta-IN-ValluvarNeural", "tam_b2": "ta-MY-KaniNeural", "tam_b3": "ta-LK-KumarNeural",
    "eng_g1": "en-US-AvaNeural", "eng_g2": "en-US-EmmaNeural",
    "eng_b1": "en-US-AndrewNeural", "eng_b2": "en-GB-ThomasNeural", "eng_b3": "en-US-BrianNeural",
    "hin_g1": "hi-IN-SwaraNeural", "hin_g2": "hi-IN-AnanyaNeural",
    "hin_b1": "hi-IN-MadhurNeural", "hin_b2": "hi-IN-SouraseniNeural", "hin_b3": "hi-IN-ManoharNeural"
}

user_settings = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("தமிழ் 🇮🇳", callback_data='lang_tam'),
         InlineKeyboardButton("English 🇺🇸", callback_data='lang_eng'),
         InlineKeyboardButton("Hindi 🇮🇳", callback_data='lang_hin')]
    ]
    await update.message.reply_text("👋 மொழியைத் தேர்ந்தெடுக்கவும் / Select Language:", reply_markup=InlineKeyboardMarkup(keyboard))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith('lang_'):
        lang = data.split('_')[1]
        buttons = []
        # தமிழ், ஆங்கிலம், ஹிந்தி பட்டன்கள் (5 குரல்கள் வீதம்)
        if lang == 'tam':
            buttons = [[InlineKeyboardButton("பெண் 1", callback_data='v_tam_g1'), InlineKeyboardButton("பெண் 2", callback_data='v_tam_g2')],
                       [InlineKeyboardButton("ஆண் 1", callback_data='v_tam_b1'), InlineKeyboardButton("ஆண் 2", callback_data='v_tam_b2')],
                       [InlineKeyboardButton("ஆண் 3", callback_data='v_tam_b3')]]
        elif lang == 'eng':
            buttons = [[InlineKeyboardButton("Girl 1", callback_data='v_eng_g1'), InlineKeyboardButton("Girl 2", callback_data='v_eng_g2')],
                       [InlineKeyboardButton("Boy 1", callback_data='v_eng_b1'), InlineKeyboardButton("Boy 2", callback_data='v_eng_b2')],
                       [InlineKeyboardButton("Boy 3", callback_data='v_eng_b3')]]
        elif lang == 'hin':
            buttons = [[InlineKeyboardButton("Girl 1", callback_data='v_hin_g1'), InlineKeyboardButton("Girl 2", callback_data='v_hin_g2')],
                       [InlineKeyboardButton("Boy 1", callback_data='v_hin_b1'), InlineKeyboardButton("Boy 2", callback_data='v_hin_b2')],
                       [InlineKeyboardButton("Boy 3", callback_data='v_hin_b3')]]
        await query.edit_message_text(f"குரலைத் தேர்ந்தெடுக்கவும் ({lang}):", reply_markup=InlineKeyboardMarkup(buttons))

    elif data.startswith('v_'):
        voice_key = data.split('_', 1)[1]
        user_settings[query.from_user.id] = VOICES[voice_key]
        await query.edit_message_text(f"✅ குரல் செட் செய்யப்பட்டது! இப்போது டெக்ஸ்ட் அனுப்பவும்.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_text = update.message.text
    voice = user_settings.get(user_id, "ta-IN-PallaviNeural")
    
    status_msg = await update.message.reply_text("🚀 Converting (Slow Speed)...")
    try:
        # ⚡ வேகம் இங்கே குறைக்கப்பட்டுள்ளது (rate="-15%")
        communicate = edge_tts.Communicate(user_text, voice, rate="-15%")
        audio_stream = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_stream.write(chunk["data"])
        audio_stream.seek(0)
        await update.message.reply_voice(voice=audio_stream, caption="✅ Meena TTS Output")
        await status_msg.delete()
    except Exception as e:
        await status_msg.edit_text(f"❌ Error: {str(e)}")

async def run_bot():
    threading.Thread(target=run_dummy_server, daemon=True).start()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("🚀 Bot Started with Slow Speed & Menu...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)
    await asyncio.Event().wait()

if __name__ == '__main__':
    asyncio.run(run_bot())
