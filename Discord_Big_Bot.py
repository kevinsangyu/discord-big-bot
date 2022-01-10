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
    facts = [
        'The moon has moonquakes',
        'Humans are the only animals that blush',
        'The wood frog can hold its pee for up to eight months',
        'The hottest spot on the planet is in Libiya',
        'Your nostrils work one at a time',
        "Rabbits can't puke",
        'The human body literally glows',
        'Copper door knobs are self-disinfecting',
        'Cotton candy was invented by a dentist',
        'Marie Curie is the only person to earn a Nobel prize in two different sciences',
        "Fingernails don't grow after you die",
        'The English word with the most definitions is "set"',
        'Pigeons can tell the difference between a painting by Monet and Picasso',
        'The dot over the lower case "i" or "j" is known as a "tittle"',
        'Chewing gum boosts concentration',
        'The first computer was invented in the 1940s',
        'Space smells like seared steak',
        'The longest wedding veil was the same length as 63.5 football fields',
        'The unicorn is the national animal of Scotland',
        'Bees sometimes sting other bees',
        'The total weight of ants on earth once equaled the total weight of people',
        "A dozen bodies were once found in Benjamin Franklin's basement",
        'The healthiest place in the world is in Panama',
        'A pharaoh once lathered his slaves in honey to keep bugs away from him',
        'Some people have an extra bone in their knee',
        "Abraham Lincoln's bodyguard left his post at Ford's Theatre to go for a drink",
        'Dolphins have been trained to be used in wars',
        'Playing the accordion was once required for teachers in North Korea',
        "Children's medicine once contained morphine",
        'Koalas have fingerprints',
        'Humans are just one of the estimated 8.7 million species on Earth',
        'Riding a roller coaster could help you pass a kidney stone',
        'Dinosaurs lived on every continent',
        'Bee hummingbirds are so small they get mistaken for insects',
        'Sea lions can dance to a beat',
        'Rolls-Royce makes the most expensive car in the world',
        'The legend of the Loch Ness Monster goes back nearly 1,500 years',
        'Nutmeg can be fatally poisonous',
        'Chinese police use geese squads',
        "The first iPhone wasn't made by Apple",
        "There's a country where twins are most likely to be born",
        'The Comic Sans font came from an actual comic book',
        "For 100 years, maps have shown an island that doesn't exist",
        'The Australian government banned the word "mate" for a day',
        'A tick bite can make you allergic to red meat',
        'Tornadoes can cause "fish rain"',
        'Napoleon was once attacked by thousands of rabbits',
        "Sweat doesn't actually stink",
        'Pigs are constitutionally protected in Florida',
        'Some planets produce diamond rain',
        'Sharks can live for five centuries',
        "The Bermuda Triangle isn't any more likely to cause a mysterious disappearance than anywhere else",
        "There's a world record—and a happy ending—for the greatest distance thrown in a car accident",
        "You can sneeze faster than a cheetah can run",
        "The fire hydrant patent was lost in a fire",
        "Saudi Arabia imports camels from Australia",
        "One man once survived two atomic bombs",
        "The cast of Friends still earns around $20 million each year",
        "Scientists have discovered that, on occasions, an octopus will 'punch' a fish for no reason other than 'spite'",
        "The Belgian Society for the Elevation of the Domestic Cat once trained 37 cats to deliver mail in the Belgian city of Liege",
        "The longest wedding veil ever was longer than 63 football fields, according to the Guinness World Records",
        "Nipples, just like a fingerprint, are unique.",
        "Macquarie Disctionary's Word of the Year for 2020 is 'doomscrolling'",
        "The letter Q doesn't appear in any of the U.S. state's names",
        'A cow-bison hybrid is called a "beefalo"',
        "Scotland has 421 words for 'snow'",
        "Peanuts aren't technically nuts",
        "Armadillo shells are bulletproof",
        "Firefighters use wetting agents to make water wetter",
        "The longest English word is 189,819 letters long",
        "Octopuses lay 56,000 eggs at a time",
        "Cats have fewer toes on their back paws",
        "Kleenex tissues were originally intended for gas masks",
        "Blue whales eat half a million calories in one mouthful",
        "That tiny pocket in jeans was designed to store pocket watches",
        "Most Disney characters wear gloves to keep animation simple",
        "The man with the worlds deepest voice can make sounds humans can't hear",
        "The current American flag was designed by a high school student",
        "Thanks to 3D printing, NASA can basically 'email' tools to astronauts",
        "There were active volcanoes on the moon when dinosaurs were alive",
        "Avocados were named after reproductive organs",
        "You only have two body parts that never stop growing: the nose and the ears",
        "No number before 1,000 contains the letter A",
        "The French have their own name for a French kiss",
        "The U.S. government saved every public tweet from 2006 through 2017",
        "H&M actually stands for Hennes & Mauritz",
        "Theodore Roosevelt had a pet hyena",
        "The CIA headquarters has its own Starbucks, but baristas don't write names on the cups",
        "Giraffe tongues can be 20 inches long",
        "Theres only one U.S. state capital without a McDonalds",
        "Europeans were scared of eating tomatoes when they were introduced",
        "The inventor of the microwave appliance only received $2 for his discovery",
        "The Eiffel Tower can grow more than six inches during the summer",
        "Glitter was made on a ranch",
        "Sloths have more neck bones than giraffes",
        "Bees can fly higher than Mount Everest",
        "Ancient Egyptians used dead mice to ease toothaches",
        "Paint used to be stored in pig bladders",
        "Humans have jumped further than horses in the Olympics",
        "Pigeon poop is the property of the British Crown",
        "Onions were found in the eyes of an Egyptian mummy",
        "Abraham Lincoln was a bartender",
        "Beethoven never knew how to multiply or divide",
        "The word aquarium means 'watering place for cattle' in Latin",
        "An employee at Pixar accidentally deleted a sequence of Toy Story 2 during production",
        "Steve Jobs, Steve Wozniak, and Ron Wayne started Apple Inc. on April Fool's Day",
        "The inventor of the tricycle personally delivered two to Queen Victoria",
        "Your brain synapses shrink while you sleep",
        "Boars wash their food",
        "Baseball umpires used to sit in rocking chairs",
        "The first commercial passenger flight lasted only 23 minutes",
        "The world's first novel ends mid-sentence",
        "The French-language Scrabble World Champion doesn't speak French",
        "A woman called the police when her ice cream didnt have enough sprinkles",
        "Uncle Bens rice was airdropped to World War II troops",
        "The British Empire was the largest empire in world history",
        "South American river turtles talk in their eggs",
        "The first stroller was pulled by a goat",
        "170-year-old bottles of champagne were found at the bottom of the Baltic Sea",
        "The MGM lion roar is trademarked",
        "Neil Armstrongs hair was sold in 2004 for $3,000",
        "Pregnancy tests date back to 1350 BCE",
        "Bananas glow blue under black lights",
        "The average person will spend six months of their life waiting for red lights to turn green",
        "A bolt of lightning contains enough energy to toast 100,000 slices of bread",
        "Cherophobia is the word for the irrational fear of being happy",
        "You can hear a blue whale's heartbeat from two miles away",
        "Nearly 30,000 rubber ducks were lost at sea in 1992 and are still being discovered today",
        "The inventor of the frisbee was turned into a frisbee after he died",
        "Blood banks in Sweden notify donors when blood is used",
        "Roosters have built-in earplugs",
        "The Netherlands is so safe, it imports criminals to fill jails",
        "The world's largest pyramid isn't in Egypt",
        "Coke saved one town from the Depression",
        "Incan people used knots to keep records",
        "A U.S. Park Ranger once got hit by lightning seven times",
        "Water bottle expiration dates are for the bottle, not the water",
        "South Koreans are four centimeters taller than North Koreans",
        "The most requested funeral song in England is by Monty Python",
        "Pandas fake pregnancy for better care",
        "Beloved children's book author Roald Dahl was a spy",
        "NASCAR drivers can lose up to 10 pounds in sweat due to high temperatures during races",
        "Indians spend 10+ hours a week reading, more than any other country in the world",
        "The Aurora Borealis has a sister phenomenon in the southern hemisphere called the Aurora Australis",
        "Your funny bone is actually a nerve",
        "Pineapples were named after pine cones",
        "A California woman tried to sue the makers of Cap'N'Crunch after she learned Crunch Berries were not real berries",
        "Apple briefly had its own clothing and lifestyle line in 1986",
        "The IKEA catalog is the most widely printed book in history",
        "Crocodiles are one of the oldest living species, having survived for more than 200 million years",
        "Bacon's saltiness isn't naturalit comes from curing and brining",
        "Research shows that all blue-eyed people may be related",
        "There was a fifth Beatle named Stuart Sutcliffe",
        "The cracking sound your joints make is the sound of gases being released",
        "The largest snowflake on record was 15 inches wide",
        "A pig was once executed for murdering a child in France",
        "Someone tried to sell New Zealand on eBay but was stopped once the bid reached $3,000",
        "The punctuation mark ?! is called an interrobang",
        "Doritos are flammable and can be used as kindling",
        "It's illegal to own only one guinea pig in Switzerland",
        "In 2016, a Florida man was charged with assault after throwing a live alligator through a drive-thru window",
        "The first written use of 'OMG' was in a 1917 letter to Winston Churchill"
    ]
    morbid = [
        "I have a severe case of depression",
        "I sometimes lie on my bed, as if I was spat out like an unwanted child from the womb of a young mother. Making a continuous drowning sound, trying to drown out the reality, that my life will not be a Yelp, but merely an agonized whisper, that won't reverberate anywhere beyond this closed up hell I call my room",
        "You have achieved nothing in your life and will die a meaningless death",
        "The last time you exercised was probably when Trump was still president",
        "Fuck you",
        "Take a piece of paper, fold it in half eight times, soak it in olive oil, and shove it up your ass."
    ]
    i = random.randint(1, 100)
    if i > 3:
        await ctx.send("Did you know: " + random.choice(facts))
        logger("A real fact was printed.")
    else:
        await ctx.send("Did you know: " + random.choice(morbid))
        logger("A morbid fact was printed.")


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
    elif amount > 10:
        amount = 10
    alphanumeric = "1 2 3 4 5 6 7 8 9 0 a b c d e f g h i j k l m n o p q r s t u v w x y z"
    alpha = alphanumeric.split(" ")
    result = "https://prnt.sc/"
    for i in range(0, amount):
        for j in range(6):
            result += random.choice(alpha)
        await ctx.send(result)


client.run(botkeys["BotToken"])
