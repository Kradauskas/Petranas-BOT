import discord
from discord.ext import commands
import os
import random
import secrets
import time
import json
from PIL import Image, ImageEnhance

ROLLS_FOLDER = "rolls"
OVERLAYS_FOLDER = "overlays"
INVENTORY_FILE = "inventory.json"


# =========================
# INVENTORY SYSTEM
# =========================

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

def roll_rarity():
    total = sum(chance for _, chance in RARITIES)
    r = random.uniform(0, total)
    cumulative = 0.0
    for rarity, chance in RARITIES:
        cumulative += chance
        if r <= cumulative:
            return rarity
    return "common"


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
            rarity_folder = os.path.join(ROLLS_FOLDER, rarity)

            if not os.path.exists(rarity_folder):
                await ctx.send(f"❌ Nerastas folderis `{rarity_folder}`.", silent=True)
                return

            # surenkam visus paveiksliukus šitam rarity
            images = [
                f for f in os.listdir(rarity_folder)
                if f.lower().endswith((".png", ".jpg", ".jpeg", ".gif"))
            ]

            if not images:
                await ctx.send(f"⚠️ `{rarity}` rarity neturi jokių paveiksliukų.", silent=True)
                return

            chosen_image = secrets.choice(images)
            photo_name = os.path.splitext(chosen_image)[0]

            source_path = os.path.join(rarity_folder, chosen_image)
            overlay_path = os.path.join(OVERLAYS_FOLDER, f"{rarity}.png")

            # laikinas failas – unikalus kiekvienai žinutei
            temp_path = f"temp_roll_{ctx.author.id}_{ctx.message.id}.png"

            # resize + overlay
            create_final_image(source_path, overlay_path, temp_path, opacity=0.65)

            # išsiunčiam rezultatą
            await ctx.send(
                f"🎲 **{rarity.upper()}** – **{photo_name}**!",
                silent=True
            )
            await ctx.send(file=discord.File(temp_path), silent=True)

            # atnaujinam inventory
            inventory = load_inventory()
            user_id = str(ctx.author.id)

            if user_id not in inventory:
                inventory[user_id] = []

            inventory[user_id].append({
                "image": chosen_image,
                "rarity": rarity
            })

            save_inventory(inventory)

        except Exception as e:
            # jeigu kas nors nulūžta – bent pamatysi klaidą ir nebus tylos
            print("ROLL ERROR:", repr(e))
            await ctx.send(f"❌ Įvyko klaida `.roll` komandoje: `{e}`", silent=True)
        finally:
            # išvalom laikiną failą, jei jis dar yra
            if 'temp_path' in locals() and os.path.exists(temp_path):
                os.remove(temp_path)

    # -----------------------------
    # .inventory
    # -----------------------------
    @bot.command()
    async def inventory(ctx: commands.Context):
        inventory = load_inventory()
        user_id = str(ctx.author.id)

        if user_id not in inventory or len(inventory[user_id]) == 0:
            await ctx.send("Nieko neturi...", silent=True)
            return

        # susigrupuoja pagal rarity
        grouped = {}
        for item in inventory[user_id]:
            grouped.setdefault(item["rarity"], []).append(item["image"])

        order = ["mythic", "legendary", "epic", "rare", "uncommon", "common"]

        msg = f"**{ctx.author.mention} inventory:**\n\n"

        for rarity in order:
            if rarity not in grouped:
                continue

            names = [os.path.splitext(img)[0] for img in grouped[rarity]]
            names_str = ", ".join(f"`{n}`" for n in names)

            msg += f"**{rarity.upper()}** ({len(names)}):\n{names_str}\n\n"

        await ctx.send(msg, silent=True)

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
                    await ctx.send(file=discord.File(candidate), silent=True)
                    return

        await ctx.send("Tokios nuotraukos nėra.. (check name)", silent=True)

    # -----------------------------
    # cooldown error
    # -----------------------------
    @roll.error
    async def roll_error(ctx: commands.Context, error):
        if isinstance(error, commands.CommandOnCooldown):
            next_time = int(time.time() + error.retry_after)
            await ctx.send(
                f"⏳ `.roll` galėsi naudoti <t:{next_time}:R>.",
                silent=True
            )
