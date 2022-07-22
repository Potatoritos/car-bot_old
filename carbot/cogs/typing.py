import asyncio
import math
import random
import time
from typing import Annotated as A, Optional

from bs4 import BeautifulSoup
import discord
from loguru import logger
import requests

import car
import carpp


class Typing(car.Cog):
    category = "Typing"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.excerpts = car.DBTable(self.bot.con, 'typing_excerpts', (
            car.DBColumn('id', 0, is_primary=True),
            car.DBColumn('text', ""),
            car.DBColumn('length', 0),
            car.DBColumn('diff', 0),
            car.DBColumn('pool', 0),
        ))

    @staticmethod
    def is_shifted(char):
        return char.isupper() or char in '~!@#$%^&*()_+{}|:"<>?'

    @staticmethod
    def typing_diff(text):
        current_points = 0
        total_points = 0
        words = 0

        text = f"  {text} "

        for i in range(2, len(text)):
            if text[i] == ' ':
                total_points += current_points**2
                current_points = 0
                words += 1
                continue

            current_points += 1 \
                + (Typing.is_shifted(text[i]) != Typing.is_shifted(text[i-1]))\
                + 0.25 * text[i].isdigit() \
                + 0.3 * (not text[i].isdigit() and not text[i].isalpha()) \
                + 0.5 * (text[i] == text[i-1] != text[i-2])

        return round(total_points*10 / words * math.log(len(text)))

    @car.mixed_command(aliases=["typingtest"])
    async def wpm(
        self, ctx,
        difficulty: A[
            Optional[str],
            car.FromChoices({
                "Any": 'any',
                "Easy": 'easy',
                "Medium": 'medium',
                "Hard": 'hard',
                "Insane": 'insane',
                "Expert": 'expert',
                "Expert+": 'expertplus',
                "WTF": 'wtf'
            })
        ] = 'medium',
        length: A[
            Optional[str],
            car.FromChoices({
                "Any": 'any',
                "Short": 'short',
                "Medium": 'medium',
                "Long": 'long',
                "Very long": 'verylong'
            })
        ] = 'medium',
        no_punctuation: Optional[bool] = False,
        capitalization_filter: A[
            Optional[str],
            car.FromChoices({
                "All uppercase": 'allupper',
                "All lowercase": 'alllower',
                "Random capitalization": 'random',
                "None": 'none'
            }),
        ] = 'none',
        radiation_level: A[
            Optional[int],
            car.ToInt() | car.InRange(0, 100),
        ] = 0,
        pool: A[
            Optional[str],
            car.FromChoices({
                "All": 'all',
                "Typeracer": 'typeracer',
                "Wab": 'wab'
            })
        ] = 'typeracer'
    ):
        """Tests your typing speed"""
        diff_query = {
            'any': "0 and 9999999",
            'easy': "0 AND 1300",
            'medium': "1300 AND 1800",
            'hard': "1800 AND 2200",
            'insane': "2200 AND 2600",
            'expert': "2600 AND 3200",
            'expertplus': "3200 AND 4000",
            'wtf': "4000 AND 9999999"
        }[difficulty]

        len_query = {
            'any': "0 and 9999",
            'short': "0 AND 150",
            'medium': "150 AND 500",
            'long': "500 AND 800",
            'verylong': "800 AND 9999"
        }[length]

        pool_query = {
            'all': "0 AND 999",
            'typeracer': "1 AND 1",
            'wab': "2 and 2"
        }[pool]

        excerpt_ids = self.excerpts.select(
            'id',
            (f"WHERE diff BETWEEN {diff_query} AND length BETWEEN {len_query} "
             f"AND pool BETWEEN {pool_query}"),
            flatten=False
        )
        if len(excerpt_ids) == 0:
            raise car.CommandError("I couldn't find an excerpt with the "
                                   "specified conditions :(")

        selected_id = excerpt_ids[random.randint(0, len(excerpt_ids))]['id']

        excerpt = self.excerpts.select('*', "WHERE id=?", (selected_id,))

        text = excerpt['text']
        if no_punctuation:
            text = ''.join(c for c in text if 'a' <= c.lower() <= 'z' 
                           or c == ' ')

        match capitalization_filter:
            case 'allupper':
                text = text.upper()
            case 'alllower':
                text = text.lower()
            case 'random':
                text = ''.join(random.choice([c.lower(), c.upper()])
                               for c in text)

        if radiation_level > 0:
            l = list(text)

            for _ in range(int(len(text) * radiation_level/100)):
                idx = random.randint(0, len(text)-1)
                action = random.randint(0, 3)

                if action == 3:
                    l[idx] = text[idx].upper()
                else:
                    l[idx] = random.choice("~!@#$%^&*()_+{}|:\"<>?'\\/")

            text = ''.join(l)

        await ctx.respond(f"```{car.zwsp(text, 'aei')}```")
        start = time.monotonic()

        try:
            msg = await self.bot.wait_for(
                'message',
                timeout = 300,
                check=lambda m: m.author == ctx.author \
                    and m.channel == ctx.channel
            )
        except asyncio.TimeoutError:
            raise car.CommandError("You took too long to complete this test!")

        ZWSP = '​' # zero-width space
        if ZWSP in msg.content:
            await ctx.reply(":rotating_light: Copy and paste detected!")
            return

        # account for human reaction time
        elapsed = max(time.monotonic() - start - 0.3, 0.000001)

        wpm = len(text.split(' ')) / elapsed * 60
        cpm = len(text) / elapsed * 60
        acc = 1 - carpp.levenshtein(text, msg.content) / len(text)

        e = discord.Embed(description=(
            f"`WPM` **{round(wpm * acc**3)}** *({round(wpm)})*\n"
            f"`CPM` **{round(cpm * acc**3)}** *({round(cpm)})*\n"
            f"`Acc` **{round(acc * 100, 1)}%**"
        ))
        e.set_author(name="Test Results",
            icon_url=ctx.author.avatar.url)

        diff = self.typing_diff(text)

        diff_names = [(4000, "WTF"), (3200, "Expert+"), (2600, "Expert"),
                      (2200, "Insane"), (1800, "Hard"), (1300, "Medium"),
                      (0, "Easy")]

        diff_name = "If you see this, something has gone horribly wrong"
        for name_diff, name in diff_names:
            if diff >= name_diff:
                diff_name = name
                break

        e.set_footer(text=f"Text Difficulty: {diff} ({diff_name})")

        await ctx.send(embed=e)

    # @car.text_command(category="Hidden")
    # @car.requires_clearance(car.ClearanceLevel.ADMIN)
    # async def add_excerpt(self, ctx, text: str):
        # self.excerpts.

    @car.text_command(hidden=True)
    @car.requires_clearance(car.ClearanceLevel.ADMIN)
    async def load_typeracer_excerpts(self, ctx):
        """Receives excerpts from typeracer.com"""

        await ctx.defer()

        logger.info("Retrieving texts from typeracer")

        r = requests.get("http://typeracerdata.com/texts?texts=full")

        soup = BeautifulSoup(r.content, "html.parser")
        rows = soup.find_all("tr")

        cur = self.bot.con.cursor()
        for i in range(1, len(rows)):
            text = rows[i].find_all("td")[2].find("a").decode_contents()
            cur.execute(
                "INSERT INTO typing_excerpts VALUES(NULL, ?, ?, ?, 1)",
                (text, len(text), self.typing_diff(text))
            )
        self.bot.con.commit()

        await ctx.respond("done")

