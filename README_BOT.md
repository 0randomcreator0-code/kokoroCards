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

- `/ping` - Check if the bot is alive
- `/hello @user` - Greet a user

## Security

⚠️ **Never commit your `.env` file or token to the repository.**

The `.env` file is listed in `.gitignore` to prevent accidental commits.
