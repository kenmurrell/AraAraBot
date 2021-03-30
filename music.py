from discord.ext import commands
from discord.ext.commands.context import Context
from discord.ext.commands.bot import Bot
from discord.errors import ClientException
import logging
import os
import discord
import typing
from musictools import Playlist, Track, Skip
from ytdownloader import YTDownloader, InvalidLinkError, YTDownloaderError

# DOCUMENTATION
DOCS_JOIN = "-> joins the user's voice channel"
DOCS_LEAVE = "-> leaves the current voice channel"
DOCS_PLAY = "-> plays the given youtube video or the first item in the queue"
DOCS_PAUSE = "-> pause/unpause the current song"
DOCS_QUEUE = "-> queues up the given song"
DOCS_CLEAR = "-> clears the queue"
DOCS_ORG = "-> ( ͡° ͜ʖ ͡°)"
DOCS_SKIP = "-> vote to skip the current song"

# PATHS
DIR_PATH = os.path.dirname(os.path.realpath(__file__))
DL_DIR = os.path.join(DIR_PATH, "downloads")
SOUNDS_DIR = os.path.join(DIR_PATH, "sounds")
SOUND_ARA_ARA = os.path.join(SOUNDS_DIR, "ara_ara.mp3")
SOUND_ORG = os.path.join(SOUNDS_DIR, "org.mp3")

logger = logging.getLogger("bot")


class Music(commands.Cog):

    def __init__(self, bot: Bot, config: dict):
        self.bot = bot
        self.config = config
        self.playlist = Playlist(int(config["META"]["PLAYLIST_LIMIT"]))
        self.skip = Skip(int(config["META"]["SKIP_LIMIT"]))
        self.config["YD_DL_OPTS"]["outtmpl"] = os.path.join(DL_DIR, '%(id)s.%(etx)s')
        self.config["YD_DL_OPTS"]["download_archive"] = os.path.join(DL_DIR, "archive.txt")
        self.ytdl = YTDownloader(self.config["YD_DL_OPTS"], DL_DIR)

    @commands.command(name="org", aliases=["o"], pass_context=True, usage=DOCS_ORG)
    async def org(self, ctx: Context):
        voice_client = ctx.voice_client
        user = ctx.message.author.name
        if not voice_client:
            logger.error("{user} requested org but bot not in voice channel".format(user=user))
            await ctx.send(content=self.config["ERRORS"]["USER_NOT_IN_VCHANNEL"].format(user=user))
            return
        try:
            voice_client.play(discord.FFmpegPCMAudio(SOUND_ORG), after=None)
            logger.info("{user} requested org".format(user=user))
            await ctx.send(content=self.config["MESSAGES"]["ORG"])
        except ClientException as ex:
            logger.error("Error requesting org: {err}".format(err=ex))

    @commands.command(name="join", aliases=["j"], pass_context=True, usage=DOCS_JOIN)
    async def join(self, ctx: Context):
        user = ctx.message.author.name
        s_voice = ctx.message.author.voice
        if not s_voice:
            logger.error("{user} requested join to null channel".format(user=user))
            await ctx.send(content=self.config["ERRORS"]["USER_NOT_IN_VCHANNEL"].format(user=user))
            return
        s_channel = s_voice.channel
        voice_client = await s_channel.connect()
        voice_client.play(discord.FFmpegPCMAudio(SOUND_ARA_ARA), after=None)
        await ctx.send(content=self.config["MESSAGES"]["JOINING_VOICE"].format(channel=s_channel))
        logger.info("{user} requested join to {channel} channel".format(user=user, channel=s_channel))

    @commands.command(name="leave", aliases=["l"], pass_context=True, usage=DOCS_LEAVE)
    async def leave(self, ctx: Context):
        user = ctx.message.author.name
        voice_client = ctx.voice_client
        if not voice_client:
            logger.error("{user} requested leave a null channel".format(user=user))
            await ctx.send(content=self.config["ERRORS"]["BOT_NOT_IN_VCHANNEL"].format(user=user))
            return
        vchannel = voice_client.channel.name
        logger.info("{user} requested leave from {channel} channel".format(user=user, channel=vchannel))
        await voice_client.disconnect()
        await ctx.send(content=self.config["MESSAGES"]["LEAVING_VOICE"].format(channel=vchannel))

    @commands.command(name="play", aliases=["p"], pass_context=True, usage=DOCS_PLAY)
    async def play(self, ctx: Context, *args):
        user = ctx.message.author.name
        if not ctx.voice_client:
            logger.error("{user} requested play but bot not in voice channel".format(user=user))
            await ctx.send(content=self.config["ERRORS"]["USER_NOT_IN_VCHANNEL"].format(user=user))
            return
        if len(args) == 0:
            if len(self.playlist) == 0:
                logger.error("{user} requested play but no song given and playlist empty".format(user=user))
                await ctx.send(content=self.config["ERRORS"]["NO_LINK_GIVEN"].format(user=user))
            else:
                self._play_music(ctx, track=self.playlist.next())
        else:
            try:
                track = self._create_track(args[0])
                logger.info("{user} requested played song {trackdt}".format(user=user, trackdt=track.details()))
                self._play_music(ctx, track)
                await ctx.send(content=self.config["MESSAGES"]["PLAYING"].format(track=str(track)))
            except ClientException as ex:
                logger.error("Error requesting org: {err}".format(err=ex))
            except InvalidLinkError as ex:
                logger.error("{user} requested to play an invalid link".format(user=user))
                await ctx.send(content=self.config["ERRORS"]["PLAYING_INVALID_LINK"].format(user=user))
            except YTDownloaderError as ex:
                logger.error("Encountered a download error: {err}".format(err=ex))

    @commands.command(name="queue", aliases=["q"], pass_context=True, usage=DOCS_QUEUE)
    async def queue(self, ctx: Context, *args):
        user = ctx.message.author.name
        if len(args) == 0:
            logger.error("{user} requested queue but no song given".format(user=user))
            await ctx.send(content=self.config["ERRORS"]["NO_LINK_GIVEN"].format(user=user))
        try:
            track = self._create_track(args[0])
            self.playlist.add(track)
            logger.info("{user} queued song {trackdt}".format(user=user, trackdt=track.details()))
            await ctx.send(content=self.config["MESSAGES"]["QUEUING"].format(track=str(track)))
        except ClientException as ex:
            logger.error("Error requesting org: {err}".format(err=ex))
        except InvalidLinkError as ex:
            logger.error("{user} requested to play an invalid link".format(user=user))
            await ctx.send(content=self.config["ERRORS"]["PLAYING_INVALID_LINK"].format(user=user))
        except YTDownloaderError as ex:
            logger.error("Encountered a download error: {err}".format(err=ex))

    @commands.command(name="clearqueue", aliases=["c"], pass_context=True, usage=DOCS_CLEAR)
    async def clearqueue(self, ctx: Context):
        user = ctx.message.author.name
        self.playlist.clear()
        logger.info("{user} requested clear queue".format(user=user))
        await ctx.send(content=self.config["MESSAGES"]["CLEARING"])

    @commands.command(name="pause", pass_context=True, usage=DOCS_PAUSE)
    async def pause(self, ctx: Context):
        user = ctx.message.author.name
        voice_client = ctx.voice_client
        if not voice_client:
            logger.error("{user} requested pause".format(user=user))
            await ctx.send(content=self.config["ERRORS"]["BOT_NOT_IN_VCHANNEL"].format(user=user))
            return
        if voice_client.is_playing():
            voice_client.pause()
            logger.info("{user} requested pause".format(user=user))
            await ctx.send(content=self.config["MESSAGES"]["PAUSING"])
        else:
            voice_client.resume()
            logger.info("{user} requested unpause".format(user=user))
            await ctx.send(content=self.config["MESSAGES"]["RESUMING"])

    @commands.command(name="skip", aliases=["s"], pass_context=True, usage=DOCS_SKIP)
    async def skip(self, ctx: Context):
        user = ctx.message.author.name
        voice_client = ctx.voice_client
        if not voice_client or not voice_client.is_playing():
            return
        if self.skip.add(user):
            logger.info("{user} requested skip ({status})".format(user=user, status=self.skip.status()))
            await ctx.send(content=self.config["MESSAGES"]["SKIP_REQUEST"].format(user=user, status=self.skip.status()))
            if self.skip.ready():
                logger.info("Vote limit reached, skipping song".format(user=user))
                await ctx.send(content=self.config["MESSAGES"]["SKIP_SUCCESS"])
                if self.playlist.isempty():
                    voice_client.stop()
                else:
                    voice_client.stop()
                    self._play_music(ctx, self.playlist.next())

    def _play_music(self, ctx: Context, track: Track):

        def _after_playing(err=None):
            if len(self.playlist) > 0:
                self._play_music(ctx, self.playlist.next())

        self.skip.clear()
        voice_client = ctx.voice_client
        if not voice_client:
            # this method is sometimes called with a None client, idk y
            return
        logger.info("played song {trackdt}".format(trackdt=track.details()))
        voice_client.play(discord.FFmpegPCMAudio(track.filename), after=_after_playing)

    def _create_track(self, url: str):
        return self.ytdl.get(url)

