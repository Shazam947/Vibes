import os
import asyncio
import aiohttp
import youtube_dl
import logging
from dotenv import load_dotenv

# Pyrogram
from pyrogram import Client, filters
# PyTgCalls
from pytgcalls import PyTgCalls
from pytgcalls import Stream
from pytgcalls.types import Update
from pytgcalls.exceptions import NoActiveGroupCall

# FFmpeg for audio processing
import ffmpeg

# Load environment variables from .env file
load_dotenv()

# Basic logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Environment Variables ---
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Pyrogram client for bot (with session name)
# This will create a file named "vc_bot.session"
app = Client(
    "vc_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# PyTgCalls client
pytgcalls = PyTgCalls(app)

# --- State Management ---
current_playing = {} # {chat_id: "title of song"}

# --- YouTube Downloader Options ---
ydl_opts = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    'outtmpl': 'downloads/%(id)s.%(ext)s',
}

# --- Command Handlers ---

@app.on_message(filters.command("join") & filters.group)
async def join_command(client, message):
    chat_id = message.chat.id
    if len(message.command) < 2:
        await message.reply_text("Please provide a link to a song or video.")
        return

    link = message.command[1]

    await app.send_chat_action(chat_id, "typing")

    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link, download=True)
            file_path = ydl.prepare_filename(info)
            song_title = info.get('title', 'Unknown Title')

        await pytgcalls.join_group_call(
            chat_id,
            Stream(file_path)
        )
        current_playing[chat_id] = song_title
        await message.reply_text(f"🎧 **Playing**: `{song_title}`")
        logger.info(f"[{chat_id}] Started playing: {song_title}")

    except NoActiveGroupCall:
        await message.reply_text("There is no active voice chat. Please start one and then try again.")
    except Exception as e:
        logger.error(f"Error joining VC or playing song: {e}", exc_info=True)
        await message.reply_text(f"Oops! I couldn't join the voice chat. Error: `{e}`")

@app.on_message(filters.command("leave") & filters.group)
async def leave_command(client, message):
    chat_id = message.chat.id
    try:
        await pytgcalls.leave_group_call(chat_id)
        if chat_id in current_playing:
            del current_playing[chat_id]
        await message.reply_text("VC se nikal gaya hoon.")
        logger.info(f"[{chat_id}] Left the voice chat.")
    except Exception as e:
        await message.reply_text(f"Error: {e}")

@app.on_message(filters.command("pause") & filters.group)
async def pause_command(client, message):
    chat_id = message.chat.id
    try:
        await pytgcalls.pause_stream(chat_id)
        await message.reply_text("🎵 Music paused.")
        logger.info(f"[{chat_id}] Music paused.")
    except Exception as e:
        await message.reply_text(f"Error: {e}")

@app.on_message(filters.command("resume") & filters.group)
async def resume_command(client, message):
    chat_id = message.chat.id
    try:
        await pytgcalls.resume_stream(chat_id)
        await message.reply_text("▶️ Music resumed.")
        logger.info(f"[{chat_id}] Music resumed.")
    except Exception as e:
        await message.reply_text(f"Error: {e}")

# --- Main Bot Logic ---
async def main():
    await app.start()
    await pytgcalls.start()
    logger.info("VC bot has started.")
    await app.idle()

if __name__ == "__main__":
    if not os.path.exists("downloads"):
        os.makedirs("downloads")
    app.run(main())
