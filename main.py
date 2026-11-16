import datetime
import logging
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
token = (os.getenv('DISCORD_TOKEN') or '').strip().strip('"').strip("'")
if not token:
    raise SystemExit("DISCORD_TOKEN is missing. Create a .env file next to main.py with: DISCORD_TOKEN=your_token")

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(
    command_prefix='.',
    intents=intents,
    help_command=None,
    case_insensitive=True,
    activity=discord.Game(name=".help | .wordle"),
)

os.makedirs("images", exist_ok=True)
os.makedirs("video", exist_ok=True)

from commands.ui import error as error_embed
from commands.Rolling import setup_roll_commands
from commands.MainFunctions import setup_pete_commands
from commands.CoinFunctions import setup_shop_commands
from commands.Gambling import setup_gambling_commands
from commands.Wordle import setup_wordle_commands
from commands.Owner import setup_owner_commands

setup_roll_commands(bot)
setup_pete_commands(bot)
setup_shop_commands(bot)
setup_gambling_commands(bot)
setup_wordle_commands(bot)
setup_owner_commands(bot)


@bot.event
async def on_ready():
    print(f"We are ready to go in, {bot.user.name} ({len(bot.guilds)} serveriai)")


@bot.event
async def on_command_error(ctx: commands.Context, err: commands.CommandError):
    err = getattr(err, "original", err)

    if isinstance(err, commands.CommandNotFound):
        return
    if isinstance(err, commands.CommandOnCooldown):
        when = discord.utils.utcnow() + datetime.timedelta(seconds=err.retry_after)
        await ctx.send(embed=error_embed("Cooldown", f"Galėsi vėl {discord.utils.format_dt(when, 'R')}"),
                       delete_after=min(err.retry_after, 15))
    elif isinstance(err, commands.MissingRequiredArgument):
        usage = f".{ctx.command.qualified_name} {ctx.command.signature}".strip()
        await ctx.send(embed=error_embed("Trūksta argumento", f"Naudojimas: `{usage}`"))
    elif isinstance(err, (commands.BadArgument, commands.MemberNotFound)):
        await ctx.send(embed=error_embed("Blogas argumentas", str(err)))
    elif isinstance(err, commands.NotOwner):
        await ctx.send(embed=error_embed("Tik botų savininkui", "Šita komanda ne tau 😎"))
    elif isinstance(err, commands.MissingPermissions):
        await ctx.send(embed=error_embed("Neturi teisių", "Reikia administratoriaus teisių."))
    else:
        logging.getLogger("bot").exception("Command error in %s", ctx.command, exc_info=err)
        print(f"ERROR in .{ctx.command}: {err!r}")
        await ctx.send(embed=error_embed("Kažkas nepavyko", f"`{type(err).__name__}: {err}`"[:300]))


bot.run(token, log_handler=handler, log_level=logging.INFO)
