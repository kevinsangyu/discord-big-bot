import re
import random
from discord.ext import commands
from datetime import *
import os


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


def sequential_calc(equation):
    if isinstance(equation, str):
        equation = re.sub("[^0-9|.|\-|+|*|/|(|)]", "", equation)
        line = re.split(r"(-|\+|\*|/|\(|\))", equation)
        i = 0
        while i < len(line):
            if not line[i]:
                line.pop(i)
            else:
                i += 1
        return sequential_calc(line)
    elif isinstance(equation, list):
        while len(equation) > 1:
            if ")" in equation and "(" not in equation:
                return "Invalid syntax: No opening bracket to match closing bracket."
            elif "(" in equation and ")" not in equation:
                return "Invalid syntax: No closing bracket to match opening bracket."
            elif "(" in equation:
                opener = equation.index("(")
                for index, value in enumerate(equation):
                    if value == ")":
                        closer = index
                else:
                    newlist = []
                    for k in range(opener + 1, closer):
                        newlist.append(equation[k])
                    for k in range(opener + 1, closer + 1):
                        equation.pop(opener + 1)
                    equation[opener] = sequential_calc(newlist)
            elif "*" in equation: # order of operations is not correct
                index = equation.index("*")
                equation[index - 1] = float(equation[index - 1]) * float(equation[index + 1])
                del equation[index:index + 2]
            elif "/" in equation:
                index = equation.index("/")
                equation[index - 1] = float(equation[index - 1]) / float(equation[index + 1])
                del equation[index:index + 2]
            elif "+" in equation:
                index = equation.index("+")
                equation[index - 1] = float(equation[index - 1]) + float(equation[index + 1])
                del equation[index:index + 2]
            elif "-" in equation:
                index = equation.index("-")
                equation[index - 1] = float(equation[index - 1]) - float(equation[index + 1])
                del equation[index:index + 2]
        return str(equation[0])


class MathCog(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command(aliases=['randomint', 'randint'],
                      description="Chooses a random number between 1 and a given number.")
    async def number(self, ctx, upperlimit):
        negative = 0
        try:
            if int(upperlimit) < 0:
                upperlimit = abs(int(upperlimit))
                negative = 1
                result = random.randint(1, upperlimit)
            else:
                result = random.randint(1, int(upperlimit))
        except TypeError and ValueError as e:
            result = "Invalid input: {" + e + "}"
        if negative == 0:
            await ctx.send(str(result))
            logger("A random number between 1 and " + str(upperlimit) + ", with result: " + str(result))
        else:
            await ctx.send("-" + str(result))
            logger("A random number between 1 and -" + str(upperlimit) + ", with result: -" + str(result))

    @commands.command(description="Returns the diagonal value of two given side values.")
    async def pythag(self, ctx, sidevalue1, sidevalue2):
        logger("Pythag called with values " + sidevalue1 + " and " + sidevalue2)
        sidevalue1 = float(sidevalue1)
        sidevalue2 = float(sidevalue2)
        result = str((sidevalue1 ** 2 + sidevalue2 ** 2) ** 0.5)
        logger("Pythag answer: " + result)
        await ctx.send(result)

    @commands.command(description="Evaluates a simple mathematical equation, such as: \n(21/3)*4+4\nSo far, can handle "
                                  "brackets[()], multiplication[*], division[/], addition[+] and subtraction[-].")
    async def calc(self, ctx, *, eq):
        logger("Calc called with raw string: " + eq)
        ans = sequential_calc(eq)
        await ctx.send(ans)
        logger("Calc concluded with answer: " + str(ans))

    @commands.command(description="Converts farenheit to celcius.")
    async def ftoc(self, ctx, temp: float):
        await ctx.send(str((temp-32)*5/9) + u'\N{DEGREE SIGN}' + "C")


def setup(client):
    client.add_cog(MathCog(client))
