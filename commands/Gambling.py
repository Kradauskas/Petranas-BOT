import discord
from discord.ext import commands
import random
import asyncio

from .economy import (
    get_user_coins,
    add_user_coins,
    deduct_user_coins
)

from .ui import make_embed, error, SUCCESS, ERROR, DARK

print(">>> Gambling commands loaded")

SLOT_SYMBOLS = ["🍒", "🍋", "🍇", "🔔", "💎", "7️⃣"]
DICE = ["⚀", "⚁", "⚂", "⚃", "⚄", "⚅"]


def spin_frame(game_key: str, won):
    """Visual for the game. won=None -> random 'spinning' frame."""
    if game_key == "cf":
        if won is None:
            return "# 🪙"
        return "# 🟡 HERBAS" if won else "# ⚪ SKAIČIUS"
    if game_key == "dr":
        if won is None:
            return f"# {random.choice(DICE)} {random.choice(DICE)}"
        # Win = double 6 look; loss = anything else
        if won:
            return "# ⚅ ⚅"
        a, b = random.choice(DICE), random.choice(DICE[:5])
        return f"# {a} {b}"
    # slots
    if won is None:
        return "# " + " | ".join(random.choice(SLOT_SYMBOLS) for _ in range(3))
    if won:
        s = random.choice(SLOT_SYMBOLS)
        return f"# {s} | {s} | {s}"
    while True:
        reel = [random.choice(SLOT_SYMBOLS) for _ in range(3)]
        if len(set(reel)) > 1:
            return "# " + " | ".join(reel)

# ---------------- GAMBLING DATA ----------------
GAMBLING_OPTIONS = {
    "cf": {
        "name": "Coin Flip",
        "chance": 0.5,
        "multiplier": 2,
        "emoji": "🪙"
    },
    "dr": {
        "name": "Dice Roll",
        "chance": 0.20,
        "multiplier": 4,
        "emoji": "🎲"
    },
    "sm": {
        "name": "Slot Machine",
        "chance": 0.08,
        "multiplier": 10,
        "emoji": "🎰"
    }
}

# --------------- SETUP FUNCTION ---------------
def setup_gambling_commands(bot):

    @bot.command()
    async def gamble(ctx):
        embed = discord.Embed(
            title="🎰 Gambling",
            description=(
                "**Pasirink žaidimą:**\n\n"
                "🪙 **.cf <amount>** – Coin Flip (x2)\n"
                "🎲 **.dr <amount>** – Dice Roll (x4)\n"
                "🎰 **.sm <amount>** – Slot Machine (x10)"
            ),
            color=DARK
        )
        embed.set_footer(text="Galima statyti ir visus: .cf all")
        await ctx.send(embed=embed)

    async def play_gamble(ctx, game_key: str, amount_raw: str):
        user_id = str(ctx.author.id)
        game = GAMBLING_OPTIONS[game_key]
        user_coins = get_user_coins(user_id)

        if amount_raw.lower() in ("all", "viska", "visus"):
            amount = user_coins
        elif amount_raw.isdigit():
            amount = int(amount_raw)
        else:
            await ctx.send(embed=error("Blogas statymas", f"Naudojimas: `.{game_key} <suma>` arba `.{game_key} all`"))
            return

        if amount <= 0:
            await ctx.send(embed=error("Statymas turi būti didesnis nei 0"))
            return
        if amount > user_coins:
            await ctx.send(embed=error("Nepakanka coinsų", f"Turi **{user_coins}**"))
            return

        deduct_user_coins(user_id, amount)
        won = random.random() < game["chance"]

        title = f"{game['emoji']} {game['name']} • statymas {amount}"
        msg = await ctx.send(embed=make_embed(title, spin_frame(game_key, None), DARK))
        for _ in range(3):
            await asyncio.sleep(0.6)
            await msg.edit(embed=make_embed(title, spin_frame(game_key, None), DARK))
        await asyncio.sleep(0.6)

        if won:
            winnings = amount * game["multiplier"]
            add_user_coins(user_id, winnings)
            text = f"{spin_frame(game_key, True)}\n\n🎉 **LAIMĖJAI {winnings} coinsų!**"
            color = SUCCESS
        else:
            text = f"{spin_frame(game_key, False)}\n\n😞 **Praradai {amount} coinsų**"
            color = ERROR

        embed = make_embed(title, text, color)
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
        embed.set_footer(text=f"Balansas: {get_user_coins(user_id)} 💰")
        await msg.edit(embed=embed)

    @bot.command()
    async def cf(ctx, amount: str):
        await play_gamble(ctx, "cf", amount)

    @bot.command()
    async def dr(ctx, amount: str):
        await play_gamble(ctx, "dr", amount)

    @bot.command()
    async def sm(ctx, amount: str):
        await play_gamble(ctx, "sm", amount)
