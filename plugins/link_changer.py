# Link Auto-Changer Core Functionality
import asyncio
import random
import string
import time
from pyrogram import Client
from plugins.database import db

class LinkChanger:
    def __init__(self):
        self.active_tasks = {}
        self.bot_client = None  # Store bot client for sending logs

    def set_bot_client(self, client):
        """Set the bot client for sending log messages"""
        self.bot_client = client

    def generate_random_suffix(self):
        """Generate random 2 characters (letters or digits)"""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=2))

    async def change_channel_link(self, user_session, channel_id, base_username):
        """Change the channel's public link with random suffix"""
        try:
            # Create client from user session
            from config import API_ID, API_HASH
            client = Client(":memory:", session_string=user_session, api_id=API_ID, api_hash=API_HASH)
            await client.connect()
            
            # Generate new username
            new_suffix = self.generate_random_suffix()
            new_username = f"{base_username}_{new_suffix}"
            
            # Try to set the new username
            max_attempts = 5
            for attempt in range(max_attempts):
                try:
                    await client.set_chat_username(channel_id, new_username)
                    await client.disconnect()
                    await db.update_last_changed(channel_id, time.time())
                    return True, new_username, None
                except Exception as e:
                    if "USERNAME_OCCUPIED" in str(e) or "occupied" in str(e).lower():
                        # Username taken, try another
                        new_suffix = self.generate_random_suffix()
                        new_username = f"{base_username}_{new_suffix}"
                        continue
                    else:
                        await client.disconnect()
                        return False, None, str(e)
            
            await client.disconnect()
            return False, None, "Could not find available username after 5 attempts"
        except Exception as e:
            return False, None, str(e)

    async def send_log_message(self, user_id, channel_id, new_username=None, error=None, interval=None):
        """Send log message to LOG_CHANNEL"""
        if not self.bot_client:
            return
        
        try:
            from config import LOG_CHANNEL
            
            if error:
                # Error log
                log_text = f"""⚠️ <b>Error changing link for channel:</b> <code>{channel_id}</code>
<b>User ID:</b> <code>{user_id}</code>
<b>Reason:</b> {error}"""
            else:
                # Success log
                log_text = f"""🔄 <b>Link changed for channel:</b> <code>{channel_id}</code>
<b>New username:</b> @{new_username}
<b>User ID:</b> <code>{user_id}</code>
<b>Interval:</b> {interval}s"""
            
            await self.bot_client.send_message(LOG_CHANNEL, log_text)
        except Exception as e:
            print(f"[v0] Failed to send log message: {e}")

    async def start_channel_rotation(self, user_id, channel_id, base_username, interval):
        """Start automatic link rotation for a channel"""
        task_key = (user_id, channel_id)  # Use tuple instead of string for better key management
        
        if task_key in self.active_tasks:
            return False, "Channel rotation already active"
        
        try:
            user_session = await db.get_session(user_id)
            if not user_session:
                return False, "User session not found"
            
            async def rotation_loop():
                while True:
                    try:
                        success, new_username, error = await self.change_channel_link(user_session, channel_id, base_username)
                        if success:
                            print(f"[v0] Link changed for channel {channel_id}: {new_username}")
                            await self.send_log_message(user_id, channel_id, new_username=new_username, interval=interval)
                        else:
                            print(f"[v0] Failed to change link for channel {channel_id}: {error}")
                            await self.send_log_message(user_id, channel_id, error=error)
                        await asyncio.sleep(interval)
                    except asyncio.CancelledError:
                        break
                    except Exception as e:
                        print(f"[v0] Error in rotation loop: {e}")
                        await self.send_log_message(user_id, channel_id, error=f"Unexpected error: {str(e)}")
                        await asyncio.sleep(interval)
            
            task = asyncio.create_task(rotation_loop())
            self.active_tasks[task_key] = task
            return True, "Channel rotation started"
        except Exception as e:
            return False, str(e)

    async def stop_channel_rotation(self, user_id, channel_id):
        """Stop automatic link rotation for a channel"""
        task_key = (user_id, channel_id)  # Use tuple instead of string
        
        if task_key not in self.active_tasks:
            return False, "Channel rotation not active"
        
        try:
            self.active_tasks[task_key].cancel()
            del self.active_tasks[task_key]
            return True, "Channel rotation stopped"
        except Exception as e:
            return False, str(e)

    async def resume_channel_rotation(self, user_id, channel_id, base_username, interval):
        """Resume automatic link rotation for a channel"""
        return await self.start_channel_rotation(user_id, channel_id, base_username, interval)

    async def get_active_channels_for_user(self, user_id):
        """Get all active channels for a user"""
        return await db.get_user_channels(user_id)

link_changer = LinkChanger()

