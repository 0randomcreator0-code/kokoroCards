import os
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
from datetime import datetime, timedelta
import random

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
PREFIX = "!"  # Custom prefix for non-slash commands

if not TOKEN:
    raise ValueError("DISCORD_TOKEN is not set. Add it to your .env file.")


class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True  # Required for prefix commands
        super().__init__(command_prefix=PREFIX, intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()


bot = MyBot()


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print(f"Prefix: {PREFIX}")


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
        timestamp=datetime.now()
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
        timestamp=datetime.now()
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
            timestamp=datetime.now()
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
        description="Here are all available commands:\n\n**Slash Commands** start with `/`\n**Prefix Commands** start with `!`",
        color=discord.Color.gold(),
        timestamp=datetime.now()
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
    
    embed.add_field(name="🛡️ Moderation Commands (Prefix: !)", value="", inline=False)
    mod_commands = [
        ("!kick @user [reason]", "Kick a user from the server"),
        ("!ban @user [reason]", "Ban a user from the server"),
        ("!unban user#tag", "Unban a user by tag (e.g., username#1234)"),
        ("!mute @user [duration]", "Mute a user for a duration (e.g., 10m, 1h, 1d)"),
        ("!unmute @user", "Unmute a user"),
        ("!warn @user [reason]", "Warn a user"),
        ("!warnings [@user]", "View warnings for a user or yourself"),
        ("!clear [amount]", "Delete messages (max 100, default 5)"),
    ]
    
    for cmd, desc in mod_commands:
        embed.add_field(name=cmd, value=desc, inline=False)
    
    await interaction.response.send_message(embed=embed)


# ==================== MODERATION COMMANDS ====================

# In-memory storage for warnings and mutes (reset on bot restart)
user_warnings = {}
muted_users = {}


def check_permissions(ctx):
    """Check if user has admin permissions"""
    return ctx.author.guild_permissions.administrator


@bot.command(name="kick", description="Kick a user from the server")
async def kick(ctx, user: discord.Member, *, reason="No reason provided"):
    if not check_permissions(ctx):
        embed = discord.Embed(
            title="❌ Permission Denied",
            description="You need Administrator permissions to use this command.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return
    
    if user == ctx.author:
        embed = discord.Embed(
            title="❌ Error",
            description="You cannot kick yourself!",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return
    
    if user == ctx.guild.owner:
        embed = discord.Embed(
            title="❌ Error",
            description="You cannot kick the server owner!",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return
    
    try:
        await user.kick(reason=reason)
        embed = discord.Embed(
            title="✅ User Kicked",
            description=f"{user.mention} has been kicked from the server.",
            color=discord.Color.green()
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Kicked by", value=ctx.author.mention, inline=False)
        await ctx.send(embed=embed)
    except discord.Forbidden:
        embed = discord.Embed(
            title="❌ Error",
            description="I don't have permission to kick this user.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)


@bot.command(name="ban", description="Ban a user from the server")
async def ban(ctx, user: discord.Member, *, reason="No reason provided"):
    if not check_permissions(ctx):
        embed = discord.Embed(
            title="❌ Permission Denied",
            description="You need Administrator permissions to use this command.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return
    
    if user == ctx.author:
        embed = discord.Embed(
            title="❌ Error",
            description="You cannot ban yourself!",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return
    
    if user == ctx.guild.owner:
        embed = discord.Embed(
            title="❌ Error",
            description="You cannot ban the server owner!",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return
    
    try:
        await user.ban(reason=reason)
        embed = discord.Embed(
            title="✅ User Banned",
            description=f"{user.mention} has been banned from the server.",
            color=discord.Color.green()
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Banned by", value=ctx.author.mention, inline=False)
        await ctx.send(embed=embed)
    except discord.Forbidden:
        embed = discord.Embed(
            title="❌ Error",
            description="I don't have permission to ban this user.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)


@bot.command(name="unban", description="Unban a user from the server")
async def unban(ctx, user_tag: str):
    if not check_permissions(ctx):
        embed = discord.Embed(
            title="❌ Permission Denied",
            description="You need Administrator permissions to use this command.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return
    
    try:
        # Parse user tag (e.g., username#1234)
        bans = [entry async for entry in ctx.guild.bans()]
        user_to_unban = None
        
        for ban in bans:
            if str(ban.user) == user_tag or ban.user.name == user_tag.split("#")[0]:
                user_to_unban = ban.user
                break
        
        if not user_to_unban:
            embed = discord.Embed(
                title="❌ Error",
                description=f"Could not find a banned user with tag: {user_tag}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        await ctx.guild.unban(user_to_unban)
        embed = discord.Embed(
            title="✅ User Unbanned",
            description=f"**{user_to_unban}** has been unbanned.",
            color=discord.Color.green()
        )
        embed.add_field(name="Unbanned by", value=ctx.author.mention, inline=False)
        await ctx.send(embed=embed)
    except discord.Forbidden:
        embed = discord.Embed(
            title="❌ Error",
            description="I don't have permission to unban users.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)


@bot.command(name="mute", description="Mute a user")
async def mute(ctx, user: discord.Member, duration: str = "10m"):
    if not check_permissions(ctx):
        embed = discord.Embed(
            title="❌ Permission Denied",
            description="You need Administrator permissions to use this command.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return
    
    if user == ctx.author:
        embed = discord.Embed(
            title="❌ Error",
            description="You cannot mute yourself!",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return
    
    # Parse duration
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
    except:
        embed = discord.Embed(
            title="❌ Invalid Duration",
            description="Use format: 10m, 1h, or 1d",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return
    
    muted_users[user.id] = mute_time
    embed = discord.Embed(
        title="🔇 User Muted",
        description=f"{user.mention} has been muted.",
        color=discord.Color.orange()
    )
    embed.add_field(name="Duration", value=duration, inline=False)
    embed.add_field(name="Muted by", value=ctx.author.mention, inline=False)
    await ctx.send(embed=embed)


@bot.command(name="unmute", description="Unmute a user")
async def unmute(ctx, user: discord.Member):
    if not check_permissions(ctx):
        embed = discord.Embed(
            title="❌ Permission Denied",
            description="You need Administrator permissions to use this command.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return
    
    if user.id in muted_users:
        del muted_users[user.id]
        embed = discord.Embed(
            title="🔊 User Unmuted",
            description=f"{user.mention} has been unmuted.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(
            title="❌ Error",
            description=f"{user.mention} is not muted.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)


@bot.command(name="warn", description="Warn a user")
async def warn(ctx, user: discord.Member, *, reason="No reason provided"):
    if not check_permissions(ctx):
        embed = discord.Embed(
            title="❌ Permission Denied",
            description="You need Administrator permissions to use this command.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return
    
    if user == ctx.author:
        embed = discord.Embed(
            title="❌ Error",
            description="You cannot warn yourself!",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return
    
    if user.id not in user_warnings:
        user_warnings[user.id] = []
    
    user_warnings[user.id].append({
        "reason": reason,
        "warned_by": ctx.author.name,
        "date": datetime.now()
    })
    
    embed = discord.Embed(
        title="⚠️ User Warned",
        description=f"{user.mention} has been warned.",
        color=discord.Color.orange()
    )
    embed.add_field(name="Reason", value=reason, inline=False)
    embed.add_field(name="Total Warnings", value=len(user_warnings[user.id]), inline=False)
    embed.add_field(name="Warned by", value=ctx.author.mention, inline=False)
    await ctx.send(embed=embed)


@bot.command(name="warnings", description="View warnings for a user")
async def warnings(ctx, user: discord.Member = None):
    target_user = user or ctx.author
    
    if target_user.id not in user_warnings or len(user_warnings[target_user.id]) == 0:
        embed = discord.Embed(
            title="✅ No Warnings",
            description=f"{target_user.mention} has no warnings.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
        return
    
    embed = discord.Embed(
        title=f"⚠️ Warnings for {target_user.name}",
        color=discord.Color.orange()
    )
    embed.description = f"Total warnings: {len(user_warnings[target_user.id])}"
    
    for i, warning in enumerate(user_warnings[target_user.id], 1):
        embed.add_field(
            name=f"Warning #{i}",
            value=f"**Reason:** {warning['reason']}\n**Warned by:** {warning['warned_by']}\n**Date:** {warning['date'].strftime('%Y-%m-%d %H:%M:%S')}",
            inline=False
        )
    
    await ctx.send(embed=embed)


@bot.command(name="clear", description="Delete messages")
async def clear(ctx, amount: int = 5):
    if not check_permissions(ctx):
        embed = discord.Embed(
            title="❌ Permission Denied",
            description="You need Administrator permissions to use this command.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return
    
    if amount < 1 or amount > 100:
        embed = discord.Embed(
            title="❌ Invalid Amount",
            description="Please specify an amount between 1 and 100.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return
    
    deleted = await ctx.channel.purge(limit=amount + 1)  # +1 to include the command message
    
    embed = discord.Embed(
        title="🗑️ Messages Cleared",
        description=f"{len(deleted) - 1} messages have been deleted.",
        color=discord.Color.green()
    )
    embed.add_field(name="Cleared by", value=ctx.author.mention, inline=False)
    
    msg = await ctx.send(embed=embed)
    await msg.delete(delay=5)  # Auto-delete confirmation after 5 seconds


if __name__ == "__main__":
    bot.run(TOKEN)
