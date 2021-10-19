import random
import discord
from discord.ext import tasks, commands
import youtube_dl
from datetime import *
from googleapiclient.discovery import build
import os
import Botkeys


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


class Song(object):
    def __init__(self, name, url):
        self.name = name
        self.url = url


class MusicCog(commands.Cog):
    def __init__(self, client):
        self.botkeys = Botkeys.get_keys()
        self.client = client
        self.music_queue = {}
        self.check.start()
        self.FFMPEG_OPTIONS = {'before_options': ' -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                               'options': '-vn'}
        self.YDL_OPTIONS = {'format': 'bestaudio'}
        self.youtube = build('youtube', 'v3', developerKey=self.botkeys["Youtube"])

    def cog_unload(self):
        self.check.cancel()

    @commands.command(aliases=['connect'], description="The bot joins the voice channel of the sender.")
    async def join(self, ctx):
        if ctx.author.voice is None:
            await ctx.send("You need to be connected to a voice channel.")
        else:
            channel = ctx.author.voice.channel
            if ctx.voice_client is None:
                await channel.connect()
            else:
                await ctx.voice_client.move_to(channel)
            logger("Connected to voice channel.")

    @commands.command(aliases=['disconnect', 'quit', 'fuckoff', 'fuck off'], description="The bot leaves the voice channel.")
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
    async def play(self, ctx, *url):  # list index out of range error somewhere when a video link is provided.
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
                request = self.youtube.search().list(
                    part="id",
                    maxResults=1,
                    q=url
                )
                response = request.execute()
                url = "https://www.youtube.com/watch?v=" + response['items'][0]['id']['videoId']
            else:
                if '&' in url:  # sometimes the link fails to work because there's extra info about uploaders and stuff.
                    url = url[:url.find("&")]
            request = self.youtube.videos().list(
                part='snippet',
                id=url[32:]
            )
            response = request.execute()
            name = response['items'][0]['snippet']['title']
            song = Song(name, url)
            async with ctx.typing():
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
                        source = await discord.FFmpegOpusAudio.from_probe(url2, **self.FFMPEG_OPTIONS)  #, executable=self.botkeys['ffmpegPATH'])
                        await ctx.send(f"Now playing {song.name}.")
                        vc.play(source)
                        logger("Playing: " + song.name)

    @tasks.loop(seconds=5.0)
    async def check(self):
        for vc in self.client.voice_clients:
            if vc.is_playing() is False and vc.is_paused() is False:
                if vc.guild.id in self.music_queue and self.music_queue[vc.guild.id] != []:
                    song = self.music_queue[vc.guild.id].pop(0)
                    with youtube_dl.YoutubeDL(self.YDL_OPTIONS) as ydl:
                        info = ydl.extract_info(song.url, download=False)
                        url2 = info['formats'][0]['url']
                        source = await discord.FFmpegOpusAudio.from_probe(url2, **self.FFMPEG_OPTIONS)  #, executable=self.botkeys['ffmpegPATH'])
                        try:
                            vc.play(source)
                        except discord.errors.ClientException:
                            self.music_queue[vc.guild.id].insert(0, song)
                            print("Already playing, skip check cancelled.")
                        logger("Playing: " + song.name)

    @commands.command(aliases=['s'], description="Skips to the next song in the queue.")
    async def skip(self, ctx):
        vc = ctx.voice_client
        if vc is None:
            await ctx.send("I must be connected to a voice channel first.")
        else:
            vc.stop()
            if ctx.guild.id in self.music_queue and self.music_queue[ctx.guild.id]:
                song = self.music_queue[ctx.guild.id].pop(0)
                with youtube_dl.YoutubeDL(self.YDL_OPTIONS) as ydl:
                    info = ydl.extract_info(song.url, download=False)
                    url2 = info['formats'][0]['url']
                    source = await discord.FFmpegOpusAudio.from_probe(url2, **self.FFMPEG_OPTIONS)  #, executable=self.botkeys['ffmpegPATH'])
                    vc.play(source)
                    await ctx.send(f"Now playing {song.name}.")
                    logger("Playing: " + song.name)

    @commands.command(aliases=['st'], description="Skips to the specified song in the queue. Removes all songs before"
                                                  " said song form the queue.")
    async def skipto(self, ctx, index):  # kind of broken right now, since the skipping takes a while and the check loop kicks in before it starts playing.
        if ctx.voice_client is None:
            await ctx.send("I must be connected to a voice channel first.")
        else:
            index = int(index)
            if index > len(self.music_queue[ctx.guild.id]) or index <= 0:
                await ctx.send("Invalid index.")
                return
            else:
                self.music_queue[ctx.guild.id] = self.music_queue[ctx.guild.id][index-1:]
                await self.skip(ctx)

    @commands.command(description="Adds all videos in a youtube playlist to the queue.")
    @commands.cooldown(1, 10)
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

    @commands.command(description="Removes a song or songs from the music queue. If removing multiple, separate the "
                                  "two numbers with a space or comma.")
    async def remove(self, ctx, *index):
        index = " ".join(index)
        try:
            index = int(index)
        except ValueError:
            digits = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
            start = -1
            end = -1
            for i in range(0, len(index)):
                if index[i] not in digits and start == -1:
                    start = i
                if index[i] in digits and start != -1:
                    end = i
            numbers = index[start:end]
            numbers = index.split(numbers)
            index = []
            for number in numbers:
                index.append(int(number))
        testlist = []
        testint = 0
        if type(index) == type(testlist):
            if len(index) > 2:
                await ctx.send("Invalid input. I suggest you do `Kevin help remove`.")
                return
            else:
                start = index[0]
                end = index[1]
                for i in range(0, end-start+1):
                    await self.remove(ctx, str(end - i))
        elif type(index) == type(testint):
            if ctx.guild.id not in self.music_queue or self.music_queue[ctx.guild.id] == []:
                msg = "There is nothing in your music queue."
            elif len(self.music_queue[ctx.guild.id]) < index:
                msg = "Invalid index. I suggest you do `Kevin help remove`."
            else:
                song = self.music_queue[ctx.guild.id].pop(index - 1)
                msg = "Removed song number " + str(index) + ": " + song.name + " from the queue."
            await ctx.send(msg)
            logger(msg)

    @commands.command(description="Shuffles the queue.")
    async def shuffle(self, ctx):
        if ctx.guild.id not in self.music_queue or not self.music_queue[ctx.guild.id]:
            await ctx.send("There is nothing in your music queue.")
        else:
            copy_list = []
            for song in self.music_queue[ctx.guild.id]:
                copy_list.append(song)
            self.music_queue[ctx.guild.id] = []
            for i in range(0, len(copy_list)):
                song = copy_list.pop(random.randint(0, len(copy_list)-1))
                self.music_queue[ctx.guild.id].append(song)
            await ctx.send("Queue has been shuffled.")
            logger("Queue shuffled.")

    @commands.command(description="Stops the playing audio and clears the queue.")
    async def stop(self, ctx):
        if ctx.voice_client is None:
            await ctx.send("I must be connected to a voice channel first.")
        else:
            ctx.voice_client.stop()
            self.music_queue[ctx.guild.id] = []


def setup(client):
    client.add_cog(MusicCog(client))
