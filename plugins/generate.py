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

@Client.on_message(filters.private & ~filters.forwarded & filters.text)
async def capture_user_input(client, message):
    """Capture messages from users waiting for input"""
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
        "<b>Please send your phone number which includes country code</b>\n<b>Example:</b> <code>+13124562345, +9171828181889</code>\n\n<b>Enter /cancel to cancel the process</b>",
        timeout=300
    )
    
    if phone_number_msg is None or phone_number_msg.text == '/cancel':
        return await message.reply('<b>Process cancelled!</b>')
    
    phone_number = phone_number_msg.text
    client = Client(":memory:", API_ID, API_HASH)
    await client.connect()
    await message.reply("Sending OTP...")
    
    try:
        code = await client.send_code(phone_number)
        
        phone_code_msg = await get_user_input(
            bot,
            user_id,
            "Please check for an OTP in official telegram account. If you got it, send OTP here after reading the below format.\n\nIf OTP is `12345`, **please send it as** `1 2 3 4 5`.\n\n**Enter /cancel to cancel the process**",
            timeout=600
        )
        
    except PhoneNumberInvalid:
        await message.reply('`PHONE_NUMBER` **is invalid.**')
        return
    
    if phone_code_msg is None or phone_code_msg.text == '/cancel':
        return await message.reply('<b>Process cancelled!</b>')
    
    try:
        phone_code = phone_code_msg.text.replace(" ", "")
        await client.sign_in(phone_number, code.phone_code_hash, phone_code)
    except PhoneCodeInvalid:
        await message.reply('**OTP is invalid.**')
        return
    except PhoneCodeExpired:
        await message.reply('**OTP is expired.**')
        return
    except SessionPasswordNeeded:
        two_step_msg = await get_user_input(
            bot,
            user_id,
            '**Your account has enabled two-step verification. Please provide the password.\n\nEnter /cancel to cancel the process**',
            timeout=300
        )
        
        if two_step_msg is None or two_step_msg.text == '/cancel':
            return await message.reply('<b>Process cancelled!</b>')
        
        try:
            password = two_step_msg.text
            await client.check_password(password=password)
        except PasswordHashInvalid:
            await message.reply('**Invalid Password Provided**')
            return
    
    string_session = await client.export_session_string()
    await client.disconnect()
    
    if len(string_session) < SESSION_STRING_SIZE:
        return await message.reply('<b>Invalid session string</b>')
    
    try:
        user_data = await db.get_session(message.from_user.id)
        if user_data is None:
            uclient = Client(":memory:", session_string=string_session, api_id=API_ID, api_hash=API_HASH)
            await uclient.connect()
            await db.set_session(message.from_user.id, session=string_session)
    except Exception as e:
        return await message.reply_text(f"<b>ERROR IN LOGIN:</b> `{e}`")
    
    await bot.send_message(message.from_user.id, "<b>Account Login Successfully.\n\nIf You Get Any Error Related To AUTH KEY Then /logout first and /login again</b>")


# Don't Remove Credit Tg - @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/@Tech_VJ
# Ask Doubt on telegram @KingVJ01
