"""Shared look & feel for all bot messages."""
import os

import discord
from discord.ext import commands

# Brand colors
BRAND = 0x5865F2
SUCCESS = 0x2ECC71
ERROR = 0xE74C3C
WARNING = 0xF1C40F
GOLD = 0xF5B700
DARK = 0x2B2D31

FOOTER = "Petranas BOT • .help"


def make_embed(title: str = None, description: str = None, color: int = BRAND, *, footer: bool = True) -> discord.Embed:
    embed = discord.Embed(title=title, description=description, color=color)
    if footer:
        embed.set_footer(text=FOOTER)
    return embed


def success(title: str, description: str = None) -> discord.Embed:
    return make_embed(f"✅ {title}", description, SUCCESS)


def error(title: str, description: str = None) -> discord.Embed:
    return make_embed(f"❌ {title}", description, ERROR)


def warning(title: str, description: str = None) -> discord.Embed:
    return make_embed(f"⚠️ {title}", description, WARNING)


def avatar_url(user: discord.abc.User) -> str:
    return user.display_avatar.url


# -------- owner check --------

def _extra_owner_ids() -> set[int]:
    raw = os.getenv("OWNER_IDS", "")
    return {int(x) for x in raw.replace(" ", "").split(",") if x.isdigit()}


async def is_bot_owner(bot: commands.Bot, user: discord.abc.User) -> bool:
    if user.id in _extra_owner_ids():
        return True
    return await bot.is_owner(user)


def owner_only():
    async def predicate(ctx: commands.Context) -> bool:
        if await is_bot_owner(ctx.bot, ctx.author):
            return True
        raise commands.NotOwner()
    return commands.check(predicate)
