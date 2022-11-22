import wikipedia
from discord.ext import commands
from datetime import *
import os


def time():
    now = datetime.now()
    return now.strftime("[%H:%M:%S] --- ")


def logger(message):
    os.chdir("logs")
    today = date.today()
    logfile = open(today.strftime("%Y%m%d") + ".txt", 'a', encoding='utf-8')
    logfile.write("\n" + time() + message)
    logfile.close()
    os.chdir("..")


class WikiCog(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command(description="Search wikipedia with the keywords and return the results, usually to do another"
                      "command, like wikisumm.", aliases=['search'])
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
            try:
                summary = wikipedia.summary(keywords, auto_suggest=False)
            except wikipedia.DisambiguationError as e:
                msg = f"DisambiguationError. {keywords} may refer to:\n"
                if len(e.options) > 5:
                    for i in range(0, 5):
                        msg += e.options[i] + "\n"
                    msg += "...and " + str(len(e.options) - 5) + f" more\n I suggest you do Kevin wikisearch {keywords}"
                else:
                    for option in e.options:
                        msg += option + "\n"
                await ctx.send(msg)
                logger(f"Disambiguation error with keyword: {keywords}")
                return
        await ctx.send(summary)
        logger("Wiki summary of: " + keywords)

    @commands.command(description="Prints the title of random wikipedia articles. Maximum of 10.")
    async def wikirand(self, ctx, amount):
        if amount <= 0:
            amount = 1
        elif amount > 10:
            amount = 10
        msg = ""
        async with ctx.typing():
            results = wikipedia.random()
            for result in results:
                msg += result + "\n"
        await ctx.send(msg)
        logger("Random wiki pages: \n" + msg)


async def setup(client):
    await client.add_cog(WikiCog(client))
