import discord
from discord.ext import commands
from discord import ThumbnailComponent, app_commands
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
        embed = discord.Embed(
            title="  **⚙️KOMANDŲ LISTAS⚙️**\n\n**NAUJA:**", 
            description="**• `.roll` **- traukia random kortelę\n• **`.view`** imageName - leidžia peržiūrėti nuotraukas\n**• `.inventory`username** (blank if your own inventory) - parodo kurias korteles turi",
            color=0x000000
            )
        embed.add_field(
            name="PAGRINDINĖS KOMANDOS:",
            value=(
                "• `.mp4` – random video\n"
                "• `.pete` – random nuotrauka"
                ),
            inline=False
            )
        embed.add_field(
            name="PRIDĖJIMO KOMANDOS:",
            value=(
                "• `.addmp4` + video – įkelia video į kolekciją\n"
                "• `.addpete` + foto – įkelia nuotrauką į kolekciją\n"
                ),
            inline=False
            )
        await ctx.send(embed=embed)



    @bot.command()
    async def addpete(ctx):
        if not ctx.message.attachments:
            embed=discord.Embed(
                title="❌ Klaida įkeliant fotkę!",
                description="Naudokite formatą **`.addpete` +foto**",
                color=0x000000
                )
            await ctx.send(embed=embed)
            return
        for attachment in ctx.message.attachments:
            if any(attachment.filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif']):
                unique_name = f"{uuid.uuid4().hex}_{attachment.filename}"
                file_path = os.path.join(IMAGE_FOLDER, unique_name)
                await attachment.save(file_path)

                max_size_mb = 10
                if os.path.getsize(file_path) > max_size_mb * 1024 * 1024:
                    os.remove(file_path)
                    embed=discord.Embed(
                        title="❌ Klaida įkeliant fotkę!",
                        description=f"perdidelis failas (maksimalus dydis {max_size_mb} MB)",
                        color=0x000000
                        )
                    await ctx.send(embed=embed)
                    return
                embed=discord.Embed(
                    title="✅ Fotkė įkelta sėkmingai!",
                    description=f"Fotkė **{attachment.filename}** įkelta kaip `{unique_name}`!",
                    color=0x000000
                    )
                await ctx.send(embed=embed)
            else:
                embed=discord.Embed(
                    title="❌ Klaida įkeliant fotkę!",
                    description="Blogas formatas! Naudokite .png, .jpg, .jpeg, arba .gif",
                    color=0x000000
                    )
                await ctx.send(embed=embed)

    @bot.command()
    async def addmp4(ctx):
        if not ctx.message.attachments:
            embed=discord.Embed(
                title="❌ Klaida įkeliant fotkę!",
                description="Naudokite formatą **`.addpete` +foto**",
                color=0xff0000
                )
            await ctx.send(embed=embed)
            return
        for attachment in ctx.message.attachments:
            if any(attachment.filename.lower().endswith(ext) for ext in ['.mp4', '.mov', '.gif']):
                unique_name = f"{uuid.uuid4().hex}_{attachment.filename}"
                file_path = os.path.join(VIDEO_FOLDER, unique_name)
                await attachment.save(file_path)

                max_size_mb = 30
                if os.path.getsize(file_path) > max_size_mb * 1024 * 1024:
                    os.remove(file_path)
                    embed=discord.Embed(
                        title="❌ Klaida įkeliant video!",
                        description=f"perdidelis failas (maksimalus dydis {max_size_mb} MB)",
                        color=0xff0000
                        )
                    await ctx.send(embed=embed)
                    return

                embed=discord.Embed(
                    title="✅ Video įkeltas sėkmingai!",
                    description=f"Video **{attachment.filename}** įkeltas kaip `{unique_name}`!",
                    color=0x00ff00
                    )
                await ctx.send(embed=embed)
            else:
                embed=discord.Embed(
                    title="❌ Klaida įkeliant video!",
                    description="Blogas formatas! Naudokite .mp4, .mov, arba .gif",
                    color=0xff0000
                    )
                await ctx.send(embed=embed)



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

        embed=discord.Embed(
            title="📸  pasiimk krw",
            color=0x000000
            )
        embed.set_image(url=f"attachment://{os.path.basename(resized_path)}")
        file=discord.File(resized_path, filename=os.path.basename(resized_path))
        await ctx.send(embed=embed, file=file, silent=True)
        os.remove(resized_path)
    @pete.error
    async def pete_error(ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            embed=discord.Embed(
                title="COOLDOWN",
                description=f"galesi naudoti komanda po {error.retry_after:.1f} sekundziu",
                color=0x000000
                )
            await ctx.send(embed=embed)

    @bot.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def mp4(ctx):
        global last_videos
        videos = [f for f in os.listdir(VIDEO_FOLDER) if f.lower().endswith(('.mp4', '.mov', '.gif'))]

        if not videos:
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
            embed=discord.Embed(
                title="COOLDOWN",
                description=f"galesi naudoti komanda po {error.retry_after:.1f} sekundziu",
                color=0x000000
                )
            await ctx.send(embed=embed)

