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


def transaction_logger(guild_id, message):  # separate log, for the logs command
    os.chdir(f"bank/{guild_id}/transfers")
    # no need to check if the directory exists, any function that uses it will have already checked
    today = date.today()
    logfile = open(today.strftime("%Y%m%d") + ".txt", 'a', encoding='utf-8')
    logfile.write("\n" + time() + message)
    logfile.close()
    os.chdir("..")
    os.chdir("..")
    os.chdir("..")


def logger(message):
    os.chdir("logs")
    today = date.today()
    logfile = open(today.strftime("%Y%m%d") + ".txt", 'a', encoding='utf-8')
    logfile.write("\n" + time() + message)
    logfile.close()
    os.chdir("..")


def get_bank(guild_id):
    try:
        bankfile = open(f"bank/{guild_id}/members.txt")
    except FileNotFoundError:
        return None
    bankdict = json.load(bankfile)
    bankfile.close()
    return bankdict


def save_bank(guild_id, bankdict):
    with open(f"bank/{guild_id}/members.txt", "w") as output:
        json.dump(bankdict, output)


def check_balance(guild_id, member_id):
    bankdict = get_bank(str(guild_id))
    return int(bankdict[str(member_id)]["balance"])


class MoneyMember:
    def __init__(self, id, money):
        self.id = id
        self.money = money


class MoneyCog(commands.Cog):
    def __init__(self, client):
        self.botkeys = Botkeys.get_keys()
        self.client = client
        self.salary.start()

    def cog_unload(self):
        self.salary.cancel()

    @commands.command(description="Initialises a bank for the server. Can only be run by bank administrators.")
    async def initbank(self, ctx):
        if ctx.author.id != self.botkeys["Lucasid"] and ctx.author.id != self.botkeys["Kevinid"]:
            await ctx.send("You do not have permission to do that.")
            return
        os.chdir("bank")
        try:
            os.mkdir(str(ctx.guild.id))
        except FileExistsError:
            await ctx.send("This server already has a bank allocated.")
            os.chdir("..")
            return
        os.chdir(str(ctx.guild.id))
        os.mkdir("transfers")
        membersfile = open("members.txt", "w")
        membersfile.write("{}")
        membersfile.close()
        rewardsfile = open("rewards.txt", "w")
        rewardsfile.write("{}")
        rewardsfile.close()
        os.chdir("..")
        os.chdir("..")
        await ctx.send("Bank has been initialised. You can now register members into the bank.")
        transaction_logger(ctx.guild.id, "Bank initialised for this server.")

    @commands.command(description="Adds a user to the bank, i.e. initialising a bank account."
                                  "Can only be run by bank administrators.")
    async def register(self, ctx, user: discord.Member):
        if ctx.author.id != self.botkeys["Lucasid"] and ctx.author.id != self.botkeys["Kevinid"]:
            await ctx.send("You do not have permission to do that.")
            return
        bankdict = get_bank(ctx.guild.id)
        if bankdict is None:
            await ctx.send("This server does not have a bank allocated.")
        if str(user.id) in bankdict.keys():
            await ctx.send("User already registered.")
        else:
            bankdict[str(user.id)] = {'balance': 0, 'salary-claimed': False}
            save_bank(ctx.guild.id, bankdict)
            await ctx.send("User registered.")

    @commands.command(description="Removes a user from the bank, i.e. deletes a bank account."
                                  "Can only be run by bank administrators.")
    async def unregister(self, ctx, user: discord.Member):
        if ctx.author.id != self.botkeys["Lucasid"] and ctx.author.id != self.botkeys["Kevinid"]:
            await ctx.send("You do not have permission to do that.")
            return
        bankdict = get_bank(ctx.guild.id)
        if bankdict is None:
            await ctx.send("This server does not have a bank allocated.")
            return
        if str(user.id) in bankdict.keys():
            amount = bankdict[str(user.id)]["balance"]
            bankdict.pop(str(user.id))
            await ctx.send(f"{user.display_name} with {amount} has been unregistered.")
            logger(f"{user.display_name} with {amount} has been unregistered.")
        else:
            await ctx.send("That user does not have a bank account.")
        save_bank(ctx.guild.id, bankdict)

    @commands.command(description="Adds users in a role to the bank, i.e. initialising a bank account."
                                  "Can only be ran by Kevin or Lucas.")
    async def massregister(self, ctx, role: discord.Role):
        if ctx.author.id != self.botkeys["Lucasid"] and ctx.author.id != self.botkeys["Kevinid"]:
            await ctx.send("You do not have permission to do that.")
            return
        bankdict = get_bank(ctx.guild.id)
        if bankdict is None:
            await ctx.send("This server does not have a bank allocated.")
            return
        counter = 0
        for member in role.members:
            if str(member.id) not in bankdict.keys():
                bankdict[str(member.id)] = {"balance": 0, "salary-claimed": False}
                counter += 1
        save_bank(ctx.guild.id, bankdict)
        await ctx.send("Registered " + str(counter) + " users to the bank.")

    @commands.command(aliases=['bal'], description="Gets the balance of the user.")
    async def balance(self, ctx):
        bankdict = get_bank(ctx.guild.id)
        if bankdict is None:
            await ctx.send("This server does not have a bank allocated.")
            return
        if str(ctx.author.id) not in bankdict.keys():
            await ctx.send("You have not been registered into the bank. Contact the bank administrators for more info.")
            return
        bal = bankdict[str(ctx.author.id)]["balance"]
        await ctx.send(f"Your current balance is {bal} Wu points.")

    @commands.command(aliases=['balof'], description="Gets the balance of a user.")
    async def balanceof(self, ctx, user: discord.Member):
        bankdict = get_bank(ctx.guild.id)
        if bankdict is None:
            await ctx.send("This server does not have a bank allocated.")
            return
        if str(user.id) not in bankdict.keys():
            await ctx.send(
                "They have not been registered into the bank. Contact the bank administrators for more info.")
            return
        bal = bankdict[str(user.id)]["balance"]
        await ctx.send(f"Their current balance is {bal} Wu points.")
        transaction_logger(ctx.guild.id, str(user.display_name) + "'s balance: " + str(bal))

    @commands.command(description="Give the given user x amount of Wu points. The Wu points will be taken from"
                                  " the author's balance, unless they are bank administrators.")
    async def pay(self, ctx, amount, user: discord.Member):
        amount = abs(int(amount))
        bankdict = get_bank(ctx.guild.id)
        if bankdict is None:
            await ctx.send("This server does not have a bank allocated.")
            return
        if str(ctx.author.id) not in bankdict.keys() or str(user.id) not in bankdict.keys():
            await ctx.send("You or the receiver have not been registered into the bank."
                           "Contact the bank administrators for more info.")
            return
        if ctx.author.id != self.botkeys["Lucasid"] and ctx.author.id != self.botkeys["Kevinid"] \
                and ctx.author.id != self.botkeys["Bigbotid"]:
            if check_balance(ctx.guild.id, ctx.author.id) - amount < 0:
                await ctx.send("You have insufficient Wu points.")
                return
            bankdict[str(ctx.author.id)]["balance"] -= amount
            await ctx.send(f"{amount} Wu points have been deducted from your account.")
        bankdict[str(user.id)]["balance"] += amount
        save_bank(ctx.guild.id, bankdict)
        await ctx.send(f"{amount} Wu points was transferred. Their balance is now "
                       f"{bankdict[str(user.id)]['balance']} Wu points")
        transaction_logger(ctx.guild.id, f"{ctx.author.display_name} paid {user.display_name} {amount} Wu points")

    @commands.command(aliases=["ded"], description="Deducts x amount of Wu points from a given user. Can only be used"
                                                   "by bank administrators. It is possible to go into the negatives.")
    async def deduct(self, ctx, amount, user: discord.Member):
        if ctx.author.id != self.botkeys["Lucasid"] and ctx.author.id != self.botkeys["Kevinid"] \
                and ctx.author.id != self.botkeys["Bigbotid"]:
            await ctx.send("You do not have permission to do that.")
            return
        amount = abs(int(amount))
        bankdict = get_bank(ctx.guild.id)
        if bankdict is None:
            await ctx.send("This server does not have a bank allocated.")
            return
        if str(user.id) not in bankdict.keys():
            await ctx.send("The user has not been registered into the bank. Contact the bank administrators for more"
                           " info.")
            return
        bankdict[str(user.id)]["balance"] -= amount
        save_bank(ctx.guild.id, bankdict)
        await ctx.send(f"{amount} Wu points was deducted. Their balance is now"
                       f" {bankdict[str(user.id)]['balance']} Wu points")
        transaction_logger(ctx.guild.id, f"{user.display_name}'s balance was deducted by {amount}, their balance is now"
                                         f" {bankdict[str(user.id)]['balance']} Wu points")

    @tasks.loop(hours=1)  # @tasks.loop(hours=1)
    async def salary(self):
        now = datetime.now()
        if now.strftime("%w%H") == "000":
            for guild_id in [guild.id async for guild in self.client.fetch_guilds()]:
                bankdict = get_bank(guild_id)
                if bankdict is None:
                    print("No bank was found for guild: " + str(guild_id))
                    continue
                else:
                    for member in bankdict.keys():
                        bankdict[member]["salary-claimed"] = False
                save_bank(guild_id, bankdict)
                logger("Salary is now claimable for members in guild: " + str(guild_id))

    @commands.command(aliases=[], description="Collects the weekly salary of Wu points.")
    async def claim(self, ctx):
        salary_amount = 50
        bankdict = get_bank(ctx.guild.id)
        if bankdict is None:
            await ctx.send("This server does not have a bank allocated.")
            return
        if str(ctx.author.id) not in bankdict.keys():
            await ctx.send("You are not registered in the server's bank. Contact bank administrators to be registered.")
            return
        if bankdict[str(ctx.author.id)]['salary-claimed'] is False:
            bankdict[str(ctx.author.id)]['salary-claimed'] = True
            bankdict[str(ctx.author.id)]['balance'] += salary_amount
            save_bank(ctx.guild.id, bankdict)
            await ctx.send(f"Salary has been claimed. Your balance is now {bankdict[str(ctx.author.id)]['balance']}.")
        else:
            await ctx.send("You have already claimed your salary. Salary claims reset every Saturday midnight ("
                           "Technically sunday).")

    @commands.command(aliases=['leader', 'lb'], description="Shows the rankings of the first 10 "
                                                            "users with the most Wu points.")
    async def leaderboard(self, ctx):
        bankdict = get_bank(ctx.guild.id)
        rankings = []
        if bankdict is None:
            await ctx.send("This server does not have a bank allocated.")
            return
        async with ctx.typing():
            for member in bankdict.keys():
                rankings.append(MoneyMember(member, bankdict[member]['balance']))
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
        os.chdir("bank")
        try:
            os.chdir(str(ctx.guild.id))
        except FileNotFoundError:
            await ctx.send("This server does not have a bank allocated.")
            os.chdir("..")
            return
        today = date.today()
        os.chdir("transfers")
        try:
            logfile = open(today.strftime("%Y%m%d") + ".txt")
            num_lines = sum(1 for line in open(today.strftime("%Y%m%d") + ".txt"))
        except FileNotFoundError:
            await ctx.send("No logs from today.")
            os.chdir("..")
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
        os.chdir("..")
        msg += " ```"
        await ctx.send(msg)

    @commands.command(
        aliases=['spr', 'SPR', 'scissorspaperrock', 'paperrockscissors', 'rockpaperscissors', 'rockscissors'
                                                                                              'paper'],
        description="Play scissors paper rock against Big Bot. Winning will earn you half of your initial bet.\n"
                    "eg Kevin spr scissors 20")
    async def paperscissorsrock(self, ctx, answer, bet_amount):
        bankdict = get_bank(ctx.guild.id)
        if bankdict is None:
            await ctx.send("This server does not have a bank allocated.")
            return
        elif str(ctx.author.id) not in bankdict.keys():
            await ctx.send("You are not registered in the server's bank. Contact bank administrators to be registered.")
            return
        bet_amount = abs(int(bet_amount))
        bal = check_balance(ctx.guild.id, ctx.author.id)
        if bal < bet_amount:
            await ctx.send(f"Not enough funds. You only have {bal} Wu points.")
            return
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
            if result == 1:
                msg += f"\n You lost {bet_amount} Wu points."
                bankdict[str(ctx.author.id)]["balance"] -= bet_amount
                transaction_logger(ctx.guild.id, ctx.author.display_name + f" lost {bet_amount} during a SPR game.")
            elif result == 2:
                bet_amount = math.floor(bet_amount / 2)
                msg += f"\n You won {bet_amount} Wu points."
                bankdict[str(ctx.author.id)]['balance'] += bet_amount
                transaction_logger(ctx.guild.id, ctx.author.display_name + f" won {bet_amount} during a SPR game.")
            save_bank(ctx.guild.id, bankdict)
        await ctx.send(msg)

    @commands.command(description="Guess the resulting number on a 6-sided dice roll.")
    async def dice(self, ctx, guess, bet_amount):
        bankdict = get_bank(ctx.guild.id)
        if bankdict is None:
            await ctx.send("This server does not have a bank allocated.")
            return
        elif str(ctx.author.id) not in bankdict.keys():
            await ctx.send("You are not registered in the server's bank. Contact bank administrators to be registered.")
            return
        bet_amount = abs(int(bet_amount))
        bal = check_balance(ctx.guild, ctx.author)
        if bal < bet_amount:
            await ctx.send(f"Not enough funds. You only have {bal} Wu points.")
            return
        guess = int(guess)
        if guess not in [1, 2, 3, 4, 5, 6]:
            await ctx.send("Invalid guess; Guess must be between 1 and 6 inclusive.")
            return
        comp = random.randint(1, 6)
        if guess == comp:
            await ctx.send(f"Dice: {comp}\nYour guess was correct. You won {bet_amount} Wu points.")
            bankdict[str(ctx.author.id)]['balance'] += bet_amount
            transaction_logger(ctx.guild.id, f"{ctx.author.display_name} won {bet_amount} in a dice game.")
        else:
            await ctx.send(f"Dice: {comp}\nYour guess was incorrect. You lost {bet_amount} Wu points.")
            bankdict[str(ctx.author.id)]['balance'] -= bet_amount
            transaction_logger(ctx.guild.id, f"{ctx.author.display_name} lost {bet_amount} in a dice game.")
        save_bank(ctx.guild.id, bankdict)

    @commands.command(description="See the rewards you can purchase with your Wu points.")
    async def rewards(self, ctx):
        try:
            rewardsfile = open(f"bank/{ctx.guild.id}/rewards.txt")
        except FileNotFoundError:
            await ctx.send("This server either has no bank allocated to it, or no rewards were found."
                           "If this is unexpected, contact bank administrators.")
            return
        reward = json.load(rewardsfile)
        rewardsfile.close()
        reward = sorted(reward.items(), key=lambda x: x[1], reverse=True)
        msg = "```"
        for item in reward:
            msg += f"\n{item[0]} -- {item[1]}"
        msg += "```"
        await ctx.send(msg)

    @commands.command(description="Add a reward onto the Wu rewards. Only permitted by bank administrators.")
    async def addreward(self, ctx, price, *description):
        if ctx.author.id != self.botkeys["Lucasid"] and ctx.author.id != self.botkeys["Kevinid"]:
            await ctx.send("You do not have permissions to do that.")
            return
        price = int(price)
        try:
            rewardsfile = open(f"bank/{ctx.guild.id}/rewards.txt")
        except FileNotFoundError:
            await ctx.send("This server either has no bank allocated to it, or no rewards were found."
                           "If this is unexpected, contact bank administrators.")
            return
        reward = json.load(rewardsfile)
        rewardsfile.close()
        description = " ".join(description)
        reward[description] = price
        with open(f"bank/{ctx.guild.id}/rewards.txt", "w") as output:
            json.dump(reward, output)
        await ctx.send("New reward added. Do `Kevin rewards` to view them.")

    @commands.command(description="Remove a reward from the Wu rewards. Only permitted by bank administrators.")
    async def remreward(self, ctx, *description):
        if ctx.author.id != self.botkeys["Lucasid"] and ctx.author.id != self.botkeys["Kevinid"]:
            await ctx.send("You do not have permissions to do that.")
            return
        description = " ".join(description)
        try:
            rewardsfile = open(f"bank/{ctx.guild.id}/rewards.txt")
        except FileNotFoundError:
            await ctx.send("This server either has no bank allocated to it, or no rewards were found."
                           "If this is unexpected, contact bank administrators.")
            return
        reward = json.load(rewardsfile)
        rewardsfile.close()
        reward.pop(description)
        with open(f"bank/{ctx.guild.id}/rewards.txt", "w") as output:
            json.dump(reward, output)
        await ctx.send(f"`{description}` was removed from the Wu rewards. View them with `Kevin rewards`.")


async def setup(client):
    await client.add_cog(MoneyCog(client))
