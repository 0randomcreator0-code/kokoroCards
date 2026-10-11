# Discord Bot Setup

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file (copy from `.env.example`):
```bash
cp .env.example .env
```

3. Add your Discord bot token to `.env`:
```
DISCORD_TOKEN=your_actual_bot_token_here
```

## Running the Bot

```bash
python bot.py
```

## Commands

### Slash Commands (use `/`)
- `/ping` - Check if the bot is alive
- `/hello @user` - Greet a user
- `/userinfo [@user]` - Get information about a user
- `/roll [sides]` - Roll a dice (default: 6 sides)
- `/choose options` - Choose randomly from comma-separated options
- `/serverinfo` - Get information about the server
- `/avatar [@user]` - Get a user's avatar
- `/echo message` - Echo a message
- `/help` - Show all available commands

### Prefix Commands (use `!`)

**Note:** Moderation commands require **Administrator** permissions.

#### Moderation
- `!kick @user [reason]` - Kick a user from the server
- `!ban @user [reason]` - Ban a user from the server
- `!unban user#tag` - Unban a user (e.g., `!unban username#1234`)
- `!mute @user [duration]` - Mute a user (e.g., `!mute @user 10m`, `!mute @user 1h`, `!mute @user 1d`)
- `!unmute @user` - Unmute a user
- `!warn @user [reason]` - Warn a user
- `!warnings [@user]` - View warnings (leave blank to view your own)
- `!clear [amount]` - Delete messages (1-100, default: 5)

## Command Examples

### Slash Commands
```
/ping
→ Pong!

/userinfo @JohnDoe
→ Shows user details

/roll 20
→ 🎲 Rolled a d20: **17**

/choose Coffee, Tea, Juice
→ 🎯 I choose: **Tea**
```

### Prefix Commands (Moderation)
```
!kick @user Being rude
→ Kicks the user and logs reason

!mute @user 1h
→ Mutes user for 1 hour (supports m/h/d)

!warn @user Spamming
→ Warns user and increments warning count

!warnings @user
→ Shows all warnings for that user

!clear 10
→ Deletes last 10 messages (max 100)

!ban @user Harassment
→ Bans user permanently from server

!unban username#1234
→ Unbans user by their tag
```

## Security

⚠️ **Never commit your `.env` file or token to the repository.**

The `.env` file is listed in `.gitignore` to prevent accidental commits.

## Prefix

The bot uses `!` as the default prefix for text commands. You can change this in `bot.py` by modifying the `PREFIX` variable:

```python
PREFIX = "!"  # Change to your desired prefix
```

## Notes

- Moderation commands require the user to have **Administrator** permissions
- Warnings and mutes are stored in memory and will reset when the bot restarts
- To make them persistent, consider adding a database (SQLite, PostgreSQL, etc.)
