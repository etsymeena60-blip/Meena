import os
import asyncio
import edge_tts
import io
import logging
import sys
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# --- உங்கள் டோக்கனை இங்கே சரியாகக் கொடுக்கவும் ---
TOKEN = "7797067340:AAH5OOJ0QxvmZ4msH3eErTb3YpDEoxGZwjQ"

# டெர்மினலில் தகவல்களைக் காட்ட லாகிங் செட்டப்
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
        # தமிழ் எழுத்துக்கள் இருக்கிறதா என்று பார்த்தல்
        is_tamil = any('\u0b80' <= char <= '\u0bff' for char in user_text)
        voice = "ta-IN-PallaviNeural" if is_tamil else "en-US-AndrewNeural"
        
        logger.info(f"🎙 Voice: {voice} தேர்வு செய்யப்பட்டுள்ளது.")

        # Edge-TTS கன்வெர்ஷன்
        communicate = edge_tts.Communicate(user_text, voice, rate="+10%")
        audio_stream = io.BytesIO()
        
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_stream.write(chunk["data"])
        
        audio_stream.seek(0)
        logger.info("✅ ஆடியோ உருவாக்கப்பட்டுவிட்டது.")

        # ஆடியோவை அனுப்புதல்
        await update.message.reply_voice(
            voice=audio_stream, 
            caption=f"✅ Language: {'Tamil' if is_tamil else 'English'}",
            write_timeout=300
        )
        await status_msg.delete()
        logger.info("📤 ஆடியோ வெற்றிகரமாக அனுப்பப்பட்டது!")

    except Exception as e:
        logger.error(f"❌ பிழை: {str(e)}")
        await status_msg.edit_text(f"❌ பிழை: {str(e)}")

async def run_bot():
    # TimeOut பிரச்சனையைத் தவிர்க்க அட்வான்ஸ்டு செட்டிங்ஸ்
    app = ApplicationBuilder().token(TOKEN).connect_timeout(40).read_timeout(40).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("🚀 பாட் ஸ்டார்ட் ஆகிறது...")
    
    await app.initialize()
    await app.start()
    
    logger.info("📡 பாட் மெசேஜ்களுக்காகக் காத்திருக்கிறது (Polling Started)...")
    
    # மெசேஜ்களைப் பெறத் தொடங்குதல்
    await app.updater.start_polling(drop_pending_updates=True)
    await asyncio.Event().wait()

if __name__ == '__main__':
    try:
        asyncio.run(run_bot())
    except Exception as final_err:
        logger.critical(f"💥 முக்கியமான எரர்: {final_err}")
