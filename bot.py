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

RARITIES = {
    "common": {"weight": 50, "value": 50},
    "uncommon": {"weight": 30, "value": 150},
    "rare": {"weight": 15, "value": 500},
    "epic": {"weight": 4, "value": 1500},
    "legendary": {"weight": 1, "value": 5000},
}

CATEGORY_MULTIPLIERS = {
    "anime": 1.0,
    "cartoon": 0.8,
    "kpop": 1.2,
    "kdrama": 1.1,
    "cdrama": 1.0,
    "jdrama": 1.0,
    "manhwa": 1.3,
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


def get_card_value(rarity: str, category: str) -> int:
    base_value = RARITIES.get(rarity, {}).get("value", 50)
    multiplier = CATEGORY_MULTIPLIERS.get(category, 1.0)
    return int(base_value * multiplier)


def generate_rarity() -> str:
    weights = [v["weight"] for v in RARITIES.values()]
    rarities_list = list(RARITIES.keys())
    return random.choices(rarities_list, weights=weights, k=1)[0]


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
            rarity TEXT NOT NULL,
            value INTEGER NOT NULL,
            locked INTEGER NOT NULL DEFAULT 0,
            obtained_at TEXT NOT NULL,
            FOREIGN KEY (owner_id) REFERENCES users(user_id)
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS trades (
            trade_id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_user_id TEXT NOT NULL,
            to_user_id TEXT NOT NULL,
            cards_offered TEXT NOT NULL,
            tokens_offered INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL,
            completed_at TEXT,
            FOREIGN KEY (from_user_id) REFERENCES users(user_id),
            FOREIGN KEY (to_user_id) REFERENCES users(user_id)
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS auctions (
            auction_id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id TEXT NOT NULL,
            cards_ids TEXT NOT NULL,
            starting_price INTEGER NOT NULL,
            current_bid INTEGER NOT NULL,
            highest_bidder_id TEXT,
            status TEXT NOT NULL DEFAULT 'active',
            created_at TEXT NOT NULL,
            ended_at TEXT,
            FOREIGN KEY (owner_id) REFERENCES users(user_id),
            FOREIGN KEY (highest_bidder_id) REFERENCES users(user_id)
        )
        """
    )

    conn.commit()
    conn.close()


def initialize_user(user_id):
    user_id = str(user_id)
    conn = connect_db()
    conn.execute(
        "INSERT OR IGNORE INTO users (user_id, tokens) VALUES (?, ?)",
        (user_id, 1000),
    )
    conn.commit()
    conn.close()


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

@bot.command(name="card", aliases=["c", "C"], help="Get a random card from a category or choose a random one.")
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
    rarity = generate_rarity()
    card_value = get_card_value(rarity, selected_category)

    conn = connect_db()
    conn.execute(
        """
        INSERT INTO cards (owner_id, name, category, rarity, value, locked, obtained_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            str(ctx.author.id),
            card_name,
            selected_category,
            rarity,
            card_value,
            0,
            datetime.now().isoformat(),
        ),
    )
    conn.commit()

    result = conn.execute("SELECT last_insert_rowid() as card_id").fetchone()
    card_id = result["card_id"]
    conn.close()

    rarity_emoji = {
        "common": "⚪",
        "uncommon": "🟢",
        "rare": "🔵",
        "epic": "🟣",
        "legendary": "🟡",
    }

    embed = discord.Embed(
        title=f"🎴 {selected_category.upper()} Card",
        description=f"**{card_name}**",
        color=discord.Color.magenta(),
        timestamp=datetime.now(),
    )
    embed.add_field(name="Category", value=selected_category.title(), inline=True)
    embed.add_field(name="Card ID", value=f"`{card_id}`", inline=True)
    embed.add_field(name="Rarity", value=f"{rarity_emoji.get(rarity, '')} {rarity.title()}", inline=True)
    embed.add_field(name="Value", value=f"{card_value} 🪙", inline=True)
    embed.add_field(name="Status", value="🔓 Unlocked", inline=True)
    await ctx.send(embed=embed)


# ==================== LOCK/UNLOCK COMMANDS ====================

@bot.command(name="lock", help="Lock a card by ID to prevent trading")
async def lock_card(ctx, card_id: int):
    initialize_user(ctx.author.id)

    conn = connect_db()
    card = conn.execute(
        "SELECT * FROM cards WHERE card_id = ? AND owner_id = ?",
        (card_id, str(ctx.author.id)),
    ).fetchone()

    if not card:
        await ctx.send(f"❌ You don't own card ID `{card_id}`")
        conn.close()
        return

    if card["locked"]:
        await ctx.send(f"❌ Card ID `{card_id}` is already locked")
        conn.close()
        return

    conn.execute("UPDATE cards SET locked = 1 WHERE card_id = ?", (card_id,))
    conn.commit()
    conn.close()

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

    conn = connect_db()
    card = conn.execute(
        "SELECT * FROM cards WHERE card_id = ? AND owner_id = ?",
        (card_id, str(ctx.author.id)),
    ).fetchone()

    if not card:
        await ctx.send(f"❌ You don't own card ID `{card_id}`")
        conn.close()
        return

    if not card["locked"]:
        await ctx.send(f"❌ Card ID `{card_id}` is already unlocked")
        conn.close()
        return

    conn.execute("UPDATE cards SET locked = 0 WHERE card_id = ?", (card_id,))
    conn.commit()
    conn.close()

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

    conn = connect_db()

    user = conn.execute("SELECT tokens FROM users WHERE user_id = ?", (str(ctx.author.id),)).fetchone()
    if tokens_amount > user["tokens"]:
        await ctx.send(f"❌ You only have {user['tokens']} tokens")
        conn.close()
        return

    for cid in card_ids:
        card = conn.execute(
            "SELECT * FROM cards WHERE card_id = ? AND owner_id = ?",
            (cid, str(ctx.author.id)),
        ).fetchone()

        if not card:
            await ctx.send(f"❌ You don't own card ID `{cid}`")
            conn.close()
            return

        if card["locked"]:
            await ctx.send(f"❌ Card ID `{cid}` is locked and cannot be traded. Use `k!unlock {cid}` first.")
            conn.close()
            return

    cards_str = ",".join(str(cid) for cid in card_ids)
    conn.execute(
        """
        INSERT INTO trades (from_user_id, to_user_id, cards_offered, tokens_offered, status, created_at)
        VALUES (?, ?, ?, ?, 'pending', ?)
        """,
        (str(ctx.author.id), str(target_user.id), cards_str, tokens_amount, datetime.now().isoformat()),
    )
    conn.commit()

    result = conn.execute("SELECT last_insert_rowid() as trade_id").fetchone()
    trade_id = result["trade_id"]
    conn.close()

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

    conn = connect_db()
    trade = conn.execute(
        "SELECT * FROM trades WHERE trade_id = ?",
        (trade_id,),
    ).fetchone()

    if not trade:
        await ctx.send(f"❌ Trade ID `{trade_id}` not found")
        conn.close()
        return

    if trade["to_user_id"] != str(ctx.author.id):
        await ctx.send("❌ This trade offer is not for you")
        conn.close()
        return

    if trade["status"] != "pending":
        await ctx.send(f"❌ This trade is already {trade['status']}")
        conn.close()
        return

    from_user_id = trade["from_user_id"]
    to_user_id = trade["to_user_id"]
    card_ids = [int(cid) for cid in trade["cards_offered"].split(",")]
    tokens_offered = trade["tokens_offered"]

    try:
        for card_id in card_ids:
            conn.execute(
                "UPDATE cards SET owner_id = ? WHERE card_id = ?",
                (to_user_id, card_id),
            )

        conn.execute(
            "UPDATE users SET tokens = tokens - ? WHERE user_id = ?",
            (tokens_offered, from_user_id),
        )
        conn.execute(
            "UPDATE users SET tokens = tokens + ? WHERE user_id = ?",
            (tokens_offered, to_user_id),
        )

        conn.execute(
            "UPDATE trades SET status = 'completed', completed_at = ? WHERE trade_id = ?",
            (datetime.now().isoformat(), trade_id),
        )

        conn.commit()

        embed = discord.Embed(
            title="✅ Trade Completed",
            description="Trade offer has been accepted and executed",
            color=discord.Color.green(),
        )
        await ctx.send(embed=embed)
    except Exception as e:
        conn.rollback()
        await ctx.send(f"❌ Error completing trade: {str(e)}")
    finally:
        conn.close()


@bot.command(name="trades", help="View your pending trades")
async def view_trades(ctx):
    initialize_user(ctx.author.id)

    conn = connect_db()
    trades = conn.execute(
        "SELECT * FROM trades WHERE (from_user_id = ? OR to_user_id = ?) AND status = 'pending' ORDER BY trade_id DESC",
        (str(ctx.author.id), str(ctx.author.id)),
    ).fetchall()
    conn.close()

    if not trades:
        await ctx.send("❌ No pending trades")
        return

    embed = discord.Embed(
        title="💳 Your Pending Trades",
        color=discord.Color.blue(),
    )

    for trade in trades[:10]:
        direction = "📤 Sent" if trade["from_user_id"] == str(ctx.author.id) else "📥 Received"
        embed.add_field(
            name=f"Trade #{trade['trade_id']} {direction}",
            value=f"Cards: {trade['cards_offered']}\nTokens: {trade['tokens_offered']} 🪙",
            inline=False,
        )

    await ctx.send(embed=embed)


# ==================== AUCTION COMMANDS ====================

@bot.command(name="as", aliases=["auctionsearch"], help="Search for auctions")
async def auction_search(ctx, *, category: str = "all"):
    initialize_user(ctx.author.id)

    conn = connect_db()
    auctions_data = conn.execute(
        "SELECT * FROM auctions WHERE status = 'active' ORDER BY auction_id DESC LIMIT 20"
    ).fetchall()
    conn.close()

    if not auctions_data:
        await ctx.send("❌ No active auctions available")
        return

    embed = discord.Embed(
        title="🏆 Auction Search",
        description=f"Searching auctions for: **{category}**",
        color=discord.Color.purple(),
        timestamp=datetime.now(),
    )

    auction_count = 0
    for auction in auctions_data:
        card_ids = [int(cid) for cid in auction["cards_ids"].split(",")]

        conn = connect_db()
        cards = conn.execute(
            f"SELECT * FROM cards WHERE card_id IN ({','.join('?' * len(card_ids))})",
            card_ids,
        ).fetchall()
        conn.close()

        if category.lower() != "all" and not any(normalize_category(category) == card["category"] for card in cards):
            continue

        card_names = ", ".join([card["name"] for card in cards])
        embed.add_field(
            name=f"Auction #{auction['auction_id']}",
            value=f"Cards: {card_names}\nCurrent Bid: {auction['current_bid']} 🪙",
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

    conn = connect_db()
    auction = conn.execute(
        "SELECT * FROM auctions WHERE auction_id = ?",
        (auction_id,),
    ).fetchone()

    if not auction:
        await ctx.send(f"❌ Auction ID `{auction_id}` not found")
        conn.close()
        return

    card_ids = [int(cid) for cid in auction["cards_ids"].split(",")]
    cards = conn.execute(
        f"SELECT * FROM cards WHERE card_id IN ({','.join('?' * len(card_ids))})",
        card_ids,
    ).fetchall()
    conn.close()

    embed = discord.Embed(
        title=f"🏆 Auction #{auction_id} Details",
        color=discord.Color.gold(),
        timestamp=datetime.now(),
    )

    card_names = "\n".join([f"• {card['name']} (ID: `{card['card_id']}`, Rarity: {card['rarity'].title()})" for card in cards])
    embed.add_field(name="Cards in Auction", value=card_names, inline=False)
    embed.add_field(name="Starting Price", value=f"{auction['starting_price']} 🪙", inline=True)
    embed.add_field(name="Current Bid", value=f"{auction['current_bid']} 🪙", inline=True)

    if auction["highest_bidder_id"]:
        try:
            highest_bidder = await bot.fetch_user(int(auction["highest_bidder_id"]))
            embed.add_field(name="Highest Bidder", value=highest_bidder.mention, inline=False)
        except:
            pass

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

    conn = connect_db()

    for card_id in card_ids:
        card = conn.execute(
            "SELECT * FROM cards WHERE card_id = ? AND owner_id = ?",
            (card_id, str(ctx.author.id)),
        ).fetchone()

        if not card:
            await ctx.send(f"❌ You don't own card ID `{card_id}`")
            conn.close()
            return

        if card["locked"]:
            await ctx.send(f"❌ Card ID `{card_id}` is locked")
            conn.close()
            return

    cards_str = ",".join(str(cid) for cid in card_ids)
    conn.execute(
        """
        INSERT INTO auctions (owner_id, cards_ids, starting_price, current_bid, status, created_at)
        VALUES (?, ?, ?, ?, 'active', ?)
        """,
        (str(ctx.author.id), cards_str, starting_price, starting_price, datetime.now().isoformat()),
    )
    conn.commit()

    result = conn.execute("SELECT last_insert_rowid() as auction_id").fetchone()
    auction_id = result["auction_id"]

    cards = conn.execute(
        f"SELECT * FROM cards WHERE card_id IN ({','.join('?' * len(card_ids))})",
        card_ids,
    ).fetchall()
    conn.close()

    embed = discord.Embed(
        title="🏆 Auction Created",
        description=f"Auction #{auction_id} is now live",
        color=discord.Color.green(),
    )
    card_names = "\n".join([f"• {card['name']} ({card['rarity'].title()})" for card in cards])
    embed.add_field(name="Cards", value=card_names, inline=False)
    embed.add_field(name="Starting Price", value=f"{starting_price} 🪙", inline=False)
    embed.add_field(name="Bid Command", value=f"`k!bid {auction_id} <amount>`", inline=False)
    await ctx.send(embed=embed)


@bot.command(name="bid", help="Place a bid on an auction")
async def place_bid(ctx, auction_id: int, bid_amount: int):
    initialize_user(ctx.author.id)

    conn = connect_db()
    auction = conn.execute(
        "SELECT * FROM auctions WHERE auction_id = ?",
        (auction_id,),
    ).fetchone()

    if not auction:
        await ctx.send(f"❌ Auction ID `{auction_id}` not found")
        conn.close()
        return

    if auction["status"] != "active":
        await ctx.send(f"❌ Auction is {auction['status']}")
        conn.close()
        return

    if bid_amount <= auction["current_bid"]:
        await ctx.send(f"❌ Bid must be higher than current bid ({auction['current_bid']} 🪙)")
        conn.close()
        return

    user = conn.execute(
        "SELECT tokens FROM users WHERE user_id = ?",
        (str(ctx.author.id),),
    ).fetchone()

    if bid_amount > user["tokens"]:
        await ctx.send(f"❌ You only have {user['tokens']} tokens")
        conn.close()
        return

    conn.execute(
        "UPDATE auctions SET current_bid = ?, highest_bidder_id = ? WHERE auction_id = ?",
        (bid_amount, str(ctx.author.id), auction_id),
    )
    conn.commit()
    conn.close()

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

    conn = connect_db()
    user = conn.execute(
        "SELECT tokens FROM users WHERE user_id = ?",
        (str(ctx.author.id),),
    ).fetchone()

    card_count = conn.execute(
        "SELECT COUNT(*) as count FROM cards WHERE owner_id = ?",
        (str(ctx.author.id),),
    ).fetchone()
    conn.close()

    embed = discord.Embed(
        title="🪙 Token Balance",
        description=f"{ctx.author.mention}'s Balance",
        color=discord.Color.yellow(),
    )
    embed.add_field(name="Tokens", value=f"{user['tokens']} 🪙", inline=True)
    embed.add_field(name="Card Count", value=f"{card_count['count']} cards", inline=True)
    await ctx.send(embed=embed)


@bot.command(name="give_tokens", help="Admin command to give tokens to a user")
async def give_tokens(ctx, user: discord.Member, amount: int):
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("❌ Only administrators can use this command")
        return

    initialize_user(user.id)

    conn = connect_db()
    conn.execute(
        "UPDATE users SET tokens = tokens + ? WHERE user_id = ?",
        (amount, str(user.id)),
    )
    conn.commit()

    user_data = conn.execute(
        "SELECT tokens FROM users WHERE user_id = ?",
        (str(user.id),),
    ).fetchone()
    conn.close()

    embed = discord.Embed(
        title="💰 Tokens Added",
        description=f"{amount} 🪙 added to {user.mention}'s balance",
        color=discord.Color.green(),
    )
    embed.add_field(name="New Balance", value=f"{user_data['tokens']} 🪙", inline=False)
    await ctx.send(embed=embed)


# ==================== INVENTORY COMMAND ====================

@bot.command(name="inv", aliases=["inventory"], help="View your card inventory")
async def inventory(ctx, user: discord.Member = None):
    target_user = user or ctx.author
    initialize_user(target_user.id)

    conn = connect_db()
    cards = conn.execute(
        "SELECT * FROM cards WHERE owner_id = ? ORDER BY card_id DESC LIMIT 10",
        (str(target_user.id),),
    ).fetchall()

    card_count = conn.execute(
        "SELECT COUNT(*) as count FROM cards WHERE owner_id = ?",
        (str(target_user.id),),
    ).fetchone()

    user_data = conn.execute(
        "SELECT tokens FROM users WHERE user_id = ?",
        (str(target_user.id),),
    ).fetchone()
    conn.close()

    if card_count["count"] == 0:
        embed = discord.Embed(
            title=f"📦 {target_user.name}'s Inventory",
            description="No cards yet. Use `k!card` to get started!",
            color=discord.Color.blue(),
        )
        await ctx.send(embed=embed)
        return

    rarity_emoji = {
        "common": "⚪",
        "uncommon": "🟢",
        "rare": "🔵",
        "epic": "🟣",
        "legendary": "🟡",
    }

    embed = discord.Embed(
        title=f"📦 {target_user.name}'s Inventory",
        description=f"Total Cards: {card_count['count']} | Tokens: {user_data['tokens']} 🪙",
        color=discord.Color.blue(),
    )

    for card in cards:
        lock_status = "🔒 Locked" if card["locked"] else "🔓 Unlocked"
        embed.add_field(
            name=f"{card['name']} (ID: `{card['card_id']}`)",
            value=f"Category: {card['category'].title()}\nRarity: {rarity_emoji.get(card['rarity'], '')} {card['rarity'].title()}\nValue: {card['value']} 🪙\nStatus: {lock_status}",
            inline=False,
        )

    if card_count["count"] > 10:
        embed.set_footer(text=f"Showing 10 of {card_count['count']} cards. Use k!inv for more details.")

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
        ("k!card [category]", "Get a random card with rarity (anime, cartoon, kpop, kdrama, cdrama, jdrama, manhwa)"),
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
        ("k!trades", "View your pending trades"),
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
    init_db()
    bot.run(TOKEN)
