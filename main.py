import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
import random
from PIL import Image

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='.', intents=intents)

IMAGE_FOLDER = "images"
VIDEO_FOLDER = "video"

os.makedirs(IMAGE_FOLDER, exist_ok=True)
os.makedirs(VIDEO_FOLDER, exist_ok=True)

@bot.event
async def on_ready():
    print(f"We are ready to go in, {bot.user.name}")

# -------------------------------
# .addpete – leidžia įkelti naują nuotrauką
# -------------------------------
@bot.command()
async def addpete(ctx):
    if not ctx.message.attachments:
        await ctx.send("❌ Įkelk paveiksliuką kartu su komanda! (.addpete + prisegtas failas)")
        return

    for attachment in ctx.message.attachments:
        if any(attachment.filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif']):
            file_path = os.path.join(IMAGE_FOLDER, attachment.filename)
            await attachment.save(file_path)
            await ctx.send(f"✅ Nuotrauka **{attachment.filename}** pridėta į Petės biblioteką!")
        else:
            await ctx.send("⚠️ Šis failas nėra palaikomas (naudok .png, .jpg, .jpeg arba .gif)")

# -------------------------------
# .addmp4 – leidžia įkelti video failą
# -------------------------------
@bot.command()
async def addmp4(ctx):
    if not ctx.message.attachments:
        await ctx.send("❌ Įkelk video failą kartu su komanda! (.addmp4 + prisegtas failas)")
        return

    for attachment in ctx.message.attachments:
        if any(attachment.filename.lower().endswith(ext) for ext in ['.mp4', '.mov', '.gif']):
            file_path = os.path.join(VIDEO_FOLDER, attachment.filename)
            await attachment.save(file_path)
            await ctx.send(f"🎞️ Video **{attachment.filename}** pridėtas į biblioteką!")
        else:
            await ctx.send("⚠️ Šis failas nėra palaikomas (naudok .mp4, .mov arba .gif)")

# -------------------------------
# Esamos .pete ir .mp4 komandos
# -------------------------------
@bot.command()
@commands.cooldown(1, 5, commands.BucketType.user)
async def pete(ctx):
    images = [f for f in os.listdir(IMAGE_FOLDER) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
    if not images:
        await ctx.send("Bibliotekoje nėra jokių Petės nuotraukų 😔")
        return

    chosen_image = random.choice(images)
    image_path = os.path.join(IMAGE_FOLDER, chosen_image)

    resized_path = os.path.join(IMAGE_FOLDER, f"resized_{chosen_image}")
    with Image.open(image_path) as img:
        img = img.resize((500, 500))
        img.save(resized_path)

    await ctx.send(f"pasiimk krw {ctx.author.mention}")
    await ctx.send(file=discord.File(resized_path))
    os.remove(resized_path)

@pete.error
async def pete_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"🖕 LIJANA NU AR TU GALI PAKENTET ({error.retry_after:.1f}s)")

@bot.command()
@commands.cooldown(1, 5, commands.BucketType.user)
async def mp4(ctx):
    videos = [f for f in os.listdir(VIDEO_FOLDER) if f.lower().endswith(('.mp4', '.mov', '.gif'))]
    if not videos:
        await ctx.send("🎞️ Nėra jokių video faile 😔")
        return

    chosen_video = random.choice(videos)
    video_path = os.path.join(VIDEO_FOLDER, chosen_video)
    await ctx.send(file=discord.File(video_path))

@mp4.error
async def mp4_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send("🖕 NU PAKENTEK KURWA 🖕")

bot.run(token, log_handler=handler, log_level=logging.DEBUG)
