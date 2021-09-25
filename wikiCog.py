import wikipedia
import discord
from discord.ext import commands
from datetime import *


def time():
    now = datetime.now()
    return now.strftime("[%H:%M:%S] --- ")


def logger(message):
    today = date.today()
    logfile = open(today.strftime("%d%m%Y") + ".txt", 'a', encoding='utf-8')
    logfile.write("\n" + time() + message)
    logfile.close()


class WikiCog(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command(description="Search wikipedia with the keywords and return the results, usually to do another"
                      "command, like wikisumm.")
    async def wikisearch(self, ctx, *keywords):
        keywords = " ".join(keywords)
        async with ctx.typing():
            search = wikipedia.search(keywords)
        msg = ""
        for i in search:
            msg += i + "\n"
        await ctx.send(msg)
        logger("Wiki search with keywords: " + keywords)

    @commands.command(description="Print a summary of a page in wikipedia. Use wikisearch to get the correct page name")
    async def wiki(self, ctx, *keywords):
        keywords = " ".join(keywords)
        async with ctx.typing():
            summary = wikipedia.summary(keywords)
        await ctx.send(summary)
        logger("Wiki summary of: " + keywords)

    # eventually want to add a random page getter, as well as a random page to random page 'game' thing.


def setup(client):
    client.add_cog(WikiCog(client))
