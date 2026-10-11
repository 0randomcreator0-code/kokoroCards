import os
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
from datetime import datetime, timedelta
import random

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
PREFIX = "k!"  # Custom prefix for prefix commands

if not TOKEN:
    raise ValueError("DISCORD_TOKEN is not set. Add it to your .env file.")

CARD_CATEGORIES = {
    "anime": [
        "Attack on Titan",
        "Demon Slayer",
        "Jujutsu Kaisen",
        "One Piece",
        "My Hero Academia",
        "Naruto",
        "Fullmetal Alchemist",
        "Spy x Family",
        "Black Clover",
        "Hunter x Hunter",
    ],
    "cartoon": [
        "Adventure Time",
        "Avatar: The Last Airbender",
        "Gravity Falls",
        "Teen Titans",
        "The Owl House",
        "Steven Universe",
        "Samurai Jack",
        "Regular Show",
        "Rick and Morty",
        "Bluey",
    ],
    "kpop": [
        "BTS",
        "Blackpink",
        "Stray Kids",
        "Seventeen",
        "TXT",
        "Enhypen",
        "aespa",
        "TWICE",
        "IVE",
        "NCT",
    ],
    "kdrama": [
        "Crash Landing on You",
        "Goblin",
        "Our Beloved Summer",
        "Reply 1988",
        "Descendants of the Sun",
        "Kingdom",
        "True Beauty",
        "The King: Eternal Monarch",
        "Hospital Playlist",
        "Itaewon Class",
    ],
    "cdrama": [
        "The Untamed",
        "Love Between Fairy and Devil",
        "The Good Night Show",
        "The King's Avatar",
        "A Love So Beautiful",
        "Meteor Garden",
        "Love O2O",
        "The Legend of Zhen Huan",
        "The Princess of the Ming Dynasty",
        "To Our Warmest Heart",
    ],
    "jdrama": [
        "Nagi no Ojo",
        "The Good Doctor",
        "Your Name",
        "Riyu no Kizuna",
        "Death Note",
        "One Punch Man",
        "The Last Samurai",
        "Midnight Diner",
        "The Queen's Gambit",
        "My Love Mix-Up!",
    ],
    "manhwa": [
        "Solo Leveling",
        "The God of High School",
        "Tower of God",
        "The Beginning After the End",
        "Lookism",
        "Sweet Home",
        "The Breaker",
        "The Boxer",
        "Noblesse",
        "The Legend of the Northern Blade",
    ],
}


def normalize_category(value: str):
    cleaned = value.strip().lower().replace("-", " ").replace("_", " ")
    aliases = {
        "kpop": "kpop",
        "k pop": "kpop",
        "anime": "anime",
        "cartoon": "cartoon",
        "kid": "anime",
        "manhwa": "manhwa",
        "kdrama": "kdrama",
        "k drama": "kdrama",
        "cdrama": "cdrama",
        "c drama": "cdrama",
        "jdrama": "jdrama",
        "j drama": "jdrama",
    }
    return aliases.get(cleaned, cleaned)


class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix=PREFIX, intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()


bot = MyBot()


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print(f"Prefix: {PREFIX}")


# ==================== CARD COMMANDS ====================

@bot.command(name="card", aliases=["c", "C"], help="Recommend a card from a category or choose a random one.")
async def card(ctx, category: str = "random"):
    if category.lower() == "random" or category.lower() == "r":
        selected_category = random.choice(list(CARD_CATEGORIES.keys()))
    else:
        selected_category = normalize_category(category)
        if selected_category not in CARD_CATEGORIES:
            valid = ", ".join(sorted(CARD_CATEGORIES.keys()))
            await ctx.send(f"Invalid category. Choose one of: {valid}")
            return

    card_name = random.choice(CARD_CATEGORIES[selected_category])

    embed = discord.Embed(
        title=f"🎴 {selected_category.upper()} Card",
        description=f"Recommended pick: **{card_name}**",
        color=discord.Color.magenta(),
        timestamp=datetime.now(),
    )
    embed.add_field(name="Category", value=selected_category.title(), inline=True)
    embed.add_field(name="Mood", value="Great for a themed collection", inline=True)
    await ctx.send(embed=embed)


@bot.command(name="anime", help="Get a random anime card suggestion")
async def anime_card(ctx):
    await card(ctx, "anime")


@bot.command(name="cartoon", help="Get a random cartoon card suggestion")
async def cartoon_card(ctx):
    await card(ctx, "cartoon")


@bot.command(name="kpop", help="Get a random K-pop card suggestion")
async def kpop_card(ctx):
    await card(ctx, "kpop")


@bot.command(name="kdrama", help="Get a random K-drama card suggestion")
async def kdrama_card(ctx):
    await card(ctx, "kdrama")


@bot.command(name="cdrama", help="Get a random C-drama card suggestion")
async def cdrama_card(ctx):
    await card(ctx, "cdrama")


@bot.command(name="jdrama", help="Get a random J-drama card suggestion")
async def jdrama_card(ctx):
    await card(ctx, "jdrama")


@bot.command(name="manhwa", help="Get a random manhwa card suggestion")
async def manhwa_card(ctx):
    await card(ctx, "manhwa")


# ==================== SLASH COMMANDS ====================

@bot.tree.command(name="ping", description="Check if the bot is alive")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong!")


@bot.tree.command(name="hello", description="Say hello to someone")
@app_commands.describe(user="Who to greet")
async def hello(interaction: discord.Interaction, user: discord.Member):
    await interaction.response.send_message(f"Hello {user.mention}!")


@bot.tree.command(name="userinfo", description="Get information about a user")
@app_commands.describe(user="The user to get info about")
async def userinfo(interaction: discord.Interaction, user: discord.Member = None):
    target_user = user or interaction.user

    embed = discord.Embed(
        title=f"User Info - {target_user.name}",
        color=discord.Color.blue(),
        timestamp=datetime.now(),
    )
    embed.set_thumbnail(url=target_user.avatar.url if target_user.avatar else None)
    embed.add_field(name="Username", value=target_user.name, inline=True)
    embed.add_field(name="ID", value=target_user.id, inline=True)
    embed.add_field(name="Account Created", value=target_user.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=False)
    embed.add_field(name="Joined Server", value=target_user.joined_at.strftime("%Y-%m-%d %H:%M:%S") if target_user.joined_at else "Unknown", inline=False)
    embed.add_field(name="Bot?", value="Yes" if target_user.bot else "No", inline=True)

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="roll", description="Roll a dice")
@app_commands.describe(sides="Number of sides on the dice (default: 6)")
async def roll(interaction: discord.Interaction, sides: int = 6):
    if sides < 2:
        await interaction.response.send_message("The dice must have at least 2 sides!")
        return

    result = random.randint(1, sides)
    await interaction.response.send_message(f"🎲 Rolled a d{sides}: **{result}**")


@bot.tree.command(name="choose", description="Let the bot choose between options")
@app_commands.describe(options="Separate choices with commas (e.g., Pizza, Burger, Tacos)")
async def choose(interaction: discord.Interaction, options: str):
    choices = [choice.strip() for choice in options.split(",")]

    if len(choices) < 2:
        await interaction.response.send_message("Please provide at least 2 choices separated by commas!")
        return

    selected = random.choice(choices)
    await interaction.response.send_message(f"🎯 I choose: **{selected}**")


@bot.tree.command(name="serverinfo", description="Get information about the server")
async def serverinfo(interaction: discord.Interaction):
    guild = interaction.guild

    embed = discord.Embed(
        title=f"Server Info - {guild.name}",
        color=discord.Color.green(),
        timestamp=datetime.now(),
    )
    embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
    embed.add_field(name="Server ID", value=guild.id, inline=True)
    embed.add_field(name="Owner", value=guild.owner.mention if guild.owner else "Unknown", inline=True)
    embed.add_field(name="Members", value=guild.member_count, inline=True)
    embed.add_field(name="Created", value=guild.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=False)
    embed.add_field(name="Text Channels", value=len(guild.text_channels), inline=True)
    embed.add_field(name="Voice Channels", value=len(guild.voice_channels), inline=True)

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="avatar", description="Get a user's avatar")
@app_commands.describe(user="The user to get the avatar of")
async def avatar(interaction: discord.Interaction, user: discord.Member = None):
    target_user = user or interaction.user

    if target_user.avatar:
        embed = discord.Embed(
            title=f"{target_user.name}'s Avatar",
            color=discord.Color.purple(),
            timestamp=datetime.now(),
        )
        embed.set_image(url=target_user.avatar.url)
        embed.description = f"[Download]({target_user.avatar.url})"
        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message(f"{target_user.mention} is using the default avatar!")


@bot.tree.command(name="echo", description="Repeat what you say")
@app_commands.describe(message="What to echo")
async def echo(interaction: discord.Interaction, message: str):
    await interaction.response.send_message(f"```{message}```")


@bot.tree.command(name="help", description="Get help with available commands")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Bot Commands",
        description="Here are all available commands:\n\n**Slash Commands** start with `/`\n**Prefix Commands** start with `k!`",
        color=discord.Color.gold(),
        timestamp=datetime.now(),
    )

    embed.add_field(name="📌 Slash Commands", value="", inline=False)
    slash_commands = [
        ("/ping", "Check if the bot is alive"),
        ("/hello @user", "Greet a user"),
        ("/userinfo [@user]", "Get information about a user"),
        ("/roll [sides]", "Roll a dice (default: 6 sides)"),
        ("/choose options", "Choose randomly from comma-separated options"),
        ("/serverinfo", "Get information about the server"),
        ("/avatar [@user]", "Get a user's avatar"),
        ("/echo message", "Echo a message"),
    ]

    for cmd, desc in slash_commands:
        embed.add_field(name=cmd, value=desc, inline=False)

    embed.add_field(name="🎴 Card Commands (Prefix: k!)", value="", inline=False)
    card_commands = [
        ("k!card", "Get a random card recommendation"),
        ("k!card anime", "Get an anime card pick"),
        ("k!card cartoon", "Get a cartoon card pick"),
        ("k!card kpop", "Get a K-pop card pick"),
        ("k!card kdrama", "Get a K-drama card pick"),
        ("k!card cdrama", "Get a C-drama card pick"),
        ("k!card jdrama", "Get a J-drama card pick"),
        ("k!card manhwa", "Get a manhwa card pick"),
        ("k!c", "Alias for k!card"),
    ]

    for cmd, desc in card_commands:
        embed.add_field(name=cmd, value=desc, inline=False)

    embed.add_field(name="🛡️ Moderation Commands (Prefix: k!)", value="", inline=False)
    mod_commands = [
        ("k!kick @user [reason]", "Kick a user from the server"),
        ("k!ban @user [reason]", "Ban a user from the server"),
        ("k!unban user#tag", "Unban a user by tag (e.g., username#1234)"),
        ("k!mute @user [duration]", "Mute a user for a duration (e.g., 10m, 1h, 1d)"),
        ("k!unmute @user", "Unmute a user"),
        ("k!warn @user [reason]", "Warn a user"),
        ("k!warnings [@user]", "View warnings for a user or yourself"),
        ("k!clear [amount]", "Delete messages (max 100, default 5)"),
    ]

    for cmd, desc in mod_commands:
        embed.add_field(name=cmd, value=desc, inline=False)

    await interaction.response.send_message(embed=embed)


# ==================== MODERATION COMMANDS ====================

user_warnings = {}
muted_users = {}


def check_permissions(ctx):
    return ctx.author.guild_permissions.administrator


@bot.command(name="kick", description="Kick a user from the server")
async def kick(ctx, user: discord.Member, *, reason="No reason provided"):
    if not check_permissions(ctx):
        embed = discord.Embed(
            title="❌ Permission Denied",
            description="You need Administrator permissions to use this command.",
            color=discord.Color.red(),
        )
        await ctx.send(embed=embed)
        return

    if user == ctx.author:
        embed = discord.Embed(title="❌ Error", description="You cannot kick yourself!", color=discord.Color.red())
        await ctx.send(embed=embed)
        return

    if user == ctx.guild.owner:
        embed = discord.Embed(title="❌ Error", description="You cannot kick the server owner!", color=discord.Color.red())
        await ctx.send(embed=embed)
        return

    try:
        await user.kick(reason=reason)
        embed = discord.Embed(
            title="✅ User Kicked",
            description=f"{user.mention} has been kicked from the server.",
            color=discord.Color.green(),
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Kicked by", value=ctx.author.mention, inline=False)
        await ctx.send(embed=embed)
    except discord.Forbidden:
        embed = discord.Embed(title="❌ Error", description="I don't have permission to kick this user.", color=discord.Color.red())
        await ctx.send(embed=embed)


@bot.command(name="ban", description="Ban a user from the server")
async def ban(ctx, user: discord.Member, *, reason="No reason provided"):
    if not check_permissions(ctx):
        embed = discord.Embed(
            title="❌ Permission Denied",
            description="You need Administrator permissions to use this command.",
            color=discord.Color.red(),
        )
        await ctx.send(embed=embed)
        return

    if user == ctx.author:
        embed = discord.Embed(title="❌ Error", description="You cannot ban yourself!", color=discord.Color.red())
        await ctx.send(embed=embed)
        return

    if user == ctx.guild.owner:
        embed = discord.Embed(title="❌ Error", description="You cannot ban the server owner!", color=discord.Color.red())
        await ctx.send(embed=embed)
        return

    try:
        await user.ban(reason=reason)
        embed = discord.Embed(
            title="✅ User Banned",
            description=f"{user.mention} has been banned from the server.",
            color=discord.Color.green(),
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Banned by", value=ctx.author.mention, inline=False)
        await ctx.send(embed=embed)
    except discord.Forbidden:
        embed = discord.Embed(title="❌ Error", description="I don't have permission to ban this user.", color=discord.Color.red())
        await ctx.send(embed=embed)


@bot.command(name="unban", description="Unban a user from the server")
async def unban(ctx, user_tag: str):
    if not check_permissions(ctx):
        embed = discord.Embed(
            title="❌ Permission Denied",
            description="You need Administrator permissions to use this command.",
            color=discord.Color.red(),
        )
        await ctx.send(embed=embed)
        return

    try:
        bans = [entry async for entry in ctx.guild.bans()]
        user_to_unban = None

        for ban in bans:
            if str(ban.user) == user_tag or ban.user.name == user_tag.split("#")[0]:
                user_to_unban = ban.user
                break

        if not user_to_unban:
            embed = discord.Embed(title="❌ Error", description=f"Could not find a banned user with tag: {user_tag}", color=discord.Color.red())
            await ctx.send(embed=embed)
            return

        await ctx.guild.unban(user_to_unban)
        embed = discord.Embed(title="✅ User Unbanned", description=f"**{user_to_unban}** has been unbanned.", color=discord.Color.green())
        embed.add_field(name="Unbanned by", value=ctx.author.mention, inline=False)
        await ctx.send(embed=embed)
    except discord.Forbidden:
        embed = discord.Embed(title="❌ Error", description="I don't have permission to unban users.", color=discord.Color.red())
        await ctx.send(embed=embed)


@bot.command(name="mute", description="Mute a user")
async def mute(ctx, user: discord.Member, duration: str = "10m"):
    if not check_permissions(ctx):
        embed = discord.Embed(
            title="❌ Permission Denied",
            description="You need Administrator permissions to use this command.",
            color=discord.Color.red(),
        )
        await ctx.send(embed=embed)
        return

    if user == ctx.author:
        embed = discord.Embed(title="❌ Error", description="You cannot mute yourself!", color=discord.Color.red())
        await ctx.send(embed=embed)
        return

    try:
        if duration.endswith("m"):
            minutes = int(duration[:-1])
            mute_time = datetime.now() + timedelta(minutes=minutes)
        elif duration.endswith("h"):
            hours = int(duration[:-1])
            mute_time = datetime.now() + timedelta(hours=hours)
        elif duration.endswith("d"):
            days = int(duration[:-1])
            mute_time = datetime.now() + timedelta(days=days)
        else:
            raise ValueError()
    except Exception:
        embed = discord.Embed(title="❌ Invalid Duration", description="Use format: 10m, 1h, or 1d", color=discord.Color.red())
        await ctx.send(embed=embed)
        return

    muted_users[user.id] = mute_time
    embed = discord.Embed(title="🔇 User Muted", description=f"{user.mention} has been muted.", color=discord.Color.orange())
    embed.add_field(name="Duration", value=duration, inline=False)
    embed.add_field(name="Muted by", value=ctx.author.mention, inline=False)
    await ctx.send(embed=embed)


@bot.command(name="unmute", description="Unmute a user")
async def unmute(ctx, user: discord.Member):
    if not check_permissions(ctx):
        embed = discord.Embed(
            title="❌ Permission Denied",
            description="You need Administrator permissions to use this command.",
            color=discord.Color.red(),
        )
        await ctx.send(embed=embed)
        return

    if user.id in muted_users:
        del muted_users[user.id]
        embed = discord.Embed(title="🔊 User Unmuted", description=f"{user.mention} has been unmuted.", color=discord.Color.green())
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(title="❌ Error", description=f"{user.mention} is not muted.", color=discord.Color.red())
        await ctx.send(embed=embed)


@bot.command(name="warn", description="Warn a user")
async def warn(ctx, user: discord.Member, *, reason="No reason provided"):
    if not check_permissions(ctx):
        embed = discord.Embed(
            title="❌ Permission Denied",
            description="You need Administrator permissions to use this command.",
            color=discord.Color.red(),
        )
        await ctx.send(embed=embed)
        return

    if user == ctx.author:
        embed = discord.Embed(title="❌ Error", description="You cannot warn yourself!", color=discord.Color.red())
        await ctx.send(embed=embed)
        return

    if user.id not in user_warnings:
        user_warnings[user.id] = []

    user_warnings[user.id].append({
        "reason": reason,
        "warned_by": ctx.author.name,
        "date": datetime.now(),
    })

    embed = discord.Embed(title="⚠️ User Warned", description=f"{user.mention} has been warned.", color=discord.Color.orange())
    embed.add_field(name="Reason", value=reason, inline=False)
    embed.add_field(name="Total Warnings", value=len(user_warnings[user.id]), inline=False)
    embed.add_field(name="Warned by", value=ctx.author.mention, inline=False)
    await ctx.send(embed=embed)


@bot.command(name="warnings", description="View warnings for a user")
async def warnings(ctx, user: discord.Member = None):
    target_user = user or ctx.author

    if target_user.id not in user_warnings or len(user_warnings[target_user.id]) == 0:
        embed = discord.Embed(title="✅ No Warnings", description=f"{target_user.mention} has no warnings.", color=discord.Color.green())
        await ctx.send(embed=embed)
        return

    embed = discord.Embed(title=f"⚠️ Warnings for {target_user.name}", color=discord.Color.orange())
    embed.description = f"Total warnings: {len(user_warnings[target_user.id])}"

    for i, warning in enumerate(user_warnings[target_user.id], 1):
        embed.add_field(
            name=f"Warning #{i}",
            value=f"**Reason:** {warning['reason']}\n**Warned by:** {warning['warned_by']}\n**Date:** {warning['date'].strftime('%Y-%m-%d %H:%M:%S')}",
            inline=False,
        )

    await ctx.send(embed=embed)


@bot.command(name="clear", description="Delete messages")
async def clear(ctx, amount: int = 5):
    if not check_permissions(ctx):
        embed = discord.Embed(
            title="❌ Permission Denied",
            description="You need Administrator permissions to use this command.",
            color=discord.Color.red(),
        )
        await ctx.send(embed=embed)
        return

    if amount < 1 or amount > 100:
        embed = discord.Embed(title="❌ Invalid Amount", description="Please specify an amount between 1 and 100.", color=discord.Color.red())
        await ctx.send(embed=embed)
        return

    deleted = await ctx.channel.purge(limit=amount + 1)

    embed = discord.Embed(title="🗑️ Messages Cleared", description=f"{len(deleted) - 1} messages have been deleted.", color=discord.Color.green())
    embed.add_field(name="Cleared by", value=ctx.author.mention, inline=False)

    msg = await ctx.send(embed=embed)
    await msg.delete(delay=5)


if __name__ == "__main__":
    bot.run(TOKEN)
