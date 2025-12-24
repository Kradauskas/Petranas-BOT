import discord
from discord.ext import commands
from discord import app_commands
import os
import random
import secrets
import time
import json
import datetime
from PIL import Image, ImageEnhance

from commands.economy import add_user_coins 

ROLLS_FOLDER = "rolls"
OVERLAYS_FOLDER = "overlays"
INVENTORY_FILE = "inventory.json"


# =========================
# INVENTORY SYSTEM
# =========================
def roll_specific_rarity(user_id: str, rarity: str):
    rarity_folder = os.path.join(ROLLS_FOLDER, rarity)

    if not os.path.exists(rarity_folder):
        return None, None, "Rarity folderis nerastas"

    images = [
        f for f in os.listdir(rarity_folder)
        if f.lower().endswith((".png", ".jpg", ".jpeg", ".gif"))
    ]

    if not images:
        return None, None, "Nėra paveikslėlių"

    chosen_image = secrets.choice(images)

    inventory = load_inventory()
    is_duplicate = has_duplicate(
        inventory,
        user_id,
        chosen_image,
        rarity
    )

    if not is_duplicate:
        inventory.setdefault(user_id, []).append({
            "image": chosen_image,
            "rarity": rarity
        })
        save_inventory(inventory)

    return chosen_image, is_duplicate, None

def load_inventory():
    if not os.path.exists(INVENTORY_FILE):
        return {}
    with open(INVENTORY_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            # sugadintas json -> pradedam iš naujo
            return {}

def save_inventory(data):
    with open(INVENTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


# =========================
# RARITY SYSTEM
# =========================

RARITIES = [
    ("common",     50.0),
    ("uncommon",   25.0),
    ("rare",       15.0),
    ("epic",        7.0),
    ("legendary",   2.5),
    ("mythic",      0.5),
]
RARITY_STYLE = {
    "mythic": {
        "emoji": "🌌",
        "color": 0x9b00ff
    },
    "legendary": {
        "emoji": "🔥",
        "color": 0xff9900
    },
    "epic": {
        "emoji": "💜",
        "color": 0x8e44ad
    },
    "rare": {
        "emoji": "💎",
        "color": 0x3498db
    },
    "uncommon": {
        "emoji": "🟢",
        "color": 0x2ecc71
    },
    "common": {
        "emoji": "⚪",
        "color": 0x95a5a6
    }
}

def roll_rarity():
    total = sum(chance for _, chance in RARITIES)
    r = random.uniform(0, total)
    cumulative = 0.0
    for rarity, chance in RARITIES:
        cumulative += chance
        if r <= cumulative:
            return rarity
    return "common"
def get_rarity_chance(rarity: str) -> float:
    for r, chance in RARITIES:
        if r == rarity:
            return chance
    return 0.0


# =========================
# IMAGE: RESIZE + OVERLAY
# =========================

def create_final_image(base_path: str, overlay_path: str, output_path: str, opacity: float = 0.65):
    """Atidaro bazinį paveikslėlį, resize'ina, uždeda overlay (jei yra) ir išsaugo PNG."""
    base = Image.open(base_path).convert("RGBA")
    base = base.resize((500, 500))

    if os.path.exists(overlay_path):
        overlay = Image.open(overlay_path).convert("RGBA")
        overlay = overlay.resize((500, 500))

        if opacity < 1.0:
            alpha = overlay.split()[3]
            alpha = ImageEnhance.Brightness(alpha).enhance(opacity)
            overlay.putalpha(alpha)

        base = Image.alpha_composite(base, overlay)

    base.save(output_path, format="PNG")

def has_duplicate(inventory, user_id, image, rarity):
    return any(
        item["image"] == image and item["rarity"] == rarity
        for item in inventory.get(user_id, [])
    )
# =========================
# COMMANDS
# =========================

def setup_roll_commands(bot: commands.Bot):

    print(">>> Rolling commands loaded")

    # -----------------------------
    # .roll
    # -----------------------------
    @bot.command()
    @commands.cooldown(5, 3600, commands.BucketType.user)
    async def roll(ctx: commands.Context):
        try:
            rarity = roll_rarity()
            style = RARITY_STYLE.get(rarity, {"emoji": "❓", "color": 0xffffff})
            chance = get_rarity_chance(rarity)

            rarity_folder = os.path.join(ROLLS_FOLDER, rarity)

            if not os.path.exists(rarity_folder):
                await ctx.send("❌ Rarity folderis nerastas.", silent=True)
                return

            images = [
                f for f in os.listdir(rarity_folder)
                if f.lower().endswith((".png", ".jpg", ".jpeg", ".gif"))
            ]

            if not images:
                await ctx.send("⚠️ Nėra paveikslėlių.", silent=True)
                return

            chosen_image = secrets.choice(images)
            photo_name = os.path.splitext(chosen_image)[0]

            source_path = os.path.join(rarity_folder, chosen_image)
            overlay_path = os.path.join(OVERLAYS_FOLDER, f"{rarity}.png")
            temp_path = f"temp_roll_{ctx.author.id}_{ctx.message.id}.png"

            create_final_image(source_path, overlay_path, temp_path, opacity=0.65)

            inventory = load_inventory()
            user_id = str(ctx.author.id)

            is_duplicate = has_duplicate(
                inventory,
                user_id,
                chosen_image,
                rarity
            )

            embed = discord.Embed(
                title=f"{style['emoji']} {rarity.upper()} - **`{photo_name}`**",
                color=style["color"]
            )

            embed.set_image(
                url=f"attachment://{os.path.basename(temp_path)}"
            )

            footer_text = f"Drop chance: {chance}%"
            if is_duplicate:
                footer_text += " • DUPLICATE (neįdėta)"

            embed.set_footer(text=footer_text)

            file = discord.File(
                temp_path,
                filename=os.path.basename(temp_path)
            )

            await ctx.send(embed=embed, file=file, silent=True)

        # ➕ Į inventory tik jei NE duplicate
            if not is_duplicate:
                inventory.setdefault(user_id, []).append({
                    "image": chosen_image,
                    "rarity": rarity
                })
                save_inventory(inventory)
            else:
                add_user_coins(user_id, 100)  # refund for duplicate
                embed=discord.Embed(
                    title="💰 Gavai 100 coins už duplicate",
                    color=0xFFFF00
                    )
                await ctx.send(embed=embed, silent=True)

        except Exception as e:
            print("ROLL ERROR:", repr(e))
            await ctx.send(f"❌ Klaida `.roll`: `{e}`", silent=True)

        finally:
            if 'temp_path' in locals() and os.path.exists(temp_path):
                os.remove(temp_path)



    # -----------------------------
    # .inventory
    # -----------------------------
    @bot.command()
    async def inventory(ctx: commands.Context, member: discord.Member | None = None):
        inventory = load_inventory()

    # jei nepaminėjo – naudojam autorių
        target = member or ctx.author
        user_id = str(target.id)

        if user_id not in inventory or len(inventory[user_id]) == 0:
            embed=discord.Embed(
                title="❌ Tuščias inventorius!",
                description=f"{target.mention} nieko neturi...",
                color=0x000000
                )
            await ctx.send(embed=embed)
            return

    # susigrupuoja pagal rarity
        grouped = {}
        for item in inventory[user_id]:
            grouped.setdefault(item["rarity"], []).append(item["image"])

        order = ["mythic", "legendary", "epic", "rare", "uncommon", "common"]

        embed=discord.Embed(
            title=f"🎒 inventorius: ",
            color=0x000000
            )
        
        embed.set_author(
            name=target.display_name,
            icon_url=target.avatar.url if target.avatar else target.default_avatar.url
           )

        for rarity in order:
            if rarity not in grouped:
                continue

            names = [os.path.splitext(img)[0] for img in grouped[rarity]]
            names_str = ", ".join(f"`{n}`" for n in names)

            embed.add_field(
                name=f"{rarity.upper()} ({len(names)})",
                value=names_str,
                inline=False
                )
        await ctx.send(embed=embed)


    # -----------------------------
    # .view <pavadinimas>
    # -----------------------------
    @bot.command()
    async def view(ctx: commands.Context, name: str):
        name = name.lower()

        # ieškom per visus rarity folders
        for rarity, _ in RARITIES:
            folder = os.path.join(ROLLS_FOLDER, rarity)

            # 1) bandome tikslų failo vardą
            exact_path = os.path.join(folder, name)
            if os.path.exists(exact_path):
                await ctx.send(file=discord.File(exact_path), silent=True)
                return

            # 2) bandome su .png/.jpg/.jpeg
            for ext in ("png", "jpg", "jpeg", "gif"):
                candidate = os.path.join(folder, f"{name}.{ext}")
                if os.path.exists(candidate):
                    embed=discord.Embed(
                        title="📸  Peržiūra",
                        color=0x000000
                        )
                    embed.set_image(url=f"attachment://{os.path.basename(candidate)}")
                    await ctx.send(embed=embed, file=discord.File(candidate), silent=True)
                    return
        
        embed=discord.Embed(
            title="❌ Nuotrauka nerasta!",
            description="Patikrink pavadinimą ir bandyk dar kartą.",
            color=0x000000
            )
        await ctx.send(embed=embed)

    # -----------------------------
    # cooldown error
    # -----------------------------
    @roll.error
    async def roll_error(ctx: commands.Context, error):
        if isinstance(error, commands.CommandOnCooldown):
            next_time = int(time.time() + error.retry_after)
            embed = discord.Embed(
                title="COOLDOWN",
                description=f"Galėsi naudoti komandą {discord.utils.format_dt(datetime.datetime.fromtimestamp(next_time), style='R')}",
                color=0x000000
            )
            await ctx.send(embed=embed)


