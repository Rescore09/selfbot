import asyncio
import json
import logging
import time
from typing import Dict, Any, Optional
import aiohttp

class GatewayHandler:
    def __init__(self, bot, token: str):
        self.bot = bot
        self.token = token
        self.logger = logging.getLogger(__name__)
        self.ws: Optional[aiohttp.ClientWebSocketResponse] = None
        self.session_id: Optional[str] = None
        self.sequence: Optional[int] = None
        self.heartbeat_interval: Optional[float] = None
        self.last_heartbeat_ack = True
        self.gateway_url = "wss://gateway.discord.gg/?v=10&encoding=json"
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5

    async def connect(self):
        self.logger.info("Connecting to Discord gateway...")
        try:
            await self._get_gateway_url()
            async with self.bot.session.ws_connect(self.gateway_url) as ws:
                self.ws = ws
                self.reconnect_attempts = 0
                self.logger.info("Gateway connection established")
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        await self._handle_message(json.loads(msg.data))
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        self.logger.error(f"Gateway error: {ws.exception()}")
                        break
                    elif msg.type == aiohttp.WSMsgType.CLOSE:
                        self.logger.warning("Gateway connection closed")
                        break
        except Exception as e:
            self.reconnect_attempts += 1
            self.logger.error(f"Gateway connection error (attempt {self.reconnect_attempts}): {e}")
            if self.reconnect_attempts < self.max_reconnect_attempts:
                delay = min(300, (2 ** self.reconnect_attempts) + (time.time() % 1))
                self.logger.info(f"Reconnecting in {delay:.1f} seconds...")
                await asyncio.sleep(delay)
                raise
            else:
                self.logger.error("Max reconnection attempts reached")
                raise

    async def close(self):
        if self.ws and not self.ws.closed:
            await self.ws.close()
        self.logger.info("Gateway connection closed")

    async def _get_gateway_url(self):
        try:
            async with self.bot.session.get(
                'https://discord.com/api/v10/gateway',
                headers={'Authorization': self.token}
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    url = data['url']
                    self.gateway_url = f"{url}/?v=10&encoding=json"
                    self.logger.debug(f"Gateway URL updated: {self.gateway_url}")
                else:
                    self.logger.warning(f"Failed to get gateway URL: {resp.status}")
        except Exception as e:
            self.logger.error(f"Error getting gateway URL: {e}")

    async def _handle_message(self, data: Dict[str, Any]):
        op = data.get('op')
        d = data.get('d')
        s = data.get('s')
        t = data.get('t')
        if s is not None:
            self.sequence = s
        if op == 0:
            self.logger.debug(f"Received event: {t}")
            await self.bot.handle_event(t, d)
        elif op == 1:
            await self._send_heartbeat()
        elif op == 7:
            self.logger.warning("Gateway requested reconnect")
            await self.close()
        elif op == 9:
            self.logger.warning("Invalid session, re-identifying...")
            self.session_id = None
            self.sequence = None
            await asyncio.sleep(5)
            await self._identify()
        elif op == 10:
            self.heartbeat_interval = d['heartbeat_interval'] / 1000.0
            self.logger.info(f"Gateway hello received, heartbeat interval: {self.heartbeat_interval}s")
            asyncio.create_task(self._heartbeat_loop())
            if self.session_id:
                await self._resume()
            else:
                await self._identify()
        elif op == 11:
            self.last_heartbeat_ack = True
            self.logger.debug("Heartbeat acknowledged")

    async def _identify(self):
        payload = {
            'op': 2,
            'd': {
                'token': self.token,
                'properties': {
                    'os': 'windows',
                    'browser': 'Chrome',
                    'device': '',
                    'system_locale': 'en-US',
                    'browser_user_agent': 'Mozilla/5.0',
                    'browser_version': '112.0',
                }
            }
        }
        await self._send_payload(payload)
        self.logger.info("Identification sent to gateway (user token)")

    async def _resume(self):
        payload = {
            'op': 6,
            'd': {
                'token': self.token,
                'session_id': self.session_id,
                'seq': self.sequence
            }
        }
        await self._send_payload(payload)
        self.logger.info("Session resume sent to gateway")

    async def _heartbeat_loop(self):
        while self.ws and not self.ws.closed:
            if not self.last_heartbeat_ack:
                self.logger.warning("Heartbeat not acknowledged, connection may be dead")
                break
            await self._send_heartbeat()
            await asyncio.sleep(self.heartbeat_interval)

    async def _send_heartbeat(self):
        payload = {
            'op': 1,
            'd': self.sequence
        }
        self.last_heartbeat_ack = False
        await self._send_payload(payload)
        self.logger.debug("Heartbeat sent")

    async def _send_payload(self, payload: Dict[str, Any]):
        if self.ws and not self.ws.closed:
            await self.ws.send_str(json.dumps(payload))
