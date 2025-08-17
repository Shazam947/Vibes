import os
import asyncio
import logging
from dotenv import load_dotenv

# Pyrogram
from pyrogram import Client, filters
# Py-TgCalls (version 3.0.0.dev24 compatible imports)
from py_tgcalls import PyTgCalls
from py_tgcalls.types import StreamAudio, StreamVideo, JoinedGroupCall
from py_tgcalls.exceptions import NoActiveGroupCall

# --- Environment Variables ---
load_dotenv()
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Basic logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pyrogram client for bot
app = Client(
    "vc_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Py-TgCalls client
pytgcalls = PyTgCalls(app)

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
        await pytgcalls.join_group_call(
            chat_id,
            StreamAudio(link)
        )
        await message.reply_text(f"🎧 **Playing**: [Stream]({link})")
        logger.info(f"[{chat_id}] Started playing: {link}")

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
    app.run(main())
