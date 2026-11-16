"""Petras Wordle — guess the iconic phrase in 6 tries."""
import asyncio
import json
import os
import random
import unicodedata

import discord
from discord.ext import commands

from .economy import add_user_coins
from .ui import make_embed, success, error, owner_only, BRAND, SUCCESS, ERROR, DARK

print(">>> Wordle commands loaded")

WORDS_FILE = "wordle_words.txt"                         # tracked in git
EXTRA_WORDS_FILE = os.path.join("data", "wordle_extra.json")  # added with .addword, lives only on the server

MAX_TRIES = 6
GUESS_TIMEOUT = 300          # seconds of silence before the game ends
REWARD_PER_TRY_LEFT = 50     # win on try 1 = 300 coins, try 6 = 50 coins

GREEN, YELLOW, GRAY = "🟩", "🟨", "⬛"
GAP = "▫️"
STOP_WORDS = {"stop", "baigti", "quit", "giveup"}

_recent: list[str] = []
_active_players: set[int] = set()


# ---------------- words ----------------

def normalize(text: str) -> str:
    """Lowercase, strip Lithuanian diacritics, keep only a-z and single spaces."""
    text = unicodedata.normalize("NFD", text.lower())
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = "".join(c if "a" <= c <= "z" else " " for c in text)
    return " ".join(text.split())


def load_extra_words() -> list[str]:
    try:
        with open(EXTRA_WORDS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def load_words() -> list[str]:
    words = []
    if os.path.exists(WORDS_FILE):
        with open(WORDS_FILE, "r", encoding="utf-8") as f:
            words += [line for line in f if line.strip() and not line.lstrip().startswith("#")]
    words += load_extra_words()
    normalized = (normalize(w) for w in words)
    return sorted({w for w in normalized if len(w.replace(" ", "")) >= 3})


def pick_word(words: list[str]) -> str:
    choices = [w for w in words if w not in _recent] or words
    word = random.choice(choices)
    _recent.append(word)
    del _recent[:-max(1, len(words) // 2)]
    return word


# ---------------- scoring / drawing ----------------

def score(guess: str, target: str) -> list[str]:
    """Classic Wordle scoring (handles repeated letters). Both strings without spaces."""
    result = [GRAY] * len(target)
    remaining = {}
    for i, (g, t) in enumerate(zip(guess, target)):
        if g == t:
            result[i] = GREEN
        else:
            remaining[t] = remaining.get(t, 0) + 1
    for i, g in enumerate(guess):
        if result[i] != GREEN and remaining.get(g, 0) > 0:
            result[i] = YELLOW
            remaining[g] -= 1
    return result


def letter_emoji(c: str) -> str:
    return chr(0x1F1E6 + ord(c) - ord("a"))


def with_gaps(cells: list[str], target: str) -> str:
    """Re-insert gaps where the target phrase has spaces. Cells are separated by a
    zero-width space so regional-indicator letters never merge into flags."""
    out, i = [], 0
    for ch in target:
        if ch == " ":
            out.append(GAP)
        else:
            out.append(cells[i])
            i += 1
    return "​".join(out)


def blank_row(target: str) -> str:
    return with_gaps(["⬜"] * len(target.replace(" ", "")), target)


class Game:
    def __init__(self, player: discord.abc.User, target: str):
        self.player = player
        self.target = target
        self.letters = target.replace(" ", "")
        self.rows: list[tuple[str, list[str]]] = []
        self.absent: set[str] = set()
        self.present: set[str] = set()

    @property
    def won(self) -> bool:
        return bool(self.rows) and all(t == GREEN for t in self.rows[-1][1])

    @property
    def over(self) -> bool:
        return self.won or len(self.rows) >= MAX_TRIES

    def guess(self, word: str):
        tiles = score(word, self.letters)
        self.rows.append((word, tiles))
        for c, t in zip(word, tiles):
            if t == GRAY and c not in self.letters:
                self.absent.add(c)
            elif t != GRAY:
                self.present.add(c)

    def board(self) -> str:
        lines = []
        for word, tiles in self.rows:
            lines.append(with_gaps(tiles, self.target))
            lines.append(with_gaps([letter_emoji(c) for c in word], self.target))
        for _ in range(MAX_TRIES - len(self.rows)):
            lines.append(blank_row(self.target))
        return "\n".join(lines)

    def embed(self, status: str = None, color: int = BRAND) -> discord.Embed:
        n = len(self.letters)
        words = len(self.target.split())
        shape = f"**{n} raidės**" + (f", **{words} žodžiai**" if words > 1 else "")
        embed = make_embed(f"🟩 Petro Wordle — {len(self.rows)}/{MAX_TRIES}", None, color)
        embed.set_author(name=self.player.display_name, icon_url=self.player.display_avatar.url)
        embed.description = f"Atspėk Petro frazę: {shape}\n\n{self.board()}"
        if self.absent:
            embed.add_field(name="🚫 Nėra", value=" ".join(sorted(self.absent)).upper(), inline=True)
        if self.present:
            embed.add_field(name="✅ Yra", value=" ".join(sorted(self.present)).upper(), inline=True)
        embed.add_field(
            name="Kaip žaisti",
            value=status or "Tiesiog parašyk spėjimą į chatą. `stop` – pasiduoti.",
            inline=False,
        )
        return embed


# ---------------- commands ----------------

def setup_wordle_commands(bot: commands.Bot):

    @bot.command(aliases=["pw", "petrowordle"])
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def wordle(ctx: commands.Context):
        if ctx.author.id in _active_players:
            await ctx.send(embed=error("Jau žaidi!", "Pirma pabaik dabartinį žaidimą (arba parašyk `stop`)."))
            return

        words = load_words()
        if not words:
            await ctx.send(embed=error("Nėra žodžių", f"Pridėk frazių į `{WORDS_FILE}` arba per `.addword`."))
            return

        game = Game(ctx.author, pick_word(words))
        _active_players.add(ctx.author.id)
        board_msg = await ctx.send(embed=game.embed())

        def check(m: discord.Message) -> bool:
            return (
                m.author.id == ctx.author.id
                and m.channel.id == ctx.channel.id
                and not m.content.startswith(ctx.prefix or ".")
            )

        try:
            while not game.over:
                try:
                    msg = await bot.wait_for("message", check=check, timeout=GUESS_TIMEOUT)
                except asyncio.TimeoutError:
                    await board_msg.edit(embed=game.embed(
                        f"⏰ Laikas baigėsi! Atsakymas buvo **{game.target.upper()}**", ERROR))
                    return

                raw = normalize(msg.content)
                if raw in STOP_WORDS:
                    await board_msg.edit(embed=game.embed(
                        f"🏳️ Pasidavei. Atsakymas buvo **{game.target.upper()}**", ERROR))
                    return

                guess = raw.replace(" ", "")
                if len(guess) != len(game.letters):
                    await msg.reply(
                        f"Reikia **{len(game.letters)}** raidžių (tu parašei {len(guess)}).",
                        delete_after=4, mention_author=False,
                    )
                    continue

                game.guess(guess)
                try:
                    await msg.delete()
                except (discord.Forbidden, discord.HTTPException):
                    pass

                if game.won:
                    tries = len(game.rows)
                    reward = (MAX_TRIES - tries + 1) * REWARD_PER_TRY_LEFT
                    add_user_coins(str(ctx.author.id), reward)
                    status = f"🎉 **{game.target.upper()}** – atspėjai per {tries}! +**{reward}** coins"
                    color = SUCCESS
                elif game.over:
                    status = f"💀 Nepavyko. Atsakymas buvo **{game.target.upper()}**"
                    color = ERROR
                else:
                    status, color = None, BRAND

                # Re-send the board so it stays at the bottom of the chat
                new_msg = await ctx.send(embed=game.embed(status, color))
                try:
                    await board_msg.delete()
                except discord.HTTPException:
                    pass
                board_msg = new_msg
        finally:
            _active_players.discard(ctx.author.id)

    @bot.command()
    @owner_only()
    async def addword(ctx: commands.Context, *, phrase: str):
        clean = normalize(phrase)
        if len(clean.replace(" ", "")) < 3:
            await ctx.send(embed=error("Per trumpa", "Mažiausiai 3 raidės."))
            return
        if clean in load_words():
            await ctx.send(embed=error("Jau yra", f"`{clean}` jau sąraše."))
            return
        extra = load_extra_words()
        extra.append(clean)
        os.makedirs("data", exist_ok=True)
        with open(EXTRA_WORDS_FILE, "w", encoding="utf-8") as f:
            json.dump(extra, f, indent=2, ensure_ascii=False)
        await ctx.send(embed=success("Pridėta į Wordle", f"`{clean}` • iš viso frazių: **{len(load_words())}**"))

    @bot.command()
    @owner_only()
    async def removeword(ctx: commands.Context, *, phrase: str):
        clean = normalize(phrase)
        extra = load_extra_words()
        if clean not in extra:
            await ctx.send(embed=error("Nerasta", f"`{clean}` nėra tarp pridėtų per `.addword` "
                                                  f"(žodžius iš `{WORDS_FILE}` keisk GitHub'e)."))
            return
        extra.remove(clean)
        with open(EXTRA_WORDS_FILE, "w", encoding="utf-8") as f:
            json.dump(extra, f, indent=2, ensure_ascii=False)
        await ctx.send(embed=success("Pašalinta", f"`{clean}`"))

    @bot.command()
    @owner_only()
    async def words(ctx: commands.Context):
        all_words = load_words()
        listing = "\n".join(f"• {w}" for w in all_words) or "—"
        embed = make_embed(f"📚 Wordle frazės ({len(all_words)})", listing[:4000], DARK)
        try:
            await ctx.author.send(embed=embed)
            await ctx.message.add_reaction("📬")
        except discord.Forbidden:
            await ctx.send(embed=error("Negaliu parašyti DM", "Įsijunk DM iš serverio narių."))
