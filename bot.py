import os
import discord
from discord import app_commands
from dotenv import load_dotenv
from datetime import datetime
import random

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise ValueError("DISCORD_TOKEN is not set. Add it to your .env file.")


class MyBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()


bot = MyBot()


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")


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
        description="Here are all available commands:",
        color=discord.Color.gold(),
        timestamp=datetime.now()
    )
    
    commands = [
        ("/ping", "Check if the bot is alive"),
        ("/hello @user", "Greet a user"),
        ("/userinfo [@user]", "Get information about a user"),
        ("/roll [sides]", "Roll a dice (default: 6 sides)"),
        ("/choose options", "Choose randomly from comma-separated options"),
        ("/serverinfo", "Get information about the server"),
        ("/avatar [@user]", "Get a user's avatar"),
        ("/echo message", "Echo a message"),
        ("/help", "Show this help message"),
    ]
    
    for cmd, desc in commands:
        embed.add_field(name=cmd, value=desc, inline=False)
    
    await interaction.response.send_message(embed=embed)


if __name__ == "__main__":
    bot.run(TOKEN)
