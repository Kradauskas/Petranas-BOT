import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
import uuid
import secrets
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

last_images = []
last_videos = []

@bot.event
async def on_ready():
    print(f"We are ready to go in, {bot.user.name}")

@bot.command()
async def addpete(ctx):
    if not ctx.message.attachments:
        await ctx.send("<@silent> ❌ Įkelk paveiksliuką kartu su komanda! (.addpete + prisegtas failas)")
        return
    for attachment in ctx.message.attachments:
        if any(attachment.filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif']):
            unique_name = f"{uuid.uuid4().hex}_{attachment.filename}"
            file_path = os.path.join(IMAGE_FOLDER, unique_name)
            await attachment.save(file_path)
            max_size_mb = 10
            if os.path.getsize(file_path) > max_size_mb * 1024 * 1024:
                os.remove(file_path)
                await ctx.send(f"<@silent> ⚠️ Failas per didelis! (maksimalus dydis {max_size_mb} MB)")
                return
            await ctx.send(f"<@silent> ✅ Nuotrauka **{attachment.filename}** pridėta į Petės biblioteką kaip `{unique_name}`!")
        else:
            await ctx.send("<@silent> ⚠️ Šis failas nėra palaikomas (naudok .png, .jpg, .jpeg arba .gif)")

@bot.command()
async def addmp4(ctx):
    if not ctx.message.attachments:
        await ctx.send("<@silent> ❌ Įkelk video failą kartu su komanda! (.addmp4 + prisegtas failas)")
        return
    for attachment in ctx.message.attachments:
        if any(attachment.filename.lower().endswith(ext) for ext in ['.mp4', '.mov', '.gif']):
            unique_name = f"{uuid.uuid4().hex}_{attachment.filename}"
            file_path = os.path.join(VIDEO_FOLDER, unique_name)
            await attachment.save(file_path)
            max_size_mb = 30
            if os.path.getsize(file_path) > max_size_mb * 1024 * 1024:
                os.remove(file_path)
                await ctx.send(f"<@silent> ⚠️ Video failas per didelis! (maksimalus dydis {max_size_mb} MB)")
                return
            await ctx.send(f"<@silent> 🎞️ Video **{attachment.filename}** pridėtas į biblioteką kaip `{unique_name}`!")
        else:
            await ctx.send("<@silent> ⚠️ Šis failas nėra palaikomas (naudok .mp4, .mov arba .gif)")

@bot.command()
@commands.cooldown(1, 5, commands.BucketType.user)
async def pete(ctx):
    global last_images
    images = [f for f in os.listdir(IMAGE_FOLDER) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
    if not images:
        await ctx.send("<@silent> Bibliotekoje nėra jokių Petės nuotraukų 😔")
        return
    available = [img for img in images if img not in last_images] or images
    chosen_image = secrets.choice(available)
    last_images.append(chosen_image)
    if len(last_images) > 3:
        last_images.pop(0)
    image_path = os.path.join(IMAGE_FOLDER, chosen_image)
    resized_path = os.path.join(IMAGE_FOLDER, f"resized_{chosen_image}")
    with Image.open(image_path) as img:
        img = img.resize((500, 500))
        img.save(resized_path)
    await ctx.send(f"<@silent> pasiimk krw {ctx.author.mention}")
    await ctx.send(file=discord.File(resized_path))
    os.remove(resized_path)

@pete.error
async def pete_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"<@silent> 🖕 LIJANA NU AR TU GALI PAKENTET ({error.retry_after:.1f}s)")

@bot.command()
@commands.cooldown(1, 5, commands.BucketType.user)
async def mp4(ctx):
    global last_videos
    videos = [f for f in os.listdir(VIDEO_FOLDER) if f.lower().endswith(('.mp4', '.mov', '.gif'))]
    if not videos:
        await ctx.send("<@silent> 🎞️ Nėra jokių video faile 😔")
        return
    available = [vid for vid in videos if vid not in last_videos] or videos
    chosen_video = secrets.choice(available)
    last_videos.append(chosen_video)
    if len(last_videos) > 3:
        last_videos.pop(0)
    video_path = os.path.join(VIDEO_FOLDER, chosen_video)
    await ctx.send(file=discord.File(video_path))

@mp4.error
async def mp4_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send("<@silent> 🖕 NU PAKENTEK KURWA 🖕")

bot.run(token, log_handler=handler, log_level=logging.DEBUG)
