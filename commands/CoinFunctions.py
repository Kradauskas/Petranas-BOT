import discord
from discord.ext import commands
import random
import asyncio
import os

from .economy import (
    get_user_coins,
    add_user_coins,
    deduct_user_coins,
    add_item_to_inventory
)

from .Rolling import(
    roll_specific_rarity,
    RARITY_STYLE,
    create_final_image,
    ROLLS_FOLDER,
    OVERLAYS_FOLDER
 )


print(">>> Shop commands loaded")
# ---------------- SHOP DATA ----------------

SHOP_ITEMS = {
    "random mythic": 100000,
    "random epic": 2500,
    "random legendary": 1000,
    "random rare": 500,
    "random uncommon": 100,
    "random common": 10
}

ITEM_POOL = {
    "mythic": ["🔥 Dragon", "🌌 God Blade"],
    "epic": ["⚡ Thunder Sword", "🧿 Magic Eye"],
    "legendary": ["👑 Crown", "🗡️ Excalibur"],
    "rare": ["🏹 Bow", "🛡️ Shield"],
    "uncommon": ["🔮 Orb", "📜 Scroll"],
    "common": ["🍎 Apple", "🪨 Stone"]
}

def get_random_item_by_rarity(rarity):
    return random.choice(ITEM_POOL[rarity])

def get_fake_roll_image(rarity: str):
    folder = os.path.join(ROLLS_FOLDER, rarity)
    images = [
        f for f in os.listdir(folder)
        if f.lower().endswith((".png", ".jpg", ".jpeg", ".gif"))
    ]
    return random.choice(images)



# --------------- SETUP FUNCTION ---------------

def setup_shop_commands(bot):

    @bot.command()
    async def shop(ctx):
        desc = ""
        for item, price in SHOP_ITEMS.items():
            desc += f"• **{item}** — {price} coins\n"

        embed = discord.Embed(
            title="🛒 SHOP",
            description=desc,
            color=0x000000
        )
        await ctx.send(embed=embed)

    @bot.command()
    async def coins(ctx):
        user_id = str(ctx.author.id)
        coins = get_user_coins(user_id)

        await ctx.send(embed=discord.Embed(
            title="💰 Coins",
            description=f"Tu turi **{coins} coinsų**",
            color=discord.Color.gold()
        ))

    @bot.command()
    async def buy(ctx, *, item_name: str):
        user_id = str(ctx.author.id)
        item_name = item_name.lower()

        PRICE_LIST = {
            "random mythic": 100000,
            "random legendary": 1000,
            "random epic": 2500,
            "random rare": 500,
            "random uncommon": 100,
            "random common": 10
        }

        if item_name not in PRICE_LIST:
            await ctx.send("❌ Tokios prekės nėra.")
            return

        price = PRICE_LIST[item_name]
        rarity = item_name.split()[-1]

        # 💰 coins check
        if get_user_coins(user_id) < price:
            await ctx.send("❌ Nepakanka coinsų.")
            return

        deduct_user_coins(user_id, price)

        # 🎁 start lootbox
        msg = await ctx.send("🎁 Atidaroma lootbox...")

        rarity_folder = os.path.join(ROLLS_FOLDER, rarity)
        images = [
            f for f in os.listdir(rarity_folder)
            if f.lower().endswith((".png", ".jpg", ".jpeg", ".gif"))
        ]

        # 🔄 FAKE SUKIMAS (vizualas)
        for _ in range(6):
            fake_image = random.choice(images)

            embed = discord.Embed(
                title="🎰 Sukasi...",
                color=0x444444
            )

            file = discord.File(
                os.path.join(rarity_folder, fake_image),
                filename=fake_image
            )

            embed.set_image(url=f"attachment://{fake_image}")

            await msg.edit(embed=embed, attachments=[file])
            await asyncio.sleep(0.4)

        # 🎯 TIKRAS DROP
        image, duplicate, error = roll_specific_rarity(user_id, rarity)
        if duplicate:
            add_user_coins(user_id, 100)
     # refund for duplicate
        

        if error:
            await msg.edit(content=f"❌ {error}")
            return

        # 🖼️ FINAL IMAGE
        source = os.path.join(ROLLS_FOLDER, rarity, image)
        overlay = os.path.join(OVERLAYS_FOLDER, f"{rarity}.png")
        temp_path = f"temp_loot_{ctx.author.id}.png"

        create_final_image(source, overlay, temp_path)

        style = RARITY_STYLE[rarity]
        name = os.path.splitext(image)[0]

        embed = discord.Embed(
            title=f"🎉 {style['emoji']} {rarity.upper()}!",
            description=f"Tu gavai **{name}**",
            color=style["color"]
        )

        if duplicate:
            embed.set_footer(text="DUPLICATE")

        file = discord.File(temp_path, filename="final.png")
        embed.set_image(url="attachment://final.png")

        await msg.edit(embed=embed, attachments=[file])

        os.remove(temp_path)
    # -------- ADMIN COMMANDS --------

    @bot.command()
    @commands.has_permissions(administrator=True)
    async def givecoins(ctx, member: discord.Member, amount: int):
        add_user_coins(str(member.id), amount)
        embed=discord.Embed(
            title="✅ Sėkmingai pridėta!",
            description=f"{member.mention} gavo {amount} coinsų",
            color=0x00ff00
            )
        await ctx.send(embed=embed)

    @bot.command()
    @commands.has_permissions(administrator=True)
    async def removecoins(ctx, member: discord.Member, amount: int):
        deduct_user_coins(str(member.id), amount)
        embed=discord.Embed(
            title="✅ Sėkmingai atimta!",
            description=f"Iš {member.mention} atimta {amount} coinsų",
            color=0x00ff00
            )
        await ctx.send(embed=embed)

    @givecoins.error
    async def givecoins_error(ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("❌ Naudojimas: .givecoins @user kiekis")
        else:
            await ctx.send(f"❌ Klaida: {error}")

    @buy.error
    async def buy_error(ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("❌ Naudojimas: .buy random common")
        else:
            await ctx.send(f"❌ Klaida: {error}")
