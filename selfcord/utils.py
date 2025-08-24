import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional
import re
import sys

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
except ImportError:
    class Fore:
        RED = ""
        GREEN = ""
        YELLOW = ""
        BLUE = ""
        RESET = ""

    class Style:
        BRIGHT = ""
        RESET_ALL = ""

def setup_logging():
    Path("logs").mkdir(exist_ok=True)
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.handlers.clear()

    class ColorFormatter(logging.Formatter):
        LEVEL_COLORS = {
            logging.DEBUG: Fore.BLUE,
            logging.INFO: Fore.GREEN,
            logging.WARNING: Fore.YELLOW,
            logging.ERROR: Fore.RED,
            logging.CRITICAL: Fore.RED + Style.BRIGHT
        }
        def format(self, record):
            color = self.LEVEL_COLORS.get(record.levelno, "")
            msg = super().format(record)
            return f"{color}{msg}{Fore.RESET}{Style.RESET_ALL}"

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_format = ColorFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    root_logger.addHandler(console_handler)

    file_handler = logging.FileHandler('logs/bot.log', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    file_handler.setFormatter(file_format)
    root_logger.addHandler(file_handler)

    logging.info("Logging initialized")

def load_config(config_path: str = 'config.json') -> Dict[str, Any]:
    default_config = {
        'token': '',
        'prefix': '!',
        'log_level': 'INFO',
        'max_message_length': 2000,
        'command_cooldown': 1.0,
        'rate_limits': {
            'message': {'requests': 5, 'window': 5},
            'command': {'requests': 10, 'window': 60}
        }
    }
    Path(config_path).parent.mkdir(parents=True, exist_ok=True)
    if not Path(config_path).exists():
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2)
        logging.warning(f"Default config created at {config_path}. Update your token.")
        return default_config
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            user_config = json.load(f)
        merged = {**default_config, **user_config}
        merged['rate_limits'] = {**default_config['rate_limits'], **user_config.get('rate_limits', {})}
        logging.info(f"Configuration loaded from {config_path}")
        return merged
    except Exception as e:
        logging.error(f"Failed to load config: {e}")
        return default_config

class RateLimiter:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.buckets: Dict[str, Dict[str, Any]] = {}
        self.logger = logging.getLogger("RateLimiter")
        self.config = config or {}
    
    async def wait_if_needed(self, bucket_name: str):
        limits = self.config.get('rate_limits', {}).get(bucket_name, {'requests': 5, 'window': 5})
        max_requests = limits.get('requests', 5)
        window = limits.get('window', 5)
        now = time.time()
        if bucket_name not in self.buckets:
            self.buckets[bucket_name] = {'requests': []}
        bucket = self.buckets[bucket_name]
        bucket['requests'] = [t for t in bucket['requests'] if now - t < window]
        if len(bucket['requests']) >= max_requests:
            wait_time = window - (now - min(bucket['requests']))
            self.logger.debug(f"Rate limit hit for '{bucket_name}', waiting {wait_time:.2f}s")
            await asyncio.sleep(wait_time)
        bucket['requests'].append(time.time())

def format_time(seconds: float) -> str:
    days, rem = divmod(int(seconds), 86400)
    hours, rem = divmod(rem, 3600)
    minutes, secs = divmod(rem, 60)
    result = []
    if days: result.append(f"{days}d")
    if hours: result.append(f"{hours}h")
    if minutes: result.append(f"{minutes}m")
    result.append(f"{secs}s")
    return " ".join(result)

def truncate_text(text: str, max_length: int = 100) -> str:
    return text if len(text) <= max_length else text[:max_length - 3] + "..."

def sanitize_filename(filename: str) -> str:
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    filename = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', filename)
    return filename[:255]

async def safe_send_message(bot, channel_id: str, content: str, max_length: int = 2000):
    if len(content) <= max_length:
        return await bot.send_message(channel_id, content)
    chunks = []
    while content:
        if len(content) <= max_length:
            chunks.append(content)
            break
        split_pos = content.rfind('\n', 0, max_length)
        if split_pos == -1:
            split_pos = content.rfind('. ', 0, max_length)
        if split_pos == -1:
            split_pos = max_length
        chunks.append(content[:split_pos + 1].strip())
        content = content[split_pos + 1:].lstrip()
    results = []
    for msg in chunks:
        results.append(await bot.send_message(channel_id, msg))
        await asyncio.sleep(0.5)
    return results
