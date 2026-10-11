import os
import sqlite3
import random
from datetime import datetime, timedelta

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
PREFIX = "k!"
DB_PATH = os.path.join(os.getcwd(), "kokoro_cards.db")

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

user_data = {}
card_counter = 1000
locked_cards = set()
trade_offers = {}
auctions = {}
auction_counter = 1


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


def connect_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = connect_db()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            tokens INTEGER NOT NULL DEFAULT 1000
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS cards (
            card_id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id TEXT NOT NULL,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            locked INTEGER NOT NULL DEFAULT 0,
            obtained_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def load_user_data():
    global card_counter

    user_data.clear()
    conn = connect_db()

    for row in conn.execute("SELECT user_id, tokens FROM users ORDER BY user_id"):
        user_id = int(row["user_id"])
        user_data[user_id] = {"cards": {}, "tokens": int(row["tokens"]), "inventory": []}

    for row in conn.execute("SELECT * FROM cards ORDER BY card_id"):
        owner_id = int(row["owner_id"])
        user_data.setdefault(owner_id, {"cards": {}, "tokens": 1000, "inventory": []})
        card_id = int(row["card_id"])
        card_entry = {
            "id": card_id,
            "name": row["name"],
            "category": row["category"],
            "locked": bool(row["locked"]),
            "obtained_at": row["obtained_at"],
        }
        user_data[owner_id]["cards"][card_id] = card_entry
        user_data[owner_id]["inventory"].append(card_id)
        if card_id >= card_counter:
            card_counter = card_id + 1

    conn.close()


def save_user_data(user_id):
    conn = connect_db()
    uid = str(user_id)
    user = user_data.get(user_id)

    if not user:
        conn.close()
        return

    conn.execute(
        "INSERT INTO users (user_id, tokens) VALUES (?, ?) ON CONFLICT(user_id) DO UPDATE SET tokens = excluded.tokens",
        (uid, int(user["tokens"])),
    )
    conn.execute("DELETE FROM cards WHERE owner_id = ?", (uid,))

    for card_id in sorted(user["cards"].keys()):
        card = user["cards"][card_id]
        conn.execute(
            "INSERT INTO cards (card_id, owner_id, name, category, locked, obtained_at) VALUES (?, ?, ?, ?, ?, ?)",
            (
                int(card_id),
                uid,
                card["name"],
                card["category"],
                1 if card["locked"] else 0,
                card["obtained_at"],
            ),
        )

    conn.commit()
    conn.close()


def initialize_user(user_id):
    user_id = int(user_id)
    if user_id not in user_data:
        user_data[user_id] = {"cards": {}, "tokens": 1000, "inventory": []}

    conn = connect_db()
    conn.execute(
        "INSERT OR IGNORE INTO users (user_id, tokens) VALUES (?, ?)",
        (str(user_id), 1000),
    )
    conn.commit()
    conn.close()

    if user_id in user_data and not user_data[user_id]["cards"]:
        save_user_data(user_id)


def generate_card_id():
    global card_counter
    card_counter += 1
    return card_counter


init_db()
load_user_data()


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
    initialize_user(ctx.author.id)

    if category.lower() == "random" or category.lower() == "r":
        selected_category = random.choice(list(CARD_CATEGORIES.keys()))
    else:
        selected_category = normalize_category(category)
        if selected_category not in CARD_CATEGORIES:
            valid = ", ".join(sorted(CARD_CATEGORIES.keys()))
            await ctx.send(f"Invalid category. Choose one of: {valid}")
            return

    card_name = random.choice(CARD_CATEGORIES[selected_category])
    card_id = generate_card_id()

    card_data = {
        "id": card_id,
        "name": card_name,
        "category": selected_category,
        "locked": False,
        "obtained_at": datetime.now().isoformat(),
    }

    user_data[ctx.author.id]["cards"][card_id] = card_data
    user_data[ctx.author.id]["inventory"].append(card_id)
    save_user_data(ctx.author.id)

    embed = discord.Embed(
        title=f"🎴 {selected_category.upper()} Card",
        description=f"Recommended pick: **{card_name}**",
        color=discord.Color.magenta(),
        timestamp=datetime.now(),
    )
    embed.add_field(name="Category", value=selected_category.title(), inline=True)
    embed.add_field(name="Card ID", value=f"`{card_id}`", inline=True)
    embed.add_field(name="Status", value="🔓 Unlocked", inline=True)
    await ctx.send(embed=embed)


# ==================== LOCK/UNLOCK COMMANDS ====================

@bot.command(name="lock", help="Lock a card by ID to prevent trading")
async def lock_card(ctx, card_id: int):
    initialize_user(ctx.author.id)

    if card_id not in user_data[ctx.author.id]["cards"]:
        await ctx.send(f"❌ You don't own card ID `{card_id}`")
        return

    card = user_data[ctx.author.id]["cards"][card_id]

    if card["locked"]:
        await ctx.send(f"❌ Card ID `{card_id}` is already locked")
        return

    card["locked"] = True
    locked_cards.add(card_id)
    save_user_data(ctx.author.id)

    embed = discord.Embed(
        title="🔒 Card Locked",
        description=f"Card **{card['name']}** (ID: `{card_id}`) has been locked",
        color=discord.Color.red(),
    )
    embed.add_field(name="Status", value="🔒 Locked - Cannot be traded", inline=False)
    await ctx.send(embed=embed)


@bot.command(name="unlock", help="Unlock a card by ID to allow trading")
async def unlock_card(ctx, card_id: int):
    initialize_user(ctx.author.id)

    if card_id not in user_data[ctx.author.id]["cards"]:
        await ctx.send(f"❌ You don't own card ID `{card_id}`")
        return

    card = user_data[ctx.author.id]["cards"][card_id]

    if not card["locked"]:
        await ctx.send(f"❌ Card ID `{card_id}` is already unlocked")
        return

    card["locked"] = False
    locked_cards.discard(card_id)
    save_user_data(ctx.author.id)

    embed = discord.Embed(
        title="🔓 Card Unlocked",
        description=f"Card **{card['name']}** (ID: `{card_id}`) has been unlocked",
        color=discord.Color.green(),
    )
    embed.add_field(name="Status", value="🔓 Unlocked - Can be traded", inline=False)
    await ctx.send(embed=embed)


# ==================== TRADE CARD COMMANDS ====================

@bot.command(name="tc", aliases=["tradecard", "trade"], help="Trade card(s) with another user")
async def trade_card(ctx, target_user: discord.Member, *, details: str = None):
    initialize_user(ctx.author.id)
    initialize_user(target_user.id)

    if target_user == ctx.author:
        await ctx.send("❌ You cannot trade with yourself")
        return

    if details is None:
        embed = discord.Embed(
            title="💳 Trade Card Command",
            description="Usage: `k!tc @user card_id1, card_id2 [tokens]`",
            color=discord.Color.blue(),
        )
        embed.add_field(
            name="Example",
            value="`k!tc @user 1001, 1002 100`\n(Trade cards 1001 and 1002 + 100 tokens to @user)",
            inline=False,
        )
        embed.add_field(
            name="Note",
            value="Locked cards cannot be traded. Use `k!unlock card_id` to unlock.",
            inline=False,
        )
        await ctx.send(embed=embed)
        return

    parts = details.split()
    card_ids_str = parts[0]
    tokens_amount = 0

    if len(parts) > 1:
        try:
            tokens_amount = int(parts[-1])
        except ValueError:
            pass

    try:
        card_ids = [int(cid.strip(",")) for cid in card_ids_str.split(",")]
    except ValueError:
        await ctx.send("❌ Invalid card ID format. Use: `k!tc @user 1001, 1002`")
        return

    for cid in card_ids:
        if cid not in user_data[ctx.author.id]["cards"]:
            await ctx.send(f"❌ You don't own card ID `{cid}`")
            return

        card = user_data[ctx.author.id]["cards"][cid]
        if card["locked"]:
            await ctx.send(f"❌ Card ID `{cid}` is locked and cannot be traded. Use `k!unlock {cid}` first.")
            return

    if tokens_amount > user_data[ctx.author.id]["tokens"]:
        await ctx.send(f"❌ You only have {user_data[ctx.author.id]['tokens']} tokens")
        return

    trade_id = len(trade_offers)
    trade_offers[trade_id] = {
        "from_user": ctx.author.id,
        "to_user": target_user.id,
        "cards": card_ids,
        "tokens": tokens_amount,
        "status": "pending",
    }

    embed = discord.Embed(
        title="💳 Trade Offer Created",
        description=f"{ctx.author.mention} wants to trade with {target_user.mention}",
        color=discord.Color.gold(),
    )
    embed.add_field(name="Trade ID", value=f"`{trade_id}`", inline=False)
    embed.add_field(name="Cards Offered", value=", ".join([f"`{cid}`" for cid in card_ids]), inline=False)
    embed.add_field(name="Tokens", value=f"{tokens_amount} 🪙", inline=False)
    embed.add_field(name="Command to Accept", value=f"`k!accept_trade {trade_id}`", inline=False)
    await ctx.send(embed=embed)


@bot.command(name="accept_trade", help="Accept a trade offer")
async def accept_trade(ctx, trade_id: int):
    initialize_user(ctx.author.id)

    if trade_id not in trade_offers:
        await ctx.send(f"❌ Trade ID `{trade_id}` not found")
        return

    trade = trade_offers[trade_id]

    if trade["to_user"] != ctx.author.id:
        await ctx.send("❌ This trade offer is not for you")
        return

    from_user_id = trade["from_user"]
    to_user_id = trade["to_user"]

    for card_id in trade["cards"]:
        card = user_data[from_user_id]["cards"].pop(card_id)
        user_data[to_user_id]["cards"][card_id] = card
        user_data[from_user_id]["inventory"].remove(card_id)
        user_data[to_user_id]["inventory"].append(card_id)

    user_data[from_user_id]["tokens"] -= trade["tokens"]
    user_data[to_user_id]["tokens"] += trade["tokens"]
    save_user_data(from_user_id)
    save_user_data(to_user_id)

    trade["status"] = "completed"

    embed = discord.Embed(
        title="✅ Trade Completed",
        description="Trade offer has been accepted and executed",
        color=discord.Color.green(),
    )
    await ctx.send(embed=embed)


# ==================== AUCTION COMMANDS ====================

@bot.command(name="as", aliases=["auctionsearch"], help="Search for auctions with specific cards")
async def auction_search(ctx, *, category: str = "all"):
    initialize_user(ctx.author.id)

    if not auctions:
        await ctx.send("❌ No active auctions available")
        return

    embed = discord.Embed(
        title="🏆 Auction Search",
        description=f"Searching auctions for: **{category}**",
        color=discord.Color.purple(),
        timestamp=datetime.now(),
    )

    auction_count = 0
    for auction_id, auction in auctions.items():
        if category.lower() == "all" or any(normalize_category(category) == card.get("category") for card in auction["cards"]):
            card_names = ", ".join([card["name"] for card in auction["cards"]])
            embed.add_field(
                name=f"Auction #{auction_id}",
                value=f"Cards: {card_names}\nStarting Price: {auction['starting_price']} 🪙\nCurrent Bid: {auction['current_bid']} 🪙",
                inline=False,
            )
            auction_count += 1

    if auction_count == 0:
        await ctx.send(f"❌ No auctions found for category: {category}")
        return

    embed.set_footer(text=f"Use k!ai <auction_id> for more details")
    await ctx.send(embed=embed)


@bot.command(name="ai", aliases=["auctioninfo"], help="Get detailed info about an auction")
async def auction_info(ctx, auction_id: int):
    initialize_user(ctx.author.id)

    if auction_id not in auctions:
        await ctx.send(f"❌ Auction ID `{auction_id}` not found")
        return

    auction = auctions[auction_id]

    embed = discord.Embed(
        title=f"🏆 Auction #{auction_id} Details",
        color=discord.Color.gold(),
        timestamp=datetime.now(),
    )

    card_names = "\n".join([f"• {card['name']} (ID: `{card['id']}`)" for card in auction["cards"]])
    embed.add_field(name="Cards in Auction", value=card_names, inline=False)
    embed.add_field(name="Starting Price", value=f"{auction['starting_price']} 🪙", inline=True)
    embed.add_field(name="Current Bid", value=f"{auction['current_bid']} 🪙", inline=True)

    if auction["highest_bidder"]:
        highest_bidder = await bot.fetch_user(auction["highest_bidder"])
        embed.add_field(name="Highest Bidder", value=highest_bidder.mention, inline=False)

    embed.add_field(name="Place a Bid", value=f"Use `k!bid {auction_id} <amount>`", inline=False)
    await ctx.send(embed=embed)


@bot.command(name="create_auction", help="Create an auction for your cards")
async def create_auction(ctx, starting_price: int, *, card_ids_str: str):
    initialize_user(ctx.author.id)

    if starting_price < 1:
        await ctx.send("❌ Starting price must be at least 1 token")
        return

    try:
        card_ids = [int(cid.strip(",")) for cid in card_ids_str.split(",")]
    except ValueError:
        await ctx.send("❌ Invalid card ID format")
        return

    cards = []
    for card_id in card_ids:
        if card_id not in user_data[ctx.author.id]["cards"]:
            await ctx.send(f"❌ You don't own card ID `{card_id}`")
            return

        card = user_data[ctx.author.id]["cards"][card_id]
        if card["locked"]:
            await ctx.send(f"❌ Card ID `{card_id}` is locked")
            return

        cards.append(card)

    global auction_counter
    auction_id = auction_counter
    auction_counter += 1

    auctions[auction_id] = {
        "owner": ctx.author.id,
        "cards": cards,
        "starting_price": starting_price,
        "current_bid": starting_price,
        "highest_bidder": None,
    }

    for card_id in card_ids:
        user_data[ctx.author.id]["cards"].pop(card_id)
        user_data[ctx.author.id]["inventory"].remove(card_id)
    save_user_data(ctx.author.id)

    embed = discord.Embed(
        title="🏆 Auction Created",
        description=f"Auction #{auction_id} is now live",
        color=discord.Color.green(),
    )
    card_names = "\n".join([f"• {card['name']}" for card in cards])
    embed.add_field(name="Cards", value=card_names, inline=False)
    embed.add_field(name="Starting Price", value=f"{starting_price} 🪙", inline=False)
    embed.add_field(name="Bid Command", value=f"`k!bid {auction_id} <amount>`", inline=False)
    await ctx.send(embed=embed)


@bot.command(name="bid", help="Place a bid on an auction")
async def place_bid(ctx, auction_id: int, bid_amount: int):
    initialize_user(ctx.author.id)

    if auction_id not in auctions:
        await ctx.send(f"❌ Auction ID `{auction_id}` not found")
        return

    auction = auctions[auction_id]

    if bid_amount <= auction["current_bid"]:
        await ctx.send(f"❌ Bid must be higher than current bid ({auction['current_bid']} 🪙)")
        return

    if bid_amount > user_data[ctx.author.id]["tokens"]:
        await ctx.send(f"❌ You only have {user_data[ctx.author.id]['tokens']} tokens")
        return

    auction["current_bid"] = bid_amount
    auction["highest_bidder"] = ctx.author.id

    embed = discord.Embed(
        title=f"💰 Bid Placed on Auction #{auction_id}",
        description=f"{ctx.author.mention} placed a bid of {bid_amount} 🪙",
        color=discord.Color.gold(),
    )
    await ctx.send(embed=embed)


# ==================== TOKEN COMMANDS ====================

@bot.command(name="token", aliases=["t", "T"], help="Check your token balance")
async def check_tokens(ctx):
    initialize_user(ctx.author.id)
    tokens = user_data[ctx.author.id]["tokens"]

    embed = discord.Embed(
        title="🪙 Token Balance",
        description=f"{ctx.author.mention}'s Balance",
        color=discord.Color.yellow(),
    )
    embed.add_field(name="Tokens", value=f"{tokens} 🪙", inline=True)
    embed.add_field(name="Card Count", value=f"{len(user_data[ctx.author.id]['inventory'])} cards", inline=True)
    await ctx.send(embed=embed)


@bot.command(name="give_tokens", help="Admin command to give tokens to a user")
async def give_tokens(ctx, user: discord.Member, amount: int):
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("❌ Only administrators can use this command")
        return

    initialize_user(user.id)
    user_data[user.id]["tokens"] += amount
    save_user_data(user.id)

    embed = discord.Embed(
        title="💰 Tokens Added",
        description=f"{amount} 🪙 added to {user.mention}'s balance",
        color=discord.Color.green(),
    )
    embed.add_field(name="New Balance", value=f"{user_data[user.id]['tokens']} 🪙", inline=False)
    await ctx.send(embed=embed)


# ==================== INVENTORY COMMAND ====================

@bot.command(name="inv", aliases=["inventory"], help="View your card inventory")
async def inventory(ctx, user: discord.Member = None):
    target_user = user or ctx.author
    initialize_user(target_user.id)

    cards = user_data[target_user.id]["cards"]
    tokens = user_data[target_user.id]["tokens"]

    if not cards:
        embed = discord.Embed(
            title=f"📦 {target_user.name}'s Inventory",
            description="No cards yet. Use `k!card` to get started!",
            color=discord.Color.blue(),
        )
        await ctx.send(embed=embed)
        return

    embed = discord.Embed(
        title=f"📦 {target_user.name}'s Inventory",
        description=f"Total Cards: {len(cards)} | Tokens: {tokens} 🪙",
        color=discord.Color.blue(),
    )

    for card_id, card in list(cards.items())[:10]:
        lock_status = "🔒 Locked" if card["locked"] else "🔓 Unlocked"
        embed.add_field(
            name=f"{card['name']} (ID: `{card_id}`)",
            value=f"Category: {card['category'].title()}\nStatus: {lock_status}",
            inline=False,
        )

    if len(cards) > 10:
        embed.set_footer(text=f"Showing 10 of {len(cards)} cards")

    await ctx.send(embed=embed)


# ==================== SLASH COMMANDS ====================

@bot.tree.command(name="ping", description="Check if the bot is alive")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong!")


@bot.tree.command(name="hello", description="Say hello to someone")
@app_commands.describe(user="Who to greet")
async def hello(interaction: discord.Interaction, user: discord.Member):
    await interaction.response.send_message(f"Hello {user.mention}!")


@bot.tree.command(name="help", description="Get help with available commands")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Bot Commands",
        description="Here are all available commands:\n\n**Prefix:** `k!`",
        color=discord.Color.gold(),
        timestamp=datetime.now(),
    )

    embed.add_field(name="🎴 Card Commands", value="", inline=False)
    for cmd, desc in [
        ("k!card [category]", "Get a random card (anime, cartoon, kpop, kdrama, cdrama, jdrama, manhwa)"),
        ("k!c", "Alias for k!card"),
    ]:
        embed.add_field(name=cmd, value=desc, inline=False)

    embed.add_field(name="🔐 Lock/Unlock Commands", value="", inline=False)
    for cmd, desc in [
        ("k!lock <card_id>", "Lock a card to prevent trading"),
        ("k!unlock <card_id>", "Unlock a card to allow trading"),
    ]:
        embed.add_field(name=cmd, value=desc, inline=False)

    embed.add_field(name="💳 Trade Commands", value="", inline=False)
    for cmd, desc in [
        ("k!tc @user <card_ids> [tokens]", "Offer a trade to another user"),
        ("k!accept_trade <trade_id>", "Accept a trade offer"),
    ]:
        embed.add_field(name=cmd, value=desc, inline=False)

    embed.add_field(name="🏆 Auction Commands", value="", inline=False)
    for cmd, desc in [
        ("k!as [category]", "Search for auctions"),
        ("k!ai <auction_id>", "Get auction details"),
        ("k!create_auction <starting_price> <card_ids>", "Create an auction"),
        ("k!bid <auction_id> <amount>", "Place a bid"),
    ]:
        embed.add_field(name=cmd, value=desc, inline=False)

    embed.add_field(name="🪙 Token Commands", value="", inline=False)
    for cmd, desc in [
        ("k!token / k!t", "Check your token balance"),
        ("k!inv", "View your card inventory"),
    ]:
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
