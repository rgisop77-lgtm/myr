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
    """Capture messages from users waiting for input - skip commands"""
    user_id = message.from_user.id
    
    if message.text.startswith('/'):
        return
    
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
        "<b>Please send your phone number which includes country code</b>\n<b>Example:</b> <code>+13124562345, +9171828181889</code>"
    )
    
    if phone_number_msg is None:
        return
    
    phone_number = phone_number_msg.text
    
    try:
        async with Client(
            name=str(user_id),
            api_id=API_ID,
            api_hash=API_HASH,
            phone_number=phone_number,
            in_memory=True
        ) as app:
            
            # Request OTP
            sent_code = await app.send_code(phone_number)
            
            # Get OTP from user
            otp_msg = await get_user_input(
                bot,
                user_id,
                "<b>Please send the OTP code you received</b>"
            )
            
            if otp_msg is None:
                return
            
            otp_code = otp_msg.text
            
            try:
                # Sign in with OTP
                await app.sign_in(phone_number, sent_code.phone_code_hash, otp_code)
                
            except SessionPasswordNeeded:
                # 2FA is enabled, ask for password
                password_msg = await get_user_input(
                    bot,
                    user_id,
                    "<b>Your account has 2FA enabled. Please send your password</b>"
                )
                
                if password_msg is None:
                    return
                
                password = password_msg.text
                
                try:
                    await app.check_password(password)
                except PasswordHashInvalid:
                    await bot.send_message(user_id, "❌ **Invalid password. Login failed.**")
                    return
            
            # Get session string
            session_string = await app.export_session_string()
            
            # Save to database
            await db.set_session(user_id, session=session_string)
            
            await bot.send_message(
                user_id,
                f"✅ **Login Successful!**\n\n**Session String Length:** `{len(session_string)}`"
            )
            
    except ApiIdInvalid:
        await bot.send_message(user_id, "❌ **Invalid API ID or API Hash**")
    except PhoneNumberInvalid:
        await bot.send_message(user_id, "❌ **Invalid phone number format**")
    except PhoneCodeInvalid:
        await bot.send_message(user_id, "❌ **Invalid OTP code**")
    except PhoneCodeExpired:
        await bot.send_message(user_id, "❌ **OTP code expired. Please try again.**")
    except Exception as e:
        await bot.send_message(user_id, f"❌ **Error:** `{str(e)}`")
        traceback.print_exc()
        
