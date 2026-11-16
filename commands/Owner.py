"""Owner-only maintenance commands: .update, .restart"""
import asyncio
import os
import sys

from discord.ext import commands

from .ui import make_embed, success, error, owner_only, SUCCESS, WARNING

print(">>> Owner commands loaded")


async def run(*cmd: str) -> tuple[int, str]:
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    out, _ = await proc.communicate()
    return proc.returncode, out.decode("utf-8", "replace").strip()


def shorten(text: str, limit: int = 900) -> str:
    return text if len(text) <= limit else "…" + text[-limit:]


def restart_process():
    """Replace the current process with a fresh copy of the bot (same PID, so the panel keeps it 'running')."""
    sys.stdout.flush()
    sys.stderr.flush()
    os.execv(sys.executable, [sys.executable] + sys.argv)


def setup_owner_commands(bot: commands.Bot):

    @bot.command()
    @owner_only()
    async def update(ctx: commands.Context):
        msg = await ctx.send(embed=make_embed("🔄 Atnaujinama...", "Traukiu naują kodą iš GitHub", WARNING))

        if not os.path.isdir(".git"):
            await msg.edit(embed=error("Nėra .git folderio", "Botas paleistas ne iš git repo."))
            return

        _, before = await run("git", "rev-parse", "HEAD")
        code, pull_out = await run("git", "pull", "--ff-only")
        if code != 0:
            await msg.edit(embed=error("git pull nepavyko", f"```\n{shorten(pull_out)}\n```"))
            return

        _, after = await run("git", "rev-parse", "HEAD")
        if before == after:
            await msg.edit(embed=success("Jau naujausia versija", f"Commit `{after[:7]}`"))
            return

        _, log = await run("git", "log", "--oneline", "--no-decorate", f"{before}..{after}")

        await msg.edit(embed=make_embed("📦 Instaliuojami paketai...", f"```\n{shorten(log)}\n```", WARNING))
        if os.path.exists("requirements.txt"):
            code, pip_out = await run(sys.executable, "-m", "pip", "install", "-q", "-U",
                                      "--prefix", ".local", "-r", "requirements.txt")
            if code != 0:
                await msg.edit(embed=error("pip install nepavyko", f"```\n{shorten(pip_out)}\n```"))
                return

        await msg.edit(embed=make_embed(
            "✅ Atnaujinta! Perkraunama...",
            f"`{before[:7]}` → `{after[:7]}`\n```\n{shorten(log)}\n```",
            SUCCESS,
        ))
        restart_process()

    @bot.command()
    @owner_only()
    async def restart(ctx: commands.Context):
        await ctx.send(embed=make_embed("🔁 Perkraunama...", "Grįšiu po kelių sekundžių", WARNING))
        restart_process()
