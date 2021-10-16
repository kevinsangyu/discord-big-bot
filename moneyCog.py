import math
import random
import discord
from discord.ext import commands, tasks
from datetime import *
import Botkeys
import json
import os


def time():
    now = datetime.now()
    return now.strftime("[%H:%M:%S] --- ")


def transaction_logger(guild, message):  # separate log, for the logs command
    os.chdir("transfers")
    try:
        os.mkdir(str(guild))
    except FileExistsError:
        pass
    os.chdir(str(guild))
    today = date.today()
    logfile = open(today.strftime("%d%m%Y") + ".txt", 'a', encoding='utf-8')
    logfile.write("\n" + time() + message)
    logfile.close()
    os.chdir("..")
    os.chdir("..")


def logger(message):
    os.chdir("logs")
    today = date.today()
    logfile = open(today.strftime("%d%m%Y") + ".txt", 'a', encoding='utf-8')
    logfile.write("\n" + time() + message)
    logfile.close()
    os.chdir("..")


def get_bank():
    bankfile = open("bank.txt")
    bankdict = json.load(bankfile)
    bankfile.close()
    return bankdict


def save_bank(bankdict):
    with open("bank.txt", "w") as output:
        json.dump(bankdict, output)


class MoneyMember:
    def __init__(self, id, money):
        self.id = id
        self.money = money


class MoneyCog(commands.Cog):
    def __init__(self, client):
        self.botkeys = Botkeys.get_keys()
        self.client = client
        self.salary.start()
        try:
            bankfile = open("bank.txt", "x")
            bankfile.write("{}")
            bankfile.close()
        except FileExistsError:
            pass

    def cog_unload(self):
        self.salary.cancel()

    @commands.command(description="Adds a user to the bank, i.e. initialising a bank account."
                                  "Can only be run by bank administrators.")
    async def register(self, ctx, user: discord.Member):
        if ctx.author.id != self.botkeys["Lucasid"] and ctx.author.id != self.botkeys["Kevinid"]:
            await ctx.send("You do not have permission to do that.")
            return
        bankdict = get_bank()
        if str(ctx.guild.id) not in bankdict.keys():
            bankdict[str(ctx.guild.id)] = {}
        if str(user.id) in bankdict[str(ctx.guild.id)].keys():
            await ctx.send("User already registered.")
        else:
            bankdict[str(ctx.guild.id)][str(user.id)] = 0
            save_bank(bankdict)
            ctx.send("User registered.")

    @commands.command(description="Removes a user from the bank, i.e. deletes a bank account."
                                  "Can only be run by bank administrators.")
    async def unregister(self, ctx, user: discord.Member):
        if ctx.author.id != self.botkeys["Lucasid"] and ctx.author.id != self.botkeys["Kevinid"]:
            await ctx.send("You do not have permission to do that.")
            return
        bankdict = get_bank()
        if str(ctx.guild.id) not in bankdict.keys():
            await ctx.send("This server does not have a bank allocated.")
            return
        if str(user.id) in bankdict[str(ctx.guild.id)].keys():
            amount = bankdict[str(ctx.guild.id)].pop(str(user.id))
            await ctx.send(f"{user.display_name} with {amount} has been unregistered.")
            logger(f"{user.display_name} with {amount} has been unregistered.")
        else:
            await ctx.send("That user does not have a bank account.")
        save_bank(bankdict)

    @commands.command(description="Adds users in a role to the bank, i.e. initialising a bank account."
                                  "Can only be ran by Kevin or Lucas.")
    async def massregister(self, ctx, role: discord.Role):
        if ctx.author.id != self.botkeys["Lucasid"] and ctx.author.id != self.botkeys["Kevinid"]:
            await ctx.send("You do not have permission to do that.")
            return
        bankdict = get_bank()
        if str(ctx.guild.id) not in bankdict.keys():
            bankdict[str(ctx.guild.id)] = {}
        counter = 0
        for member in role.members:
            if str(member.id) not in bankdict[str(ctx.guild.id)].keys():
                bankdict[str(ctx.guild.id)][str(member.id)] = 0
                counter += 1
        save_bank(bankdict)
        await ctx.send("Registered " + str(counter) + " users to the bank.")

    @commands.command(aliases=['bal'], description="Gets the balance of the user.")
    async def balance(self, ctx):
        bankdict = get_bank()
        if str(ctx.guild.id) not in bankdict.keys():
            await ctx.send("This server does not have a bank allocated.")
            return
        if str(ctx.author.id) not in bankdict[str(ctx.guild.id)].keys():
            await ctx.send("You have not been registered into the bank. Contact the bank administrators for more info.")
            return
        bal = bankdict[str(ctx.guild.id)][str(ctx.author.id)]
        await ctx.send(f"Your current balance is {bal} Wu points.")

    @commands.command(aliases=['balof'], description="Gets the balance of a user.")
    async def balanceof(self, ctx, user: discord.Member):
        bankdict = get_bank()
        if str(ctx.guild.id) not in bankdict.keys():
            await ctx.send("This server does not have a bank allocated.")
            return
        if str(user.id) not in bankdict[str(ctx.guild.id)].keys():
            await ctx.send(
                "They have not been registered into the bank. Contact the bank administrators for more info.")
            return
        bal = bankdict[str(ctx.guild.id)][str(user.id)]
        await ctx.send(f"Their current balance is {bal} Wu points.")
        transaction_logger(ctx.guild.id, str(user.display_name) + "'s balance: " + str(bal))

    @commands.command(description="Give the given user x amount of Wu points. The Wu points will be taken from"
                                  " the author's balance, unless they are bank administrators.")
    async def pay(self, ctx, amount, user: discord.Member):
        amount = abs(int(amount))
        bankdict = get_bank()
        if str(ctx.guild.id) not in bankdict.keys():
            await ctx.send("This server does not have a bank allocated.")
            return
        if str(ctx.author.id) not in bankdict[str(ctx.guild.id)].keys() or str(user.id) not in bankdict[str(ctx.guild.id)].keys():
            await ctx.send("You or the receiver have not been registered into the bank."
                           "Contact the bank administrators for more info.")
            return
        if ctx.author.id != self.botkeys["Lucasid"] and ctx.author.id != self.botkeys["Kevinid"] \
                and ctx.author.id != self.botkeys["Bigbotid"]:
            if bankdict[str(ctx.guild.id)][str(ctx.author.id)] - amount < 0:
                await ctx.send("You have insufficient Wu points.")
                return
            bankdict[str(ctx.guild.id)][str(ctx.author.id)] -= amount
        bankdict[str(ctx.guild.id)][str(user.id)] += amount
        save_bank(bankdict)
        await ctx.send(f"{amount} Wu points was transferred. Their balance is now "
                       f"{bankdict[str(ctx.guild.id)][str(user.id)]} Wu points")
        transaction_logger(ctx.guild.id, f"{ctx.author.display_name} paid {user.display_name} {amount} Wu points")

    @commands.command(aliases=["ded"], description="Deducts x amount of Wu points from a given user. Can only be used"
                                                   "by bank administrators. It is possible to go into the negatives.")
    async def deduct(self, ctx, amount, user: discord.Member):
        if ctx.author.id != self.botkeys["Lucasid"] and ctx.author.id != self.botkeys["Kevinid"] \
                and ctx.author.id != self.botkeys["Bigbotid"]:
            await ctx.send("You do not have permission to do that.")
            return
        amount = abs(int(amount))
        bankdict = get_bank()
        if str(ctx.guild.id) not in bankdict.keys():
            await ctx.send("This server does not have a bank allocated.")
            return
        if str(user.id) not in bankdict[str(ctx.guild.id)].keys():
            await ctx.send("The user has not been registered into the bank. Contact the bank administrators for more"
                           " info.")
            return
        bankdict[str(ctx.guild.id)][str(user.id)] -= amount
        save_bank(bankdict)
        await ctx.send(f"{amount} Wu points was deducted. Their balance is now"
                       f" {bankdict[str(ctx.guild.id)][str(user.id)]} Wu points")
        transaction_logger(ctx.guild.id, f"{user.display_name}'s balance was deducted by {amount}, their balance is now"
                                         f" {bankdict[str(ctx.guild.id)][str(user.id)]} Wu points")

    @tasks.loop(hours=1)
    async def salary(self):  # at the moment it gives everyone in every guild a weekly salary of 50
        now = datetime.now()  # if i wanted to have custom salaries, I'll have to make another json file for it
        salary_amount = 50
        if now.strftime("%w%H") == "000":
            bankdict = get_bank()
            for guild in bankdict.keys():
                for member in bankdict[guild].keys():
                    bankdict[guild][member] += salary_amount
                    user = await self.client.fetch_user(int(member))
                    transaction_logger(guild, f"{user.display_name} was paid their salary of "
                                              f"{salary_amount} Wu points.")
            save_bank(bankdict)

    @commands.command(aliases=['leader', 'lb'], description="Shows the rankings of the first 10 "
                                                            "users with the most Wu points.")
    async def leaderboard(self, ctx):
        bankdict = get_bank()
        rankings = []
        if str(ctx.guild.id) not in bankdict.keys():
            await ctx.send("This server does not have a bank allocated.")
            return
        async with ctx.typing():
            for member in bankdict[str(ctx.guild.id)].keys():
                rankings.append(MoneyMember(member, bankdict[str(ctx.guild.id)][member]))
            for i in range(len(rankings)):
                max_index = i
                for j in range(i + 1, len(rankings)):
                    if rankings[max_index].money < rankings[j].money:
                        max_index = j
                rankings[i], rankings[max_index] = rankings[max_index], rankings[i]
            msg = "```Wu points rankings:"
            for i in range(10):
                if i + 1 == 1:
                    msg += "\n1st: "
                elif i + 1 == 2:
                    msg += "\n2nd: "
                elif i + 1 == 3:
                    msg += "\n3rd: "
                else:
                    msg += f"\n{i + 1}th: "
                user = await self.client.fetch_user(rankings[i].id)
                msg += f"{user.display_name} -- {rankings[i].money}"
                if i == len(rankings) - 1:
                    break
            msg += "```"
            await ctx.send(msg)

    @commands.command(description="Shows the transaction logs of the current day.")
    async def logs(self, ctx):
        os.chdir("transfers")
        try:
            os.chdir(str(ctx.guild.id))
        except FileNotFoundError:
            await ctx.send("No logs from this server yet.")
            os.chdir("..")
            return
        today = date.today()
        try:
            logfile = open(today.strftime("%d%m%Y") + ".txt")
            num_lines = sum(1 for line in open(today.strftime("%d%m%Y") + ".txt"))
        except FileNotFoundError:
            await ctx.send("No logs from today.")
            os.chdir("..")
            os.chdir("..")
            return
        msg = "```"
        if num_lines > 20:
            for i in range(20):
                msg += logfile.readline()
            msg += "Only 20 lines printed to prevent verbosity; Contact owner for full logs."
        else:
            for line in logfile:
                msg += line
        logfile.close()
        os.chdir("..")
        os.chdir("..")
        msg += " ```"
        await ctx.send(msg)

    @commands.command(
        aliases=['spr', 'SPR', 'scissorspaperrock', 'paperrockscissors', 'rockpaperscissors', 'rockscissors'
                                                                                              'paper'],
        description="Play scissors paper rock against Big Bot. Winning will earn you half of your initial bet.\n"
                    "eg Kevin spr scissors 20")
    async def paperscissorsrock(self, ctx, answer, bet_amount):
        bet_amount = abs(int(bet_amount))
        comp = random.choice(['s', 'r', 'p'])
        answer = answer[0].lower()
        if answer not in ['s', 'r', 'p']:
            await ctx.send("Pick either Scissors, Paper or Rock.")
            return
        logger("Scissors paper rock called with: " + answer)
        result = -1
        msg = ""
        if comp == "s":
            msg += "I picked Scissors. "
        elif comp == "r":
            msg += "I picked Rock. "
        elif comp == "p":
            msg += "I picked Paper. "
        if answer == comp:
            msg += "Tie."
            result = 0
        else:
            if answer == "s":
                if comp == 'r':
                    msg += "I win."
                    result = 1
                elif comp == 'p':
                    msg += "You win."
                    result = 2
            elif answer == "r":
                if comp == 's':
                    msg += "You win."
                    result = 2
                elif comp == 'p':
                    msg += "I win."
                    result = 1
            elif answer == "p":
                if comp == 's':
                    msg += " I win."
                    result = 1
                elif comp == 'r':
                    msg += "You win."
                    result = 2
        if result != 0:
            bankdict = get_bank()
            user = await self.client.fetch_user(ctx.author.id)
            if result == 1:
                msg += f"\n You lost {bet_amount} Wu points."
                bankdict[str(ctx.guild.id)][str(ctx.author.id)] -= bet_amount
                transaction_logger(ctx.guild.id, user.display_name + f" lost {bet_amount} during a SPR game.")
            elif result == 2:
                bet_amount = math.floor(bet_amount / 2)
                msg += f"\n You won {bet_amount} Wu points."
                bankdict[str(ctx.guild.id)][str(ctx.author.id)] += bet_amount
                transaction_logger(ctx.guild.id, user.display_name + f" won {bet_amount} during a SPR game.")
            save_bank(bankdict)
        await ctx.send(msg)

    @commands.command(description="Guess the resulting number on a 6-sided dice roll.")
    async def dice(self, ctx, guess, bet_amount):
        guess = int(guess)
        if guess not in [1, 2, 3, 4, 5, 6]:
            await ctx.send("Invalid guess; Guess must be between 1 and 6 inclusive.")
            return
        bet_amount = abs(int(bet_amount))
        comp = random.randint(1, 6)
        bankdict = get_bank()
        user = await self.client.fetch_user(ctx.author.id)
        if guess == comp:
            await ctx.send(f"Dice: {comp}\nYour guess was correct. You won {bet_amount} Wu points.")
            bankdict[str(ctx.guild.id)][str(ctx.author.id)] += bet_amount
            transaction_logger(ctx.guild.id, f"{user.display_name} won {bet_amount} in a dice game.")
        else:
            await ctx.send(f"Dice: {comp}\nYour guess was incorrect. You lost {bet_amount} Wu points.")
            bankdict[str(ctx.guild.id)][str(ctx.author.id)] -= bet_amount
            transaction_logger(ctx.guild.id, f"{user.display_name} lost {bet_amount} in a dice game.")
        save_bank(bankdict)

    @commands.command(description="See the rewards you can purchase with your Wu points.")
    async def rewards(self, ctx):
        rewardsfile = open("rewards.txt")
        reward = json.load(rewardsfile)
        rewardsfile.close()
        msg = "```"
        for item in reward:
            msg += f"\n{item} -- {reward[item]}"
        msg += "```"
        await ctx.send(msg)

    @commands.command(description="Add a reward onto the Wu rewards. Only permitted by bank administrators.")
    async def addreward(self, ctx, price, *description):
        if ctx.author.id != self.botkeys["Lucasid"] and ctx.author.id != self.botkeys["Kevinid"]:
            await ctx.send("You do not have permissions to do that.")
            return
        price = int(price)
        rewardsfile = open("rewards.txt")
        reward = json.load(rewardsfile)
        rewardsfile.close()
        description = " ".join(description)
        reward[description] = price
        reward = sorted(reward.items(), key=lambda x: x[1], reverse=True)
        with open("rewards.txt", "w") as output:
            json.dump(reward, output)
        await ctx.send("New reward added. Do `Kevin rewards` to view them.")

    @commands.command(description="Remove a reward from the Wu rewards. Only permitted by bank administrators.")
    async def remreward(self, ctx, *description):
        if ctx.author.id != self.botkeys["Lucasid"] and ctx.author.id != self.botkeys["Kevinid"]:
            await ctx.send("You do not have permissions to do that.")
            return
        description = " ".join(description)
        rewardsfile = open("rewards.txt")
        reward = json.load(rewardsfile)
        rewardsfile.close()
        removed = reward.pop(description)
        with open("rewards.txt", "w") as output:
            json.dump(reward, output)
        await ctx.send(f"`{description}` was removed from the Wu rewards. View them with `Kevin rewards`.")


def setup(client):
    client.add_cog(MoneyCog(client))
