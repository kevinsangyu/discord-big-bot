import json
import urllib.request
import urllib.parse
import discord
from discord.ext import commands
from datetime import *
import Botkeys
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


class TranslateCog(commands.Cog):
    def __init__(self, client):
        self.botkeys = Botkeys.get_keys()
        self.client = client

    @commands.command(description="Translates a given string to english. Only supports 13 languages:\n"
                                  "korean, english, japanese, traditional chinese, simplified chinese, vietnamese, "
                                  "indonesian, thai, german, russian, spanish, italian and french.")
    async def translate(self, ctx, *, sentence):
        data = "query=" + urllib.parse.quote(sentence)
        request = urllib.request.Request("https://openapi.naver.com/v1/papago/detectLangs")
        request.add_header("X-Naver-Client-Id", self.botkeys["translate_id"])
        request.add_header("X-Naver-Client-Secret", self.botkeys["translate_secret"])
        response = urllib.request.urlopen(request, data=data.encode("utf-8"))
        rescode = response.getcode()
        if rescode == 200:
            response_body = response.read()
            srclang = json.loads(response_body.decode('utf-8'))["langCode"]
            logger("Translate command: Given sentence is in: " + srclang)
        else:
            await ctx.send("Error Code:" + rescode)
            logger("Error Code: " + rescode)
            return
        data = "source=" + srclang + "&target=en&text=" + urllib.parse.quote(sentence)
        request = urllib.request.Request("https://openapi.naver.com/v1/papago/n2mt")
        request.add_header("X-Naver-Client-Id", self.botkeys["translate_id"])
        request.add_header("X-Naver-Client-Secret", self.botkeys["translate_secret"])
        response = urllib.request.urlopen(request, data=data.encode("utf-8"))
        rescode = response.getcode()
        if rescode == 200:
            response_body = response.read()
            output = response_body.decode('utf-8')
            output = json.loads(output)
            await ctx.send(output["message"]["result"]["srcLangType"] + " to " +
                           output["message"]["result"]["tarLangType"] + ": " + output["message"]["result"][
                               "translatedText"])
            logger(output["message"]["result"]["srcLangType"] + " to " + output["message"]["result"]["tarLangType"])
        else:
            await ctx.send("Error Code:" + rescode)
            logger("Error Code: " + rescode)
            return


def setup(client):
    client.add_cog(TranslateCog(client))
