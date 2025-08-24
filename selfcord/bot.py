import asyncio
import json
import logging
import time
from typing import Dict, Any, Optional
import aiohttp

from gateway import GatewayHandler
from commands import CommandSystem
from utils import RateLimiter

class DiscordUser:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.user_id: Optional[str] = None
        self.username: Optional[str] = None
        self.session: Optional[aiohttp.ClientSession] = None
        self.running = False
        self.gateway: Optional[GatewayHandler] = None
        self.commands = CommandSystem(self, config.get('prefix', '!'))
        self.rate_limiter = RateLimiter()
        self.stats = {
            'start_time': time.time(),
            'messages_processed': 0,
            'commands_executed': 0,
            'events_received': 0,
            'reconnections': 0
        }
        self.logger.info("Discord selfbot initialized with configuration")

    async def start(self):
        self.logger.info("Starting Discord selfbot...")
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        try:
            await self._get_user_info()
            self.gateway = GatewayHandler(self, self.config['token'])
            self.running = True
            while self.running:
                try:
                    await self.gateway.connect()
                except Exception as e:
                    self.logger.error(f"Gateway connection failed: {e}")
                    if self.running:
                        self.stats['reconnections'] += 1
                        self.logger.info("Attempting reconnection in 5 seconds...")
                        await asyncio.sleep(5)
                    else:
                        break
        finally:
            await self.cleanup()

    async def stop(self):
        self.logger.info("Stopping Discord selfbot...")
        self.running = False
        if self.gateway:
            await self.gateway.close()

    async def cleanup(self):
        if self.session and not self.session.closed:
            await self.session.close()
        self.logger.info("Selfbot cleanup completed")

    async def _get_user_info(self):
        try:
            async with self.session.get(
                'https://discord.com/api/v10/users/@me',
                headers={'Authorization': self.config["token"]}
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.user_id = data['id']
                    self.username = data['username']
                    self.logger.info(f"Authenticated as {self.username} ({self.user_id})")
                else:
                    raise Exception(f"Failed to authenticate user: {resp.status}")
        except Exception as e:
            self.logger.error(f"Failed to get user info: {e}")
            raise

    async def handle_event(self, event_type: str, data: Dict[str, Any]):
        self.stats['events_received'] += 1
        try:
            if event_type == 'MESSAGE_CREATE':
                await self._handle_message(data)
            elif event_type == 'GUILD_CREATE':
                await self._handle_guild_create(data)
            elif event_type == 'GUILD_UPDATE':
                await self._handle_guild_update(data)
            elif event_type == 'MESSAGE_REACTION_ADD':
                await self._handle_reaction_add(data)
            elif event_type == 'MESSAGE_REACTION_REMOVE':
                await self._handle_reaction_remove(data)
            else:
                self.logger.debug(f"Unhandled event: {event_type}")
        except Exception as e:
            self.logger.error(f"Error handling event {event_type}: {e}", exc_info=True)

    async def _handle_message(self, data: Dict[str, Any]):
        self.stats['messages_processed'] += 1
        author = data.get('author', {})
        guild_id = data.get('guild_id', 'DM')
        channel_id = data.get('channel_id')
        content = data.get('content', '')
        self.logger.info(
            f"Message received - Guild: {guild_id}, Channel: {channel_id}, "
            f"Author: {author.get('username', 'Unknown')} ({author.get('id')}), "
            f"Content: {content[:100]}{'...' if len(content) > 100 else ''}"
        )
        if content.startswith(self.commands.prefix):
            await self.commands.handle_command(data)

    async def send_message(self, channel_id: str, content: str, **kwargs) -> Optional[Dict[str, Any]]:
        await self.rate_limiter.wait_if_needed('message')
        payload = {'content': content, **{k: v for k, v in kwargs.items() if v is not None}}
        try:
            async with self.session.post(
                f'https://discord.com/api/v10/channels/{channel_id}/messages',
                headers={'Authorization': self.config["token"]},
                json=payload
            ) as resp:
                if resp.status in (200, 201):
                    result = await resp.json()
                    self.logger.info(f"Message sent to channel {channel_id}: {content[:50]}...")
                    return result
                else:
                    error_text = await resp.text()
                    self.logger.warning(f"Failed to send message ({resp.status}): {error_text}")
                    return None
        except Exception as e:
            self.logger.error(f"Error sending message: {e}")
            return None

    def get_stats(self) -> Dict[str, Any]:
        uptime = time.time() - self.stats['start_time']
        return {
            **self.stats,
            'uptime_seconds': uptime,
            'uptime_formatted': f"{int(uptime//3600)}h {int((uptime%3600)//60)}m {int(uptime%60)}s"
        }
