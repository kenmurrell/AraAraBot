import asyncio
import itertools
import logging
import os
from collections import deque
from typing import Dict, Any

import discord
from async_timeout import timeout
from discord.errors import ClientException
from discord.ext import commands
from discord.ext.commands.bot import Bot
from discord.ext.commands.context import Context

from musictools import Skip
from ytapi import YoutubeAPI, InvalidLinkError, YTDownloaderError, YTReturnedEmptyError

# DOCUMENTATION
DOCS_JOIN = "-> joins the user's voice channel"
DOCS_LEAVE = "-> leaves the current voice channel"
DOCS_PLAY = "-> plays the given youtube video or the first item in the queue"
DOCS_PAUSE = "-> pause/unpause the current song"
DOCS_QUEUE = "-> queues up the given song"
DOCS_CLEAR = "-> clears the queue"
DOCS_ORG = "-> ( ͡° ͜ʖ ͡°)"
DOCS_SKIP = "-> vote to skip the current song"
DOCS_LIST = "-> list all the songs currently in the queue"

# PATHS
DIR_PATH = os.path.dirname(os.path.realpath(__file__))
DL_DIR = os.path.join(DIR_PATH, "downloads")
SOUNDS_DIR = os.path.join(DIR_PATH, "sounds")
SOUND_ARA_ARA = os.path.join(SOUNDS_DIR, "ara_ara.mp3")
SOUND_ORG = os.path.join(SOUNDS_DIR, "org.mp3")

logger = logging.getLogger("bot")


class Music(commands.Cog):

    def __init__(self, bot: Bot, config: Dict[str, Any]):
        self.bot = bot
        self.config = config
        self.voice_client = None
        self.channel = None
        self.skip = Skip(int(config["SKIP_LIMIT"]))

        self.url_queue = deque()
        self.track_queue = asyncio.Queue(config["QUEUE_LIMIT"], loop=self.bot.loop)
        self.next_song_event = asyncio.Event()
        self.play_song_event = asyncio.Event()
        self.bot.loop.create_task(self.load_loop())
        self.bot.loop.create_task(self.player_loop())

        self.lock = asyncio.Lock()
        yt_dl_opts = config["YD_DL_OPTS"]
        yt_dl_opts["outtmpl"] = os.path.join(DL_DIR, '%(id)s.%(etx)s')
        yt_dl_opts["download_archive"] = os.path.join(DL_DIR, "archive.txt")
        self.yt_api = YoutubeAPI(yt_dl_opts, DL_DIR)

    @commands.command(name="org", aliases=["o"], pass_context=True, usage=DOCS_ORG)
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def org(self, ctx: Context):
        try:
            async with self.lock:  # abusing asyncio locks but shouldn't orgs break things?
                ctx.voice_client.play(discord.FFmpegPCMAudio(SOUND_ORG), after=None)
            logger.info("{user} requested org".format(user=ctx.message.author.name))
            await ctx.send(content=self.config["MESSAGES"]["ORG"])
        except ClientException as ex:
            logger.error("Error requesting org: {err}".format(err=ex))

    @commands.command(name="join", aliases=["j"], pass_context=True, usage=DOCS_JOIN)
    async def join(self, ctx: Context):
        await asyncio.sleep(1)
        ctx.voice_client.play(discord.FFmpegPCMAudio(SOUND_ARA_ARA), after=None)
        await ctx.send(content=self.config["MESSAGES"]["JOINING_VOICE"].format(channel=ctx.message.author.voice.channel))

    @commands.command(name="leave", aliases=["l"], pass_context=True, usage=DOCS_LEAVE)
    async def leave(self, ctx: Context):
        user = ctx.message.author
        voice_client = ctx.voice_client
        if not ctx.voice_client:
            logger.error("{user} requested leave but not in a voice channel".format(user=user.name))
            await ctx.send(content=self.config["ERRORS"]["BOT_NOT_IN_VCHANNEL"].format(user=user.name))
            return
        logger.info("{user} requested leave from {channel} channel".format(user=user.name, channel=ctx.voice_client.channel))
        await ctx.send(content=self.config["MESSAGES"]["LEAVING_VOICE"].format(channel=ctx.voice_client.channel))
        await voice_client.disconnect()

    @commands.command(name="play", aliases=["p"], pass_context=True, usage=DOCS_PLAY)
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def play(self, ctx: Context, *args):
        user = ctx.message.author
        if len(args) == 0:
            if self.track_queue.empty():
                logger.error("{user} requested play but no song given and queue empty".format(user=user.name))
                await ctx.send(content=self.config["ERRORS"]["NO_LINK_GIVEN"].format(user=user.name))
            else:
                self.play_song_event.set()
                logger.info("{user} started the queue".format(user=user.name))
        else:
            self.play_song_event.set()
            logger.info("{user} started the queue".format(user=user.name))
            for url in args:
                r = {"url": url, "channel": ctx.message.channel, "user": user}  # add multiple url handling here
                self.url_queue.append(r)
                logger.info("{user} queued url {url}".format(user=user.name, url=url))

    @commands.command(name="queue", aliases=["q"], pass_context=True, usage=DOCS_QUEUE)
    async def queue(self, ctx: Context, *args):
        user = ctx.message.author
        if len(args) == 0:
            logger.error("{user} requested queue but no song given".format(user=user.name))
            await ctx.send(content=self.config["ERRORS"]["NO_LINK_GIVEN"].format(user=user.name))
        for url in args:
            r = {"url": url, "channel": ctx.message.channel, "user": user}
            self.url_queue.append(r)
            logger.info("{user} queued url {url}".format(user=user.name, url=url))

    @commands.command(name="clear", aliases=["c"], pass_context=True, usage=DOCS_CLEAR)
    async def clear(self, ctx: Context):
        user = ctx.message.author
        logger.info("{user} requested clear queue".format(user=user.name))
        i = 0
        while not self.track_queue.empty():
            await self.track_queue.get()
            i += 1
        await ctx.send(content=self.config["MESSAGES"]["CLEARING"].format(size=i))
        logger.info("{user} requested clear, cleared {size} items from queue".format(user=user.name, size=i))

    @commands.command(name="pause", aliases=["v", "resume"], pass_context=True, usage=DOCS_PAUSE)
    async def pause(self, ctx: Context):
        user = ctx.message.author
        if not ctx.voice_client:
            logger.error("{user} requested pause".format(user=user.name))
            await ctx.send(content=self.config["ERRORS"]["BOT_NOT_IN_VCHANNEL"].format(user=user.name))
            return
        if ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            logger.info("{user} requested pause".format(user=user.name))
            await ctx.send(content=self.config["MESSAGES"]["PAUSING"])
        else:
            ctx.voice_client.resume()
            logger.info("{user} requested unpause".format(user=user.name))
            await ctx.send(content=self.config["MESSAGES"]["RESUMING"])

    @commands.command(name="skip", aliases=["s"], pass_context=True, usage=DOCS_SKIP)
    async def skip(self, ctx: Context):
        user = ctx.message.author
        if not ctx.voice_client.is_connected() or not ctx.voice_client.is_playing():
            logger.error("{user} requested skip but nothing is playing ".format(user=user.name))
        if self.skip.add(user.name):
            logger.info("{user} requested skip ({status})".format(user=user.name, status=self.skip.status()))
            await ctx.send(content=self.config["MESSAGES"]["SKIP_REQUEST"].format(user=user.name, status=self.skip.status()))
            if self.skip.ready():
                ctx.voice_client.stop()
                await self.next_song_event.wait()
                logger.info("vote limit reached, skipping song".format(user=user.name))
                await ctx.send(content=self.config["MESSAGES"]["SKIP_SUCCESS"])
                self.skip.clear()

    @commands.command(name="list", aliases=["x"], pass_context=True, usage=DOCS_LIST)
    async def list(self, ctx: Context):
        user = ctx.message.author
        logger.info("{user} requested list queue".format(user=user.name))
        if self.track_queue.empty():
            await ctx.send(content=self.config["MESSAGES"]["QUEUE_EMPTY"])
            return
        text = self.config["MESSAGES"]["QUEUELIST_HEADER"] + "\n"
        for i, track in enumerate(list(itertools.islice(self.track_queue._queue, 0, 10))):  # kinda gross but idgaf
            text += "Track {}: {}{}".format(i + 1, track.prettify(), "\n\n")
        text += self.config["MESSAGES"]["QUEUELIST_FOOTER"]
        await ctx.send(content=text)

    @org.before_invoke
    @join.before_invoke
    @play.before_invoke
    async def connect_voice(self, ctx):
        if not ctx.voice_client:
            user = ctx.message.author
            if not user.voice:
                err_text = "{user} requested action but not in a voice channel".format(user=user.name)
                logger.error(err_text)
                await ctx.send(content=self.config["ERRORS"]["USER_NOT_IN_VCHANNEL"].format(user=user.name))
                raise commands.CommandError(err_text)
            else:
                try:
                    await ctx.author.voice.channel.connect(timeout=10, reconnect=False)
                    logger.info("{user} requested join {channel}".format(channel=user.voice.channel, user=user.name))
                    self.voice_client = ctx.voice_client
                except commands.CommandError:
                    err_text = "{user} requested action but failed to join the voice channel".format(user=user.name)
                    logger.error("{user} requested action but failed to join the voice channel".format(user=user.name))
                    raise commands.CommandError(err_text)
        elif ctx.voice_client.is_playing():
            ctx.voice_client.stop()

    async def load_loop(self):
        while True:
            await asyncio.sleep(10)
            if len(self.url_queue) != 0:
                r = self.url_queue.popleft()  # could make this faster but there's no point
                self.channel = r["channel"]
                try:
                    tracks = await self.yt_api.create_tracks(r["url"])
                    for track in tracks:
                        if await self.yt_api.download_track(track):
                            await self.track_queue.put(track)
                            logger.info("successfully queued track {track}".format(track=track.details()))
                            await self.channel.send(content=self.config["MESSAGES"]["QUEUING"].format(user=r["user"].name, track=track.prettify()))
                except InvalidLinkError:
                    logger.error("Tried queuing {url} but  invalid link".format(url=r["url"]))
                    await self.channel.send(content=self.config["ERRORS"]["PLAYING_INVALID_LINK"].format(user=r["user"].name))
                except YTReturnedEmptyError:
                    logger.error("Tried queuing {url} but received an empty list from Youtube. This is often from "
                                 "downloading the same playlist too many times".format(url=r["url"]))
                    await self.channel.send(content=self.config["ERRORS"]["YOUTUBE_NULL_ERROR"].format(user=r["user"].name))
                except YTDownloaderError as ex:
                    logger.error("Tried queuing {url} but encountered a download error: {err}".format(url=r["url"], err=ex))

    async def player_loop(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            self.next_song_event.clear()
            if self.track_queue.empty():
                self.play_song_event.clear()
            await self.play_song_event.wait()
            try:
                async with timeout(300):
                    track = await self.track_queue.get()
            except asyncio.TimeoutError as ex:
                logger.error("Very scary asyncio.TimeoutError: {err}".format(err=str(ex)))
            source = discord.FFmpegPCMAudio(track.filename)
            async with self.lock:
                if not self.voice_client.is_connected():
                    await self.voice_client.connect(timeout=10, reconnect=False)
                self.skip.clear()
                self.voice_client.play(
                    source,
                    after=lambda _: self.bot.loop.call_soon_threadsafe(self.next_song_event.set))
                await self.channel.send(content=self.config["MESSAGES"]["PLAYING"].format(track=track.prettify()))
                logger.info("Now playing song {track}".format(track=track.details()))
                await self.next_song_event.wait()
            source.cleanup()
            await asyncio.sleep(5)
