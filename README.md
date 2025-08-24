# Discord Selfbot Wrapper

A discord wrapper made specifically for selfbots.

> This project was purely made for fun, This can and likely will get you banned.

> This project was made at 6AM so ignore any shit code or mistakes and just post them on issues.

> This project wasn't made with easy usage in mind, If you are a skid I'm just warning you, it wont be easy.
---

## Features

* **User Token Support** – Works directly with a user token for full access.
* **Command System** – Easily add commands with aliases and track usage.
* **Rate Limiter** – Prevents accidental API spamming. Configurable per bucket.
* **Event Handling** – Covers messages, reactions, and guild updates.
* **Gateway Management** – Reconnects automatically, keeps heartbeat, resumes sessions.
* **Logging** – Console logs in color, plus detailed file logs.

---

## Example: Usage

Below here is an example of how to use the selfcord library:

```python
import asyncio
import json
from selfcord.bot import DiscordUser

async def main():
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    bot = DiscordUser(config)
    
    async def custom_command_handler(message_data, args):
        channel_id = message_data.get('channel_id')
        user = message_data.get('author', {}).get('username', 'Unknown')
        response = f"Hello {user}! You said: {' '.join(args)}"
        await bot.send_message(channel_id, response)
    
    bot.commands.register_command(
        'hello', 
        custom_command_handler, 
        'Say hello with custom message',
        ['hi', 'greet']
    )
    
    try:
        await bot.start()
    except KeyboardInterrupt:
        await bot.stop()
        print("Bot stopped by user")
    except Exception as e:
        print(f"Error running bot: {e}")

if __name__ == "__main__":
    asyncio.run(main())
```


---

## Setup

1. Clone the repo:

```bash
git clone https://github.com/rescore09/selfcord.git
cd discord-selfbot
```

2. Run the setup script:

```bat
setup.bat
```

3. Input your token into the `config.json`.

```json
{
  "token": "YOUR_TOKEN_HERE",
  "prefix": "!",
  "log_level": "INFO",
  "max_message_length": 2000,
  "command_cooldown": 1.0,
  "rate_limits": {
    "message": {
      "requests": 5,
      "window": 5
    },
    "command": {
      "requests": 10,
      "window": 60
    }
  },
  "features": {
    "auto_reconnect": true,
    "log_all_messages": true,
    "log_reactions": false,
    "command_logging": true
  },
  "intents": {
    "guilds": true,
    "guild_messages": true,
    "guild_reactions": false,
    "direct_messages": true
  }
}
```

4. Start the bot:

```bat
start.bat
```

---

## Project Layout

```
selfcord/
├── bot.py
├── gateway.py
├── commands.py
├── utils.py
└── logs/
```

---

## Configuration

* `token` – Your Discord user token
* `prefix` – Command prefix (default: `!`)
* `log_level` – DEBUG / INFO / WARNING / ERROR
* `max_message_length` – Max message length for splitting
* `command_cooldown` – Minimum delay between commands
* `rate_limits` – Configure limits per bucket

---

## Logging

* File logs in `logs/bot.log`
* Includes timestamp, function, line, log level, and message

---

## Advanced Tips

* Add commands on the fly:

```python
bot.commands.register_command('shout', shout_handler, "Shout a message")
```

* Send long messages safely:

```python
await safe_send_message(bot, channel_id, long_text)
```

* Access stats:

```python
stats = bot.get_stats()
print(stats)
```

---

## Disclaimer

This bot is strictly for learning. Running it on real accounts may get you banned. Use responsibly.

---

## Requirements

* Python 3.10+
* `aiohttp`
* `colorama`

---

## License

MIT License. Free to use and modify for learning or personal projects.

---
