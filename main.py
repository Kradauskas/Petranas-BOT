import discord
from discord.ext import commands
from discord import app_commands
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

bot = commands.Bot(command_prefix='.', intents=intents, help_command=None)

IMAGE_FOLDER = "images"
VIDEO_FOLDER = "video"

os.makedirs(IMAGE_FOLDER, exist_ok=True)
os.makedirs(VIDEO_FOLDER, exist_ok=True)

last_images = []
last_videos = []

from commands.Rolling import setup_roll_commands
from commands.MainFunctions import setup_pete_commands
from commands.CoinFunctions import setup_shop_commands
from commands.Gambling import setup_gambling_commands

setup_roll_commands(bot)
setup_pete_commands(bot)
setup_shop_commands(bot)
setup_gambling_commands(bot)

@bot.event
async def on_ready():
    print(f"We are ready to go in, {bot.user.name}")

bot.run(token, log_handler=handler, log_level=logging.DEBUG)
