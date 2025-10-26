# Don't Remove Credit Tg - @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/@Tech_VJ
# Ask Doubt on telegram @KingVJ01

import traceback
import asyncio
from pyrogram.types import Message
from pyrogram import Client, filters
from asyncio.exceptions import TimeoutError
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import (
    ApiIdInvalid,
    PhoneNumberInvalid,
    PhoneCodeInvalid,
    PhoneCodeExpired,
    SessionPasswordNeeded,
    PasswordHashInvalid
)
from config import API_ID, API_HASH
from plugins.database import db

SESSION_STRING_SIZE = 351

pending_responses = {}

async def get_user_input(client, user_id, prompt_text, timeout=600):
    """Wait for user input with a prompt message - works with all Pyrogram versions"""
    await client.send_message(user_id, prompt_text)
    
    # Create an event to signal when a message arrives
    event = asyncio.Event()
    pending_responses[user_id] = {"event": event, "message": None}
    
    try:
        # Wait for the message with timeout
        await asyncio.wait_for(event.wait(), timeout=timeout)
        message = pending_responses[user_id]["message"]
        del pending_responses[user_id]
        return message
    except asyncio.TimeoutError:
        del pending_responses[user_id]
        await client.send_message(user_id, "⏱️ **Request timed out. Please try again.**")
        return None

@Client.on_message(filters.private & ~filters.forwarded & filters.text & ~filters.command)
async def capture_user_input(client, message):
    """Capture messages from users waiting for input - skip commands"""
    user_id = message.from_user.id
    
    # If this user is waiting for input, store the message and signal the event
    if user_id in pending_responses:
        pending_responses[user_id]["message"] = message
        pending_responses[user_id]["event"].set()

@Client.on_message(filters.private & ~filters.forwarded & filters.command(["logout"]))
async def logout(client, message):
    user_data = await db.get_session(message.from_user.id)  
    if user_data is None:
        return 
    await db.set_session(message.from_user.id, session=None)  
    await message.reply("**Logout Successfully** ♦")

@Client.on_message(filters.private & ~filters.forwarded & filters.command(["login"]))
async def main(bot: Client, message: Message):
    user_data = await db.get_session(message.from_user.id)
    if user_data is not None:
        await message.reply("**Your Are Already Logged In. First /logout Your Old Session. Then Do Login.**")
        return 
    user_id = int(message.from_user.id)
    
    phone_number_msg = await get_user_input(
        bot, 
        user_id, 
        "<b>Please send your phone number which includes country code</b>\n<b>Example:</b> <code>+13124562345, +9171828181889
    
