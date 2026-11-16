import asyncio
import os
import random
import time

import discord
from discord.ext import commands

from .economy import (
    get_user_coins,
    add_user_coins,
    deduct_user_coins,
    get_user_field,
    set_user_field,
    top_users,
)
from .Rolling import (
    roll_specific_rarity,
    RARITY_STYLE,
    create_final_image,
    ROLLS_FOLDER,
    OVERLAYS_FOLDER,
)
from .ui import make_embed, success, error, GOLD, DARK

print(">>> Shop commands loaded")

# ---------------- SHOP DATA (single source of truth) ----------------

SHOP_ITEMS = {
    "random mythic": 100000,
    "random legendary": 10000,
    "random epic": 2500,
    "random rare": 500,
    "random uncommon": 100,
    "random common": 10,
}

DUPLICATE_REFUND = 100
DAILY_AMOUNT = 250
DAILY_STREAK_BONUS = 50      # extra per day of streak
DAILY_STREAK_MAX = 7
DAY = 24 * 3600


def fmt(n: int) -> str:
    return f"{n:,}".replace(",", " ")


# --------------- SETUP FUNCTION ---------------

def setup_shop_commands(bot):

    @bot.command()
    async def shop(ctx):
        embed = make_embed("🛒 Lootbox Shop", "Pirk su `.buy random <rarity>`", DARK)
        for item, price in SHOP_ITEMS.items():
            rarity = item.split()[-1]
            style = RARITY_STYLE.get(rarity, {"emoji": "❓"})
            embed.add_field(name=f"{style['emoji']} {rarity.capitalize()}", value=f"💰 **{fmt(price)}**", inline=True)
        embed.add_field(name="​", value=f"Duplicate = **+{DUPLICATE_REFUND}** coins atgal", inline=False)
        await ctx.send(embed=embed)

    @bot.command(aliases=["bal", "balance"])
    async def coins(ctx, member: discord.Member = None):
        target = member or ctx.author
        amount = get_user_coins(str(target.id))
        embed = make_embed(description=f"💰 **{fmt(amount)}** coinsų", color=GOLD)
        embed.set_author(name=target.display_name, icon_url=target.display_avatar.url)
        await ctx.send(embed=embed)

    @bot.command()
    async def daily(ctx):
        user_id = str(ctx.author.id)
        now = time.time()
        last = get_user_field(user_id, "last_daily", 0)
        streak = get_user_field(user_id, "daily_streak", 0)

        if now - last < DAY:
            ready = int(last + DAY)
            await ctx.send(embed=error("Jau pasiėmei šiandien", f"Kitas daily <t:{ready}:R>"))
            return

        streak = streak + 1 if now - last < 2 * DAY else 1
        reward = DAILY_AMOUNT + DAILY_STREAK_BONUS * (min(streak, DAILY_STREAK_MAX) - 1)

        add_user_coins(user_id, reward)
        set_user_field(user_id, "last_daily", now)
        set_user_field(user_id, "daily_streak", streak)

        fire = "🔥" * min(streak, DAILY_STREAK_MAX)
        embed = make_embed("🎁 Daily!", f"+**{fmt(reward)}** coinsų\nStreak: **{streak}** {fire}", GOLD)
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

    @bot.command(aliases=["leaderboard", "lb"])
    async def top(ctx):
        medals = ["🥇", "🥈", "🥉"]
        lines = []
        for i, (uid, amount) in enumerate(top_users(10)):
            member = ctx.guild.get_member(int(uid)) if ctx.guild else None
            name = member.display_name if member else f"<@{uid}>"
            place = medals[i] if i < 3 else f"`#{i + 1}`"
            lines.append(f"{place} **{name}** — {fmt(amount)} 💰")
        await ctx.send(embed=make_embed("🏆 Turtingiausi", "\n".join(lines) or "Dar niekas neturi coinsų", GOLD))

    @bot.command()
    async def buy(ctx, *, item_name: str):
        user_id = str(ctx.author.id)
        item_name = " ".join(item_name.lower().split())
        if not item_name.startswith("random "):
            item_name = f"random {item_name}"   # allow ".buy rare"

        if item_name not in SHOP_ITEMS:
            await ctx.send(embed=error("Tokios prekės nėra", "Žiūrėk `.shop`"))
            return

        price = SHOP_ITEMS[item_name]
        rarity = item_name.split()[-1]

        if get_user_coins(user_id) < price:
            await ctx.send(embed=error("Nepakanka coinsų", f"Reikia **{fmt(price)}**, turi **{fmt(get_user_coins(user_id))}**"))
            return

        rarity_folder = os.path.join(ROLLS_FOLDER, rarity)
        images = [f for f in os.listdir(rarity_folder) if f.lower().endswith((".png", ".jpg", ".jpeg", ".gif"))] \
            if os.path.isdir(rarity_folder) else []
        if not images:
            await ctx.send(embed=error("Šitas lootboxas tuščias", "Pinigai nenuskaičiuoti."))
            return

        deduct_user_coins(user_id, price)
        style = RARITY_STYLE[rarity]
        msg = await ctx.send(embed=make_embed("🎁 Atidaroma lootbox...", color=style["color"]))

        # Spin animation
        for _ in range(5):
            fake_image = random.choice(images)
            embed = make_embed("🎰 Sukasi...", color=0x444444)
            embed.set_image(url=f"attachment://{fake_image}")
            await msg.edit(embed=embed, attachments=[discord.File(os.path.join(rarity_folder, fake_image), filename=fake_image)])
            await asyncio.sleep(0.4)

        image, duplicate, err = roll_specific_rarity(user_id, rarity)
        if err:
            add_user_coins(user_id, price)  # refund – nothing was given
            await msg.edit(embed=error(err, "Coinsai grąžinti."), attachments=[])
            return

        if duplicate:
            add_user_coins(user_id, DUPLICATE_REFUND)

        source = os.path.join(ROLLS_FOLDER, rarity, image)
        overlay = os.path.join(OVERLAYS_FOLDER, f"{rarity}.png")
        temp_path = f"temp_loot_{ctx.author.id}.png"
        try:
            create_final_image(source, overlay, temp_path)
            embed = make_embed(
                f"🎉 {style['emoji']} {rarity.upper()}!",
                f"Tu gavai **{os.path.splitext(image)[0]}**",
                style["color"],
            )
            if duplicate:
                embed.set_footer(text=f"DUPLICATE • +{DUPLICATE_REFUND} coins")
            embed.set_image(url="attachment://final.png")
            await msg.edit(embed=embed, attachments=[discord.File(temp_path, filename="final.png")])
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    # -------- ADMIN COMMANDS --------

    @bot.command()
    @commands.has_permissions(administrator=True)
    async def givecoins(ctx, member: discord.Member, amount: int):
        add_user_coins(str(member.id), amount)
        await ctx.send(embed=success("Pridėta!", f"{member.mention} gavo **{fmt(amount)}** coinsų"))

    @bot.command()
    @commands.has_permissions(administrator=True)
    async def removecoins(ctx, member: discord.Member, amount: int):
        deduct_user_coins(str(member.id), amount)
        await ctx.send(embed=success("Atimta!", f"Iš {member.mention} atimta **{fmt(amount)}** coinsų"))
