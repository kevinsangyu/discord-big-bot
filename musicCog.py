import discord
from discord.ext import commands
from discord.ext import tasks
import youtube_dl
from datetime import *
import requests


def time():
    now = datetime.now()
    return now.strftime("[%H:%M:%S] --- ")


def logger(message):
    today = date.today()
    logfile = open(today.strftime("%d%m%Y") + ".txt", 'a', encoding='utf-8')
    logfile.write("\n" + time() + message)
    logfile.close()


class MusicCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.music_queue = {}
        self.check.start()
        self.FFMPEG_OPTIONS = {'before_options': ' -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                               'options': '-vn'}
        self.YDL_OPTIONS = {'format': 'bestaudio'}

    def cog_unload(self):
        self.check.cancel()

    @commands.command(aliases=['connect'], description="The bot joins the voice channel of the sender.")
    async def join(self, ctx):
        if ctx.author.voice is None:
            await ctx.send("You need to be connected to a voice channel.")
            logger("Connection to voice channel failed.")
        channel = ctx.author.voice.channel
        if ctx.voice_client is None:
            await channel.connect()
            logger("Connected to voice channel.")
        else:
            await ctx.voice_client.move_to(channel)
            logger("Connected to voice channel.")

    @commands.command(aliases=['disconnect', 'quit'], description="The bot leaves the voice channel.")
    async def leave(self, ctx):
        await ctx.voice_client.disconnect()
        logger("Left voice channel.")

    @commands.command(aliases=['p'], description="Pause the playing audio.")
    async def pause(self, ctx):
        if ctx.voice_client is None:
            await ctx.send("I must be connected to a voice channel first.")
        else:
            ctx.voice_client.pause()

    @commands.command(aliase=['r'], description="Resumes the playing audio.")
    async def resume(self, ctx):
        if ctx.voice_client is None:
            await ctx.send("I must be connected to a voice channel first.")
        else:
            ctx.voice_client.resume()

    @commands.command(description="Play a video's audio from provided youtube link.")
    async def play(self, ctx, *url):
        if ctx.guild.id not in self.music_queue:
            self.music_queue[ctx.guild.id] = []
        url = " ".join(url)
        if ctx.voice_client is None:
            await ctx.send("I must be connected to a voice channel first.")
        else:
            if url[0:31] != "https://www.youtube.com/watch?v=":
                url = "https://www.youtube.com/results?search_query=" + url
                page = requests.get(url)
                content = str(page.content.decode('utf-8'))
                index = content.find('/watch?v=')
                counter = 5
                while True:
                    if content[index + counter] == '"':
                        break
                    else:
                        counter += 1
                url = "https://www.youtube.com" + content[index:index + counter]
            if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
                self.music_queue[ctx.guild.id].append(url)
                await ctx.send(
                    f"Queued as number {str(len(self.music_queue[ctx.guild.id]))} in queue.\nType `Kevin queue` to"
                    f" see your queue.")
                logger("Added to queue: " + url)
            else:
                vc = ctx.voice_client
                with youtube_dl.YoutubeDL(self.YDL_OPTIONS) as ydl:
                    info = ydl.extract_info(url, download=False)
                    url2 = info['formats'][0]['url']
                    source = await discord.FFmpegOpusAudio.from_probe(url2, **self.FFMPEG_OPTIONS)
                    vc.play(source)
                    logger("Playing: " + url)

    @tasks.loop(seconds=3.0)
    async def check(self):
        for vc in self.client.voice_clients:
            if vc.is_playing() is False:
                if vc.guild.id in self.music_queue and self.music_queue[vc.guild.id] != []:
                    url = self.music_queue[vc.guild.id].pop(0)
                    with youtube_dl.YoutubeDL(self.YDL_OPTIONS) as ydl:
                        info = ydl.extract_info(url, download=False)
                        url2 = info['formats'][0]['url']
                        source = await discord.FFmpegOpusAudio.from_probe(url2, **self.FFMPEG_OPTIONS)
                        vc.play(source)
                        logger("Playing: " + url)

    @commands.command(aliases=['s'], description="Skips to the next song in the queue.")
    async def skip(self, ctx):
        if ctx.voice_client is None:
            await ctx.send("I must be connected to a voice channel first.")
        else:
            if ctx.guild.id not in self.music_queue or self.music_queue[ctx.guild.id] == []:
                ctx.voice_client.stop()
            else:
                url = self.music_queue[ctx.guild.id].pop(0)
                ctx.voice_client.stop()
                await self.play(ctx, url)

    @commands.command(aliases=['q'], description="Displays the current music queue.")
    async def queue(self, ctx):
        if ctx.guild.id not in self.music_queue or self.music_queue[ctx.guild.id] == []:
            msg = "There is nothing in your music queue."
        else:
            msg = ""
            for i in range(0, len(self.music_queue[ctx.guild.id])):
                msg += str(i + 1) + ": " + self.music_queue[ctx.guild.id][i] + "\n"
            msg += "In the future, this list will be upgraded for readability."
        await ctx.send(msg)
        logger("Queue was printed as: \n" + msg)

    @commands.command(description="Stops the playing audio and clears the queue.")
    async def stop(self, ctx):
        if ctx.voice_client is None:
            await ctx.send("I must be connected to a voice channel first.")
        else:
            ctx.voice_client.stop()
            self.music_queue[ctx.guild.id] = []


def setup(client):
    client.add_cog(MusicCog(client))
