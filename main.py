#main.py
import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
print("PROJECT ROOT:", os.getcwd())
print("FILES IN PROJECT ROOT:", os.listdir())
print("FILES IN commands/:", os.listdir("commands"))
from commands.MainFunctions import setup_pete_commands
from commands.Rolling import setup_roll_commands

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

setup_pete_commands(bot)
setup_roll_commands(bot)
print(">>> setup_roll_commands CALLED")


@bot.event
async def on_ready():
    print(f"The bot {bot.user.name} is running")

bot.run(token, log_handler=handler, log_level=logging.DEBUG)
