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
            new_username = f"{base_username}{new_suffix}"
            
            # Try to set the new username
            max_attempts = 5
            for attempt in range(max_attempts):
                try:
                    await client.set_chat_username(channel_id, new_username)
                    await client.disconnect()
                    await db.update_last_changed(channel_id, time.time())
                    return True, new_username
                except Exception as e:
                    if "USERNAME_OCCUPIED" in str(e) or "occupied" in str(e).lower():
                        # Username taken, try another
                        new_suffix = self.generate_random_suffix()
                        new_username = f"{base_username}{new_suffix}"
                        continue
                    else:
                        await client.disconnect()
                        return False, str(e)
            
            await client.disconnect()
            return False, "Could not find available username after 5 attempts"
        except Exception as e:
            return False, str(e)

    async def start_channel_rotation(self, user_id, channel_id, base_username, interval):
        """Start automatic link rotation for a channel"""
        task_key = f"{user_id}_{channel_id}"
        
        if task_key in self.active_tasks:
            return False, "Channel rotation already active"
        
        try:
            user_session = await db.get_session(user_id)
            if not user_session:
                return False, "User session not found"
            
            async def rotation_loop():
                while True:
                    try:
                        success, result = await self.change_channel_link(user_session, channel_id, base_username)
                        if success:
                            print(f"[v0] Link changed for channel {channel_id}: {result}")
                        else:
                            print(f"[v0] Failed to change link for channel {channel_id}: {result}")
                        await asyncio.sleep(interval)
                    except asyncio.CancelledError:
                        break
                    except Exception as e:
                        print(f"[v0] Error in rotation loop: {e}")
                        await asyncio.sleep(interval)
            
            task = asyncio.create_task(rotation_loop())
            self.active_tasks[task_key] = task
            return True, "Channel rotation started"
        except Exception as e:
            return False, str(e)

    async def stop_channel_rotation(self, user_id, channel_id):
        """Stop automatic link rotation for a channel"""
        task_key = f"{user_id}_{channel_id}"
        
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
