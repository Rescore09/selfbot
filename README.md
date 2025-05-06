# SelfCord Library Documentation

SelfCord is a lightweight, asynchronous Python library for creating Discord bots and self-bots with a simple command framework. It uses WebSockets to connect to Discord's Gateway API and provides an intuitive interface for handling commands and events.

## Table of Contents

1. [Overview](#overview)
2. [Core Components](#core-components)
   - [SelfCord](#selfcord-class)
   - [Context](#context-class)
   - [Command](#command-class)
3. [Getting Started](#getting-started)
4. [Command Registration](#command-registration)
5. [Event Handling](#event-handling)
6. [Message Operations](#message-operations)
7. [Advanced Usage](#advanced-usage)
8. [Best Practices](#best-practices)
9. [Examples](#examples)

## Overview

SelfCord is designed to provide a simple yet powerful interface for interacting with Discord's API. The library:

- Uses async/await syntax for efficient I/O operations
- Provides decorator-based command registration
- Handles WebSocket communication with Discord's Gateway
- Manages heartbeats and reconnections automatically
- Offers context-based command handling

**Dependencies:**
- `asyncio`: For asynchronous programming
- `websockets`: For WebSocket connections to Discord's Gateway
- `aiohttp`: For REST API calls
- `json`: For payload parsing and formatting
- `logging`: For detailed logs

## Core Components

### SelfCord Class

The main bot class that handles connection to Discord and command dispatching.

#### Key Properties

| Property | Type | Description |
|----------|------|-------------|
| `token` | `str` | Discord authentication token |
| `prefix` | `str` | Command prefix (default: "!") |
| `ignore_self` | `bool` | Whether to ignore messages from the bot itself (default: `True`) |
| `autodelete` | `bool` | Whether to automatically delete bot messages (default: `False`) |
| `delete_after` | `int` | Time in seconds before messages are deleted if autodelete is True (default: `30`) |
| `commands` | `Dict[str, Command]` | Dictionary of registered commands |
| `session` | `aiohttp.ClientSession` | HTTP session for API requests |
| `ws` | `websockets.WebSocketClientProtocol` | WebSocket connection to Discord Gateway |
| `user` | `dict` | Information about the bot user once logged in |

#### Key Methods

| Method | Description |
|--------|-------------|
| `start(token)` | Initialize and connect the bot with the provided token |
| `cmd(name, description)` | Decorator to register a command |
| `send_message(channel_id, payload)` | Send a message to a specific channel |
| `edit_message(channel_id, message_id, payload)` | Edit an existing message |
| `delete_message(channel_id, message_id)` | Delete a message |

### Context Class

Represents the context in which a command was invoked, providing information about the message, channel, author, etc.

#### Key Properties

| Property | Type | Description |
|----------|------|-------------|
| `bot` | `SelfCord` | Reference to the bot instance |
| `message` | `dict` | Raw message data |
| `content` | `str` | Message content |
| `author` | `dict` | Message author information |
| `channel_id` | `str` | ID of the channel where message was sent |
| `guild_id` | `str` | ID of the guild (server) where message was sent |
| `message_id` | `str` | ID of the message |

#### Key Methods

| Method | Description |
|--------|-------------|
| `reply(content, embed)` | Reply to the message that triggered the command |
| `send(content, embed)` | Send a message to the same channel |

### Command Class

Simple container for command information.

#### Properties

| Property | Type | Description |
|----------|------|-------------|
| `name` | `str` | Command name |
| `callback` | `Callable` | Function to execute when command is invoked |
| `description` | `str` | Command description |

## Getting Started

### Installation

```bash
# Library itself would be installed via pip, but it's not published yet
# pip install selfcord

# Dependencies
pip install websockets aiohttp
```

### Basic Bot Setup

```python
import asyncio
from selfcord import bot

# Create a bot instance with "!" as the command prefix
# With auto-deletion of messages after 30 seconds
client = bot("!", autodelete=True, delete_after=30)

# Create a bot without auto-deletion
# client = bot("!")

# Register a command
@client.cmd("ping", description="Check if the bot is responsive")
async def ping(ctx):
    await ctx.reply("Pong!")
    
# Command with custom deletion time
@client.cmd("temp", description="Send a temporary message")
async def temp_message(ctx):
    # This message will be deleted after 10 seconds, regardless of bot settings
    await ctx.send("This message will disappear in 10 seconds", delete_after=10)

# Start the bot
if __name__ == "__main__":
    asyncio.run(client.start("YOUR_TOKEN_HERE"))
```

## Command Registration

Commands are registered using the `@bot.cmd()` decorator:

```python
@client.cmd("hello", description="Sends a greeting")
async def hello_command(ctx):
    await ctx.send(f"Hello, {ctx.author.get('username')}!")

@client.cmd("echo", description="Repeats your message")
async def echo_command(ctx):
    # Get content after the command name
    content = ctx.content.split(' ', 1)
    if len(content) > 1:
        await ctx.reply(content[1])
    else:
        await ctx.reply("You didn't provide anything to echo!")
```

## Event Handling

SelfCord primarily handles the `MESSAGE_CREATE` event for command processing. The event flow is:

1. Discord Gateway sends events over WebSocket
2. `_event_loop()` processes incoming event data
3. `_handle_dispatch()` routes events to appropriate handlers
4. `_handle_message()` checks for command prefixes and executes commands

## Message Operations

### Sending Messages

```python
# Direct send
await ctx.send("Hello, world!")

# Reply to the command message
await ctx.reply("This is a reply!")

# With an embed
embed = {
    "title": "Embed Title",
    "description": "This is an embed description",
    "color": 0x3498db
}
await ctx.send("Message with embed", embed=embed)
```

### Editing Messages

```python
@client.cmd("edit")
async def edit_example(ctx):
    # Send a message
    message = await ctx.send("Original message")
    
    # Wait 3 seconds
    await asyncio.sleep(3)
    
    # Edit the message
    await client.edit_message(
        ctx.channel_id, 
        message["id"], 
        {"content": "Edited message"}
    )
```

### Deleting Messages

```python
@client.cmd("delete")
async def delete_example(ctx):
    # Send a message
    message = await ctx.send("This message will self-destruct in 5 seconds")
    
    # Wait 5 seconds
    await asyncio.sleep(5)
    
    # Delete the message
    await client.delete_message(ctx.channel_id, message["id"])
```

## Advanced Usage

### Custom Configuration

```python
# Custom prefix
client = bot(prefix="$")  # Commands will be triggered with $command

# Auto-delete all bot messages after 15 seconds
client = bot(prefix="!", autodelete=True, delete_after=15)

# Combination of options
client = bot(prefix="?", ignore_self=False, autodelete=True, delete_after=60)
```

### Using Both Bot Tokens and User Tokens

SelfCord works with both bot tokens and user tokens:

```python
# For bot accounts
await client.start("Bot YOUR_BOT_TOKEN")

# For user accounts (self-bot)
await client.start("YOUR_USER_TOKEN")
```

**Warning:** Using self-bots (user tokens) violates Discord's Terms of Service and may result in account termination.

### Handling Command Errors

```python
@client.cmd("divide")
async def divide_command(ctx):
    try:
        args = ctx.content.split()[1:]
        if len(args) != 2:
            await ctx.reply("Please provide two numbers!")
            return
            
        result = float(args[0]) / float(args[1])
        await ctx.reply(f"Result: {result}")
    except ZeroDivisionError:
        await ctx.reply("Cannot divide by zero!")
    except ValueError:
        await ctx.reply("Please provide valid numbers!")
    except Exception as e:
        await ctx.reply(f"An error occurred: {str(e)}")
```

## Best Practices

1. **Error Handling**: Always wrap command callbacks in try-except blocks to prevent the bot from crashing
2. **Rate Limiting**: Be mindful of Discord's rate limits when sending multiple messages
3. **Token Security**: Never share your token or commit it to version control
4. **Logging**: Use the built-in logger for debugging and monitoring
5. **Respect Discord TOS**: Be aware that using user tokens violates Discord's Terms of Service

## Examples

### Help Command

```python
@client.cmd("help", description="Shows available commands")
async def help_command(ctx):
    commands_list = "\n".join([
        f"`{client.prefix}{name}`: {cmd.description}" 
        for name, cmd in client.commands.items()
    ])
    
    embed = {
        "title": "Available Commands",
        "description": commands_list,
        "color": 0x2ecc71
    }
    
    await ctx.send("Here are the available commands:", embed=embed)
```

### Status Command

```python
@client.cmd("status", description="Shows bot status")
async def status_command(ctx):
    uptime = time.time() - start_time  # assuming start_time was set when bot started
    
    embed = {
        "title": "Bot Status",
        "fields": [
            {"name": "Username", "value": client.user["username"], "inline": True},
            {"name": "Uptime", "value": f"{uptime:.2f} seconds", "inline": True},
            {"name": "Commands", "value": str(len(client.commands)), "inline": True}
        ],
        "color": 0x9b59b6
    }
    
    await ctx.send("Current bot status:", embed=embed)
```

### Purge Command

```python
@client.cmd("purge", description="Delete multiple messages")
async def purge_command(ctx):
    try:
        args = ctx.content.split()
        if len(args) != 2 or not args[1].isdigit():
            await ctx.reply("Usage: !purge [number of messages]")
            return
            
        count = int(args[1])
        if count < 1 or count > 100:
            await ctx.reply("Please provide a number between 1 and 100")
            return
            
        # This would require additional API calls to fetch message history
        # and then delete each message - simplified example
        await ctx.reply(f"Would delete {count} messages (not implemented)")
    except Exception as e:
        await ctx.reply(f"An error occurred: {str(e)}")
```

---

## Quick Start

```python
import asyncio
from selfcord import bot

client = bot("!")

@client.cmd("ping", description="Check if the bot is responsive")
async def ping(ctx):
    await ctx.reply("Pong!")

if __name__ == "__main__":
    asyncio.run(client.start("YOUR_TOKEN_HERE"))
```

## Features

- Simple, decorator-based command system
- Automatic message deletion (optional)
- Built-in logging
- Asynchronous WebSocket and HTTP handling
- Works with both bot tokens and user tokens

## Documentation

For full documentation, visit [GitHub repository](https://github.com/rescore09/selfcord).

## Disclaimer

Using self-bots (user tokens) violates Discord's Terms of Service and may result in account termination.

## Inspiration 
I took great inspiration from [discord.py](https://github.com/Rapptz/discord.py) while creating this, and credit is due where it's due.

## Enjoy!
Enjoy using this library!

```

