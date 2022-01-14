import random
from datetime import *
import discord
from discord.ext import commands
import musicCog
import wikiCog
import moneyCog
import translateCog
import mathCog
import os
import Botkeys


try:
    os.mkdir("logs")
except FileExistsError:
    pass
try:
    os.mkdir("transfers")
except FileExistsError:
    pass

intents = discord.Intents.default()
intents.members = True
client = commands.Bot(command_prefix='Kevin ', intents=intents)
cogs = [musicCog, wikiCog, moneyCog, translateCog, mathCog]
for cog in cogs:
    cog.setup(client)
botkeys = Botkeys.get_keys()


def time():
    now = datetime.now()
    return now.strftime("[%H:%M:%S] --- ")


def logger(message):
    os.chdir("logs")
    today = date.today()
    logfile = open(today.strftime("%d%m%Y") + ".txt", 'a', encoding='utf-8')
    logfile.write("\n" + time() + message)
    logfile.close()
    os.chdir("..")


@client.event
async def on_ready():
    await client.change_presence(activity=discord.Activity(name="'Kevin help' for help.", type=3))
    logger("Big Bot is online.")
    print("Big Bot is online.")


@client.event
async def on_command_error(ctx, error):
    if isinstance(error, discord.ext.commands.MissingRequiredArgument):
        msg = f"Missing required argument(s): {error.param}\nI suggest you do `Kevin help {ctx.command}`"
    elif isinstance(error, discord.ext.commands.MissingPermissions):
        msg = f"Missing permissions: {error.missing_perms}."
    elif isinstance(error, discord.ext.commands.CommandNotFound):
        msg = f"No such command\nI suggest you do `Kevin help`"
    elif isinstance(error, discord.ext.commands.MemberNotFound):
        msg = f"Member {error.argument} does not exist."
    elif isinstance(error, discord.ext.commands.CommandOnCooldown):
        msg = "Command is on cooldown, give it {:.1f} seconds.".format(error.retry_after)
    else:
        msg = f"Something went wrong, or invalid input.\nI suggest you do `Kevin help {ctx.command}`\n{error}"
        print(error)
        logger("Error: " + str(error))
    await ctx.send(msg)


@client.command(description="Replys with the time taken to respond in ms.")
async def ping(ctx):
    latency = round(client.latency * 1000)
    await ctx.send(f"Pong {latency}ms")
    logger("Ping command, with latency:" + str(latency))


@client.command(description="Repeats whatever you wrote.")
async def say(ctx, *, message):
    await ctx.send(message)
    logger("From: " + ctx.message.author.name + "\nSaid: " + message)


@client.command(aliases=['8ball'], description="Gives you an 8ball reply.")
async def _8ball(ctx, *, question):
    responses = ["It is certain.",
                 "It is decidedly so.",
                 "Without a doubt.",
                 "Yes – definitely.",
                 "You may rely on it.",
                 "As I see it, yes.",
                 "Most likely.",
                 "Outlook good.",
                 "Yes.",
                 "Signs point to yes.",
                 "Reply hazy, try again.",
                 "Ask again later.",
                 "Better not tell you now.",
                 "Cannot predict now.",
                 "Concentrate and ask again.",
                 "Don't count on it.",
                 "My reply is no.",
                 "My sources say no.",
                 "Outlook not so good.",
                 "Very doubtful."]
    reply = random.choice(responses)
    await ctx.send(reply)
    logger("8Ball result: " + reply)


@client.command(aliases=['coin', 'headsortails', 'heads', 'tails'], description="Flips a coin.")
async def coinflip(ctx):
    results = ["Heads.", "Tails."]
    reply = random.choice(results)
    await ctx.send(reply)
    logger("Heads or tails, result: " + reply)


@commands.has_permissions(manage_messages=True)
@client.command(aliases=['prune'], description="Deletes the most recent messages. The number does not count the messag"
                                               "e itself.")
async def clear(ctx, amount=0):
    await ctx.channel.purge(limit=amount + 1)
    logger("Clearing " + str(amount) + " lines.")


@client.command(description="Warns a user.")
async def warn(ctx, member: discord.Member):
    msg = "You have 2 weeks."
    await member.send(msg)
    logger("Warning: " + str(member))


@client.command(aliases=['pm', 'msg', 'whisper', 'message'], description="The bot will send a message to the given user"
                                                                         ". EG: Kevin dm @Shrewd#3618 testing message")
async def dm(ctx, member: discord.Member, *, message):
    await member.send(message)
    logger("Sending message to: " + str(member) + ". The message: " + message)


@client.command(aliases=['Paint', 'assign'],
                description="Gives a user another user in the group, with no repeats. "
                            "Separate names with only a single space.")
async def paint(ctx, *, memberlist):
    logger("Paint command received, string: " + memberlist)
    members = memberlist.split(" ")
    if len(members) == 1:
        await ctx.send("Not enough members provided.")
        logger("Not enough members provided for paint command.")
        return
    logger("Provided members: " + str(members))
    while True:
        reset = 0
        results = []
        used = []
        for x in range(0, len(members)):
            choice = random.choice(members)
            while members[x] == choice or choice in used:
                choice = random.choice(members)
                if len(used) == len(members) - 1 and members[x] == choice:
                    reset = 1
                    break
            results.append(members[x] + " --> ||" + choice + "||")
            used.append(choice)
        if reset == 0:
            break
    logstr = "\n               ------Results------"
    for x in results:
        await ctx.send(x)
        logstr += "\n               " + x
    logger(logstr)


@client.command(aliases=['team', 'split', 'Team', 'Teams', 'Split'],
                description="Splits given people into given number of teams. Separate names with only a single space.")
async def teams(ctx, amount, *, memberlist):
    logger("Teams: String received: " + memberlist)
    members = memberlist.split(" ")
    result = []
    amount = int(amount)
    logger("Splitting people into teams, with members: " + str(members))
    i = 0
    while i < amount:
        result.append("")
        i += 1
    while members:
        for x in range(0, amount):
            choice = random.choice(members)
            result[x] += choice + " "
            i = 0
            while i < len(members):
                if choice == members[i]:
                    del members[i]
                i += 1
            if not members:
                break
    logstr = "\n               ------Results------"
    for x in range(0, len(result)):
        await ctx.send("Team number " + str(x + 1) + ": " + result[x])
        logstr += "\n               " + "Team number " + str(x + 1) + ": " + result[x]
    logger(logstr)


@client.command(aliases=['pick'], description="Chooses an item in a given set of items. Separate names with a single"
                                              " space.")
async def choose(ctx, *, itemlist):
    logger("Choose: String received: " + itemlist)
    items = itemlist.split(" ")
    logger("Items: " + str(items))
    result = random.choice(items)
    logger("Chosen item: " + result)
    await ctx.send("I choose " + result + ".")


@client.command(description="Returns a random fact.")
async def fact(ctx):
    facts = open("facts.txt", "r+").readlines()
    await ctx.send("Did you know: " + random.choice(facts)[:-1])
    logger("A real fact was printed.")


@client.command(description="Holds a poll with reactions. Prompt comes first, then separate the prompt and options with"
                            " a comma - Kevin poll This is a prompt, opt1, opt2, opt3")
async def poll(ctx, *, question):
    options = question.split(",")
    prompt = options.pop(0)
    number_emojis = ["1\N{combining enclosing keycap}", "2\N{combining enclosing keycap}",
                     "3\N{combining enclosing keycap}", "4\N{combining enclosing keycap}",
                     "5\N{combining enclosing keycap}", "6\N{combining enclosing keycap}",
                     "7\N{combining enclosing keycap}", "8\N{combining enclosing keycap}",
                     "9\N{combining enclosing keycap}", "0\N{combining enclosing keycap}"]
    options_str = ""
    for i in range(0, len(options)):
        options[i] = number_emojis[i] + options[i] + "\n"
        options_str += options[i]
    msg = await ctx.send(prompt + "\n" + options_str)
    logger("Poll called with prompt: " + prompt + ", and options: " + str(options))
    for i in range(0, len(options)):
        await msg.add_reaction(number_emojis[i])


@client.command(description="Wishes luck to kevin")
async def goodluck(ctx, *rest):
    await ctx.send("Thanks.")


@client.command(description="Retrives a given amount (max 10) of random screenshot from lightshot's website, prnt.sc\n "
                            "Warning: These are really random, you might see things that you shouldn't or wouldn't want"
                            " to.")
async def randomss(ctx, amount: int = 1):
    if amount < 1:
        amount = 1
    elif amount > 5:
        amount = 5
    alphanumeric = "1 2 3 4 5 6 7 8 9 0 a b c d e f g h i j k l m n o p q r s t u v w x y z"
    alpha = alphanumeric.split(" ")
    result = ""
    for i in range(0, amount):
        page = "https://prnt.sc/"
        for j in range(6):
            page += random.choice(alpha)
        result += page + "\n"
    await ctx.send(result)


client.run(botkeys["BotToken"])
