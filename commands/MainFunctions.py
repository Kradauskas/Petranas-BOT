import discord
from discord.ext import commands
import os
import uuid
import secrets
from PIL import Image

IMAGE_FOLDER = "images"
VIDEO_FOLDER = "video"

last_images = []
last_videos = []


def setup_pete_commands(bot):

    @bot.command()
    async def help(ctx):
        await ctx.send("**Komandų listas:**\n\n\n**NAUJA:**\n**.roll** (Random petes korteles issukimas, galima paziureti turimus su **.inventory** ir **.view (nuotraukos pavadinimas)**\n\n\n**.addpete** (prideti nuotrauka i aplanka)\n**.addmp4** (prideti video i aplanka)\n**.mp4** (issiuncia random video)\n**.pete** (atsiuncia random fotke)")

    @bot.command()
    async def addpete(ctx):
        if not ctx.message.attachments:
            await ctx.send(".addpete +foto)")
            return
        for attachment in ctx.message.attachments:
            if any(attachment.filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif']):
                unique_name = f"{uuid.uuid4().hex}_{attachment.filename}"
                file_path = os.path.join(IMAGE_FOLDER, unique_name)
                await attachment.save(file_path)

                max_size_mb = 10
                if os.path.getsize(file_path) > max_size_mb * 1024 * 1024:
                    os.remove(file_path)
                    await ctx.send(f"perdidelis failas (maksimalus dydis {max_size_mb} MB)")
                    return

                await ctx.send(f"Fotkė **{attachment.filename}** įkelta kaip `{unique_name}`!")
            else:
                await ctx.send("Blogas formatas")

    @bot.command()
    async def addmp4(ctx):
        if not ctx.message.attachments:
            await ctx.send(".addmp4 +video")
            return
        for attachment in ctx.message.attachments:
            if any(attachment.filename.lower().endswith(ext) for ext in ['.mp4', '.mov', '.gif']):
                unique_name = f"{uuid.uuid4().hex}_{attachment.filename}"
                file_path = os.path.join(VIDEO_FOLDER, unique_name)
                await attachment.save(file_path)

                max_size_mb = 30
                if os.path.getsize(file_path) > max_size_mb * 1024 * 1024:
                    os.remove(file_path)
                    await ctx.send(f"perdidelis failas (maksimalus dydis {max_size_mb} MB)")
                    return

                await ctx.send(f"Vidosas **{attachment.filename}** įkeltas kaip `{unique_name}`!")
            else:
                await ctx.send("Blogas formatas")

    @bot.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def pete(ctx):
        global last_images
        images = [f for f in os.listdir(IMAGE_FOLDER) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]

        if not images:
            await ctx.send("Nera fotkiu")
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

        await ctx.send(f"pasiimk krw", silent=True)
        await ctx.send(file=discord.File(resized_path), silent=True)
        os.remove(resized_path)

    @pete.error
    async def pete_error(ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"<🖕 LIJANA NU AR TU GALI PAKENTET ({error.retry_after:.1f}s)", silent=True)

    @bot.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def mp4(ctx):
        global last_videos
        videos = [f for f in os.listdir(VIDEO_FOLDER) if f.lower().endswith(('.mp4', '.mov', '.gif'))]

        if not videos:
            await ctx.send("<🎞️ Nėra jokių video faile 😔")
            return

        available = [vid for vid in videos if vid not in last_videos] or videos
        chosen_video = secrets.choice(available)

        last_videos.append(chosen_video)
        if len(last_videos) > 3:
            last_videos.pop(0)

        video_path = os.path.join(VIDEO_FOLDER, chosen_video)
        await ctx.send(file=discord.File(video_path), silent=True)

    @mp4.error
    async def mp4_error(ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send("🖕 NU PAKENTEK KURWA 🖕", silent=True)
