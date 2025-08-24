import asyncio
import logging
import time
from typing import Dict, List, Callable, Any, Optional

class Command:
    def __init__(self, name: str, handler: Callable, description: str = "", aliases: List[str] = None):
        self.name = name
        self.handler = handler
        self.description = description
        self.aliases = aliases or []
        self.usage_count = 0
        self.last_used = None

class CommandSystem:
    def __init__(self, bot, prefix: str = '!'):
        self.bot = bot
        self.prefix = prefix
        self.commands: Dict[str, Command] = {}
        self.logger = logging.getLogger(__name__)
        self._register_default_commands()
        self.logger.info(f"Command system initialized with prefix: {prefix}")

    def register_command(self, name: str, handler: Callable, description: str = "", aliases: List[str] = None):
        command = Command(name, handler, description, aliases)
        self.commands[name] = command
        for alias in aliases or []:
            self.commands[alias] = command
        self.logger.info(f"Command registered: {name} (aliases: {aliases or []})")

    def _register_default_commands(self):
        self.register_command('ping', self._ping_command, 'Test bot responsiveness')
        self.register_command('help', self._help_command, 'Show available commands')
        self.register_command('stats', self._stats_command, 'Show bot statistics')
        self.register_command('uptime', self._uptime_command, 'Show bot uptime')

    async def handle_command(self, message_data: Dict[str, Any]):
        content = message_data.get('content', '')
        author = message_data.get('author', {})
        channel_id = message_data.get('channel_id')
        guild_id = message_data.get('guild_id', 'DM')
        if not content.startswith(self.prefix):
            return
        command_text = content[len(self.prefix):].strip()
        if not command_text:
            return
        parts = command_text.split()
        command_name = parts[0].lower()
        args = parts[1:]
        command = self.commands.get(command_name)
        if not command:
            self.logger.debug(f"Unknown command: {command_name}")
            return
        self.logger.info(
            f"Command executed - User: {author.get('username')} ({author.get('id')}), "
            f"Guild: {guild_id}, Channel: {channel_id}, Command: {command_name}, Args: {args}"
        )
        command.usage_count += 1
        command.last_used = time.time()
        self.bot.stats['commands_executed'] += 1
        try:
            await command.handler(message_data, args)
        except Exception as e:
            self.logger.error(f"Error executing command {command_name}: {e}", exc_info=True)
            await self.bot.send_message(
                channel_id,
                f"❌ An error occurred while executing the command: `{e}`"
            )

    async def _ping_command(self, message_data: Dict[str, Any], args: List[str]):
        channel_id = message_data.get('channel_id')
        start_time = time.time()
        await self.bot.send_message(channel_id, "🏓 Pong!")
        response_time = (time.time() - start_time) * 1000
        await self.bot.send_message(channel_id, f"🏓 Pong! Response time: `{response_time:.2f}ms`")

    async def _help_command(self, message_data: Dict[str, Any], args: List[str]):
        channel_id = message_data.get('channel_id')
        if args and args[0] in self.commands:
            command = self.commands[args[0]]
            help_text = f"**{self.prefix}{command.name}** - {command.description}\n"
            if command.aliases:
                help_text += f"*Aliases: {', '.join(command.aliases)}*\n"
            help_text += f"*Used {command.usage_count} times*"
        else:
            unique_commands = {}
            for name, command in self.commands.items():
                if name == command.name:
                    unique_commands[name] = command
            help_text = f"**Available Commands** (prefix: `{self.prefix}`)\n\n"
            for name, command in sorted(unique_commands.items()):
                help_text += f"`{self.prefix}{name}` - {command.description}\n"
            help_text += f"\nType `{self.prefix}help <command>` for detailed help."
        await self.bot.send_message(channel_id, help_text)

    async def _stats_command(self, message_data: Dict[str, Any], args: List[str]):
        channel_id = message_data.get('channel_id')
        stats = self.bot.get_stats()
        stats_text = "📊 **Bot Statistics**\n\n"
        stats_text += f"**Uptime:** {stats['uptime_formatted']}\n"
        stats_text += f"**Messages Processed:** {stats['messages_processed']:,}\n"
        stats_text += f"**Commands Executed:** {stats['commands_executed']:,}\n"
        stats_text += f"**Events Received:** {stats['events_received']:,}\n"
        stats_text += f"**Reconnections:** {stats['reconnections']}\n"
        await self.bot.send_message(channel_id, stats_text)

    async def _uptime_command(self, message_data: Dict[str, Any], args: List[str]):
        channel_id = message_data.get('channel_id')
        stats = self.bot.get_stats()
        uptime_text = f"⏱️ **Bot Uptime:** {stats['uptime_formatted']}"
        await self.bot.send_message(channel_id, uptime_text)

    def get_command_stats(self) -> Dict[str, Any]:
        unique_commands = {}
        for name, command in self.commands.items():
            if name == command.name:
                unique_commands[name] = {
                    'usage_count': command.usage_count,
                    'last_used': command.last_used,
                    'description': command.description
                }
        return unique_commands
