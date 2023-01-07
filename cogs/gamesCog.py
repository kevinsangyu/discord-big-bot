import random
import os
from datetime import *
from discord.ext import commands
import Botkeys


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


class GamesCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.botkeys = Botkeys.get_keys()

    @commands.command(hidden=True)
    async def createGamesDB(self, ctx):
        try:
            os.mkdir("guildData")
        except FileExistsError:
            pass
        os.chdir("guildData")
        try:
            os.mkdir(str(ctx.guild.id))
        except FileExistsError:
            pass
        os.chdir("..")

    def generatePattern(self):
        pattern = []
        # mastermind pattern generation rules: 10* different colours, and pick 5 for one pattern. Repeats are allowed,
        # however: There must be at least 2 instances of at least one colour, but no more than 3 instances of one
        # colour, in one pattern.
        # *10 digits for more difficulty.
        colours = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

        # initially, lets pick 1 colour and add 2 instances of it:
        pattern.append(colours.pop(random.randint(0, len(colours) - 1)))
        pattern.append(pattern[0])

        # then, lets add 2 random colours, which can be the same colours, but not the initial colour.
        pattern.append(random.choice(colours))
        pattern.append(random.choice(colours))

        # finally, lets pick a random colour with no restrictions, then shuffle the pattern.
        pattern.append(random.randint(0, 9))
        random.shuffle(pattern)
        patternstring = ""
        for i in pattern:
            patternstring += str(i)
        return patternstring

    @commands.command(description="Starts or continues a game of mastermind. Try to guess the 5 digit combination by "
                                  "inputting a 5 digit combination of numbers between 0 and 9 inclusive. A black "
                                  "square means it's the right number in the right place, and a white square means a "
                                  "right number in the wrong place. A cross means a wrong number.")
    async def mastermind(self, ctx, guess):
        if len(guess) != 5:
            await ctx.send("Invalid amount of digits, a pattern consists of 5 numbers (repetition allowed).")
            return
        try:
            os.chdir(f"guildData/{ctx.guild.id}")
        except FileNotFoundError:
            await self.createGamesDB(ctx)
            os.chdir(f"guildData/{ctx.guild.id}")
        try:
            fileobj = open("mastermind.txt", "r")
            pattern = fileobj.readline()
            fileobj.close()
            await ctx.send("Continuing your game of mastermind. Only numbers between 0 and 9 inclusive are valid.")
        except FileNotFoundError:
            fileobj = open("mastermind.txt", "w")
            pattern = self.generatePattern()
            fileobj.write(pattern)
            fileobj.close()
            await ctx.send("Starting a new game of mastermind. Only numbers between 0 and 9 inclusive are valid.")
        results = ""
        emojis = {"0": "0️⃣", "1": "1️⃣", "2": "2️⃣", "3": "3️⃣", "4": "4️⃣", "5": "5️⃣", "6": "6️⃣", "7": "7️⃣", "8": "8️⃣", "9": "9️⃣"}
        emojified = ""
        for i in range(len(pattern)):
            if guess[i] not in ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]:
                await ctx.send("Invalid input, characters must be between numbers 0~9.")
                os.chdir("..")
                os.chdir("..")
                return
            if guess[i] == pattern[i]:
                results += "⬛"
            elif guess[i] in pattern:
                results += "⬜"
            else:
                results += "❌"
            emojified += emojis[guess[i]]
        await ctx.send(emojified + "\n" + results)
        if results == "⬛⬛⬛⬛⬛":
            await ctx.send("You win.")
            os.remove("mastermind.txt")
        os.chdir("..")
        os.chdir("..")


async def setup(client):
    await client.add_cog(GamesCog(client))
