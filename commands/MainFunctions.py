import io
import os
import secrets
import uuid

import discord
from discord.ext import commands
from PIL import Image, ImageOps

from .ui import make_embed, success, error, BRAND, DARK

IMAGE_FOLDER = "images"
VIDEO_FOLDER = "video"

IMAGE_EXTS = ('.png', '.jpg', '.jpeg', '.gif', '.webp')
VIDEO_EXTS = ('.mp4', '.mov', '.gif')

last_images = []
last_videos = []

HELP_PAGES = {
    "🎲 Pramogos": (
        "`.pete` – random Petro nuotrauka\n"
        "`.mp4` – random video\n"
        "`.sw` – sweikhi lohai\n"
        "`.wordle` – 🟩 **Petro Wordle** (atspėk frazę, laimėk coinsų)"
    ),
    "🃏 Kortelės": (
        "`.roll` – traukia random kortelę (5 per valandą)\n"
        "`.inventory [@user]` – kortelių kolekcija\n"
        "`.view <pavadinimas>` – peržiūrėti kortelę"
    ),
    "💰 Ekonomika": (
        "`.coins [@user]` – kiek turi coinsų\n"
        "`.daily` – kasdieniai coinsai\n"
        "`.top` – turtingiausių topas\n"
        "`.shop` / `.buy <prekė>` – lootboxai"
    ),
    "🎰 Gambling": (
        "`.cf <suma>` – Coin Flip (x2)\n"
        "`.dr <suma>` – Dice Roll (x4)\n"
        "`.sm <suma>` – Slot Machine (x10)"
    ),
    "📤 Įkėlimas": (
        "`.addpete` + foto – įkelia nuotrauką\n"
        "`.addmp4` + video – įkelia video"
    ),
}


async def save_attachments(ctx, folder, exts, max_mb, kind, usage):
    if not ctx.message.attachments:
        await ctx.send(embed=error(f"Nėra {kind}", f"Naudok **`{usage}`** ir prisek failą."))
        return

    for attachment in ctx.message.attachments:
        if not attachment.filename.lower().endswith(exts):
            await ctx.send(embed=error("Blogas formatas", f"`{attachment.filename}` – leidžiami: {', '.join(exts)}"))
            continue
        if attachment.size > max_mb * 1024 * 1024:
            await ctx.send(embed=error("Per didelis failas", f"`{attachment.filename}` – max **{max_mb} MB**"))
            continue

        unique_name = f"{uuid.uuid4().hex[:8]}_{attachment.filename}"
        await attachment.save(os.path.join(folder, unique_name))
        await ctx.send(embed=success(f"{kind.capitalize()} įkelta!", f"**{attachment.filename}** pridėta į kolekciją"))


def pick_random(folder, exts, recent):
    files = [f for f in os.listdir(folder) if f.lower().endswith(exts)]
    if not files:
        return None
    available = [f for f in files if f not in recent] or files
    chosen = secrets.choice(available)
    recent.append(chosen)
    del recent[:-min(10, max(1, len(files) // 2))]
    return chosen


def setup_pete_commands(bot):

    @bot.command(aliases=["komandos", "h"])
    async def help(ctx):
        embed = make_embed(
            "⚙️ Petranas BOT – komandos",
            "Prefiksas: **`.`**   •   🆕 **Naujiena:** `.wordle` ir `.daily`!",
            BRAND,
        )
        if bot.user:
            embed.set_thumbnail(url=bot.user.display_avatar.url)
        for name, value in HELP_PAGES.items():
            embed.add_field(name=name, value=value, inline=False)
        await ctx.send(embed=embed)

    @bot.command()
    async def sw(ctx):
        await ctx.send("sweikhi lohai as grizhau")

    @bot.command()
    async def addpete(ctx):
        await save_attachments(ctx, IMAGE_FOLDER, IMAGE_EXTS, 10, "nuotrauka", ".addpete + foto")

    @bot.command()
    async def addmp4(ctx):
        await save_attachments(ctx, VIDEO_FOLDER, VIDEO_EXTS, 25, "video", ".addmp4 + video")

    @bot.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def pete(ctx):
        chosen = pick_random(IMAGE_FOLDER, IMAGE_EXTS, last_images)
        if not chosen:
            await ctx.send(embed=error("Nėra nuotraukų", "Įkelk su `.addpete`"))
            return

        path = os.path.join(IMAGE_FOLDER, chosen)
        if chosen.lower().endswith(".gif"):
            file = discord.File(path, filename="pete.gif")
        else:
            # Crop to a square instead of stretching, render in memory (no temp files)
            with Image.open(path) as img:
                img = ImageOps.exif_transpose(img).convert("RGB")
                img = ImageOps.fit(img, (512, 512), Image.LANCZOS)
                buf = io.BytesIO()
                img.save(buf, "JPEG", quality=90)
                buf.seek(0)
            file = discord.File(buf, filename="pete.jpg")

        embed = make_embed("📸 pasiimk krw", color=DARK)
        embed.set_image(url=f"attachment://{file.filename}")
        await ctx.send(embed=embed, file=file, silent=True)

    @bot.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def mp4(ctx):
        chosen = pick_random(VIDEO_FOLDER, VIDEO_EXTS, last_videos)
        if not chosen:
            await ctx.send(embed=error("Nėra video", "Įkelk su `.addmp4`"))
            return
        try:
            await ctx.send(file=discord.File(os.path.join(VIDEO_FOLDER, chosen)), silent=True)
        except discord.HTTPException as e:
            if e.status == 413:
                await ctx.send(embed=error("Video per didelis Discordui", f"`{chosen}`"))
            else:
                raise
