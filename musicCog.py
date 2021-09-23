import discord
from discord.ext import commands
from discord.ext import tasks
import youtube_dl
from datetime import *
import requests
from lxml import html
from googleapiclient.discovery import build


def time():
    now = datetime.now()
    return now.strftime("[%H:%M:%S] --- ")


def logger(message):
    today = date.today()
    logfile = open(today.strftime("%d%m%Y") + ".txt", 'a', encoding='utf-8')
    logfile.write("\n" + time() + message)
    logfile.close()


class Song(object):
    def __init__(self, name, url):
        self.name = name
        self.url = url


class MusicCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.music_queue = {}
        self.check.start()
        self.FFMPEG_OPTIONS = {'before_options': ' -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                               'options': '-vn'}
        self.YDL_OPTIONS = {'format': 'bestaudio'}
        self.youtube = build('youtube', 'v3', developerKey="devkey")

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

    @commands.command(description="Play a video's audio from provided youtube link. If something is already playing,"
                                  "it will be queued.")
    @commands.cooldown(1, 3)
    async def play(self, ctx, *url):
        url = " ".join(url)
        if url[0:38] == "https://www.youtube.com/playlist?list=":
            await self.playlist(ctx, url)
            return
        if ctx.guild.id not in self.music_queue:
            self.music_queue[ctx.guild.id] = []
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
            page = requests.get(url)
            tree = html.fromstring(page.text)
            name = tree.xpath('//meta[@itemprop="name"]/@content')[0]
            song = Song(name, url)
            if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
                self.music_queue[ctx.guild.id].append(song)
                await ctx.send(
                    f"Queued as number {str(len(self.music_queue[ctx.guild.id]))} in queue.\nType `Kevin queue` to"
                    f" see your queue.")
                logger("Added to queue: " + song.name)
            else:
                vc = ctx.voice_client
                with youtube_dl.YoutubeDL(self.YDL_OPTIONS) as ydl:
                    info = ydl.extract_info(url, download=False)
                    url2 = info['formats'][0]['url']
                    source = await discord.FFmpegOpusAudio.from_probe(url2, **self.FFMPEG_OPTIONS)
                                                                      #executable=r"D:\Program Files\ffmpeg-2021-09-16-git-8f92a1862a-essentials_build\bin\ffmpeg.exe")
                    await ctx.send(f"Now playing {song.name}.")
                    vc.play(source)
                    logger("Playing: " + song.name)

    @tasks.loop(seconds=3.0)
    async def check(self):
        for vc in self.client.voice_clients:
            if vc.is_playing() is False:
                if vc.guild.id in self.music_queue and self.music_queue[vc.guild.id] != []:
                    url = self.music_queue[vc.guild.id].pop(0).url
                    with youtube_dl.YoutubeDL(self.YDL_OPTIONS) as ydl:
                        info = ydl.extract_info(url, download=False)
                        url2 = info['formats'][0]['url']
                        source = await discord.FFmpegOpusAudio.from_probe(url2, **self.FFMPEG_OPTIONS)
                                                                          #executable=r"D:\Program Files\ffmpeg-2021-09-16-git-8f92a1862a-essentials_build\bin\ffmpeg.exe")
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
                url = self.music_queue[ctx.guild.id].pop(0).url
                ctx.voice_client.stop()
                await self.play(ctx, url)

    @commands.command(description="Adds all videos in a youtube playlist to the queue.")
    async def playlist(self, ctx, url):
        if ctx.voice_client is None:
            await ctx.send("I must be connected to a voice channel first.")
        else:
            if url[0:38] == "https://www.youtube.com/playlist?list=":
                playlist_id = url[38:]
            else:
                await ctx.send("Invalid link. I suggest you do `Kevin help playlist`.")
                return
            request = self.youtube.playlistItems().list(
                part="snippet,contentDetails",
                maxResults=100,
                playlistId=playlist_id
            )
            response = request.execute()
            if ctx.guild.id not in self.music_queue:
                self.music_queue[ctx.guild.id] = []
            queue_list = [] # this is a workaround for the looped check() function to not trigger the bot to play when this function will try to play anyway.
            for item in response["items"]:
                song = Song(item['snippet']['title'], "https://www.youtube.com/watch?v=" + item["contentDetails"]["videoId"])
                queue_list.append(song)
            if ctx.voice_client.is_playing() is False:
                url = queue_list.pop(0).url
                await self.play(ctx, url)
            while queue_list:
                self.music_queue[ctx.guild.id].append(queue_list.pop(0))
            await ctx.send("Added " + str(len(response["items"])) + " songs to the queue.")

    @commands.command(aliases=['q'], description="Displays the current music queue.")
    async def queue(self, ctx):
        if ctx.guild.id not in self.music_queue or self.music_queue[ctx.guild.id] == []:
            msg = "There is nothing in your music queue."
        else:
            msg = ""
            for i in range(0, len(self.music_queue[ctx.guild.id])):
                msg += str(i + 1) + ": " + self.music_queue[ctx.guild.id][i].name + "\n"
        await ctx.send(msg)
        logger("Queue was printed as: \n" + msg)

    @commands.command(description="Removes a song from the music queue.")
    async def remove(self, ctx, index):
        index = int(index)
        if ctx.guild.id not in self.music_queue or self.music_queue[ctx.guild.id] == [] or len(self.music_queue[ctx.guild.id]) > index:
            msg = "There is nothing in your music queue."
        else:
            song = self.music_queue[ctx.guild.id].pop(index - 1)
            msg = "Removed song number " + str(index) + ": " + song.name + " from the queue."
        await ctx.send(msg)
        logger(msg)

    @commands.command(description="Stops the playing audio and clears the queue.")
    async def stop(self, ctx):
        if ctx.voice_client is None:
            await ctx.send("I must be connected to a voice channel first.")
        else:
            ctx.voice_client.stop()
            self.music_queue[ctx.guild.id] = []


def setup(client):
    client.add_cog(MusicCog(client))
