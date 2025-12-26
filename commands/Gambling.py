import discord
from discord.ext import commands
import random
import asyncio

from .economy import (
    get_user_coins,
    add_user_coins,
    deduct_user_coins
)

print(">>> Gambling commands loaded")

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
            color=0x000000
        )
        await ctx.send(embed=embed)

    async def play_gamble(ctx, game_key: str, amount: int):
        user_id = str(ctx.author.id)
        game = GAMBLING_OPTIONS[game_key]

        if amount <= 0:
            await ctx.send("❌ Statymas turi būti didesnis nei 0.")
            return

        user_coins = get_user_coins(user_id)
        if amount > user_coins:
            await ctx.send(f"❌ Neturi pakankamai monetų. Turi: {user_coins}")
            return

        deduct_user_coins(user_id, amount)

        msg = await ctx.send(
            embed=discord.Embed(
                title=f"{game['emoji']} {game['name']}",
                description="🎲 Sukama...",
                color=0x000000
            )
        )

        for dots in ["🎲.", "🎲..", "🎲..."]:
            await asyncio.sleep(0.6)
            await msg.edit(
                embed=discord.Embed(
                    title=f"{game['emoji']} {game['name']}",
                    description=dots,
                    color=0x000000
                )
            )

        if random.random() < game["chance"]:
            winnings = amount * game["multiplier"]
            add_user_coins(user_id, winnings)
            result = discord.Embed(
                title=f"{game['emoji']} {game['name']} – Rezultatas",
                description=f"🎉 **LAIMĖJAI**\nLaimėjai **{winnings}** coins",
                color=0x00ff00
            )
            color = 0x00ff00
        else:
            result = discord.Embed(
                title=f"{game['emoji']} {game['name']} – Rezultatas",
                description=f"😞 **PRALAIMĖJAI**\nPraradai **{amount}** coins",
                color=0xff0000
            )
            color = 0xff0000

        await msg.edit(embed=result)

    @bot.command()
    async def cf(ctx, amount: int):
        await play_gamble(ctx, "cf", amount)

    @bot.command()
    async def dr(ctx, amount: int):
        await play_gamble(ctx, "dr", amount)

    @bot.command()
    async def sm(ctx, amount: int):
        await play_gamble(ctx, "sm", amount)
