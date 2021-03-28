import logging
import os
import discord
import regex as re
import youtube_dl
from discord.errors import ClientException
from discord.ext import commands
from playlist import Playlist, Track

# DOCUMENTATION
DOCS_JOIN = "-> joins the user's voice channel"
DOCS_LEAVE = "-> leaves the current voice channel"
DOCS_PLAY = "-> plays the given youtube video or the first item in the queue"
DOCS_PAUSE = "-> pause/unpause the current playing video"
DOCS_QUEUE = "-> queues up the given youtube video"
DOCS_CLEAR = "-> clears the queue"
DOCS_ORG = "-> ( ͡° ͜ʖ ͡°)"

# PATHS
DIR_PATH = os.path.dirname(os.path.realpath(__file__))
DL_DIR = os.path.join(DIR_PATH, "downloads")
SOUNDS_DIR = os.path.join(DIR_PATH, "sounds")
SOUND_ARA_ARA = os.path.join(SOUNDS_DIR, "ara_ara.mp3")
SOUND_ORG = os.path.join(SOUNDS_DIR, "org.mp3")

logger = logging.getLogger("bot")
YT_PATTERN = re.compile("https\:\/\/www\.youtube\.com\/watch\?v\=[a-zA-Z0-9\-\_]{11}")


class Music(commands.Cog):

    def __init__(self, bot, config):
        self.bot = bot
        self.config = config
        self.playlist = Playlist(20)
        self.config["YD_DL_OPTS"]["outtmpl"] = os.path.join(DL_DIR, '%(id)s.%(etx)s')
        self.config["YD_DL_OPTS"]["download_archive"] = os.path.join(DL_DIR, "archive.txt")

    @commands.command(name="org", pass_context=True, usage=DOCS_ORG)
    async def org(self, ctx):
        voice_client = ctx.voice_client
        user = ctx.message.author.name
        if not voice_client:
            await ctx.send(content=self.config["ERRORS"]["USER_NOT_IN_VCHANNEL"].format(user=user))
            logger.error("{user} requested org but bot not in voice channel".format(user=user))
            return
        try:
            voice_client.play(discord.FFmpegPCMAudio(SOUND_ORG), after=None)
            await ctx.send(content=self.config["MESSAGES"]["ORG"])
            logger.info("{user} requested org".format(user=user))
        except ClientException as ex:
            logger.error("Error requesting org: {err}".format(err=ex))

    @commands.command(name="join", aliases=["j"], pass_context=True, usage=DOCS_JOIN)
    async def join(self, ctx):
        user = ctx.message.author.name
        s_voice = ctx.message.author.voice
        if not s_voice:
            await ctx.send(content=self.config["ERRORS"]["USER_NOT_IN_VCHANNEL"].format(user=user))
            logger.error("{user} requested join to null channel".format(user=user))
            raise HandledBotError("not in channel")
        s_channel = s_voice.channel
        voice_client = await s_channel.connect()
        voice_client.play(discord.FFmpegPCMAudio(SOUND_ARA_ARA), after=None)
        await ctx.send(content=self.config["MESSAGES"]["JOINING_VOICE"].format(channel=s_channel))
        logger.info("{user} requested join to {channel} channel".format(user=user, channel=s_channel))

    @commands.command(name="leave", aliases=["kick", "exit"], pass_context=True, usage=DOCS_LEAVE)
    async def leave(self, ctx):
        user = ctx.message.author.name
        voice_client = ctx.voice_client
        if not voice_client:
            await ctx.send(content=self.config["ERRORS"]["BOT_NOT_IN_VCHANNEL"].format(user=user))
            logger.error("{user} requested leave a null channel".format(user=user))
            return
        vchannel = voice_client.channel.name
        await voice_client.disconnect()
        await ctx.send(content=self.config["MESSAGES"]["LEAVING_VOICE"].format(channel=vchannel))
        logger.info("{user} requested leave from {channel} channel".format(user=user, channel=vchannel))

    @commands.command(name="play", aliases=["run", "pl"], pass_context=True, usage=DOCS_PLAY)
    async def play(self, ctx, *args):
        user = ctx.message.author.name
        voice_client = ctx.voice_client
        if not ctx.voice_client:
            await ctx.send(content=self.config["ERRORS"]["USER_NOT_IN_VCHANNEL"].format(user=user))
            logger.error("{user} requested play but bot not in voice channel".format(user=user))
            return
        if len(args) == 0 and len(self.playlist) == 0:
            await ctx.send(content=self.config["ERRORS"]["EMPTY_QUEUE"].format(user=user))
            logger.error("{user} requested play but no song and playlist empty".format(user=user))
        elif len(self.playlist) > 0:
            self._play_music(ctx, voice_client, track=self.playlist.next())
        else:
            try:
                track = self._create_track(args[0])
                logger.info("{user} played song {trackdt}".format(user=user, trackdt=track.details()))
                self._play_music(ctx, voice_client, track)
                await ctx.send(content=self.config["MESSAGES"]["PLAYING"].format(track=str(track)))
            except ClientException as ex:
                logger.error("Error requesting org: {err}".format(err=ex))
            except InvalidLinkError as ex:
                logger.error("{user} requested to play an invalid link".format(user=user))
                await ctx.send(content=self.config["ERRORS"]["PLAYING_INVALID_LINK"].format(user=user))
            except YTDownloadError as ex:
                logger.error("Encountered a download error: {err}".format(err=ex))

    @commands.command(name="queue", aliases=["q", "next"], pass_context=True, usage=DOCS_QUEUE)
    async def queue(self, ctx, *args):
        user = ctx.message.author.name
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
        except YTDownloadError as ex:
            logger.error("Encountered a download error: {err}".format(err=ex))

    @commands.command(name="clearqueue", aliases=["cq"], pass_context=True, usage=DOCS_CLEAR)
    async def clearqueue(self, ctx):
        user = ctx.message.author.name
        self.playlist.clear()
        logger.info("{user} requested clear queue".format(user=user))
        await ctx.send(content=self.config["MESSAGES"]["CLEARING"])

    @commands.command(name="pause", aliases=["st", "stop", "yamete"], pass_context=True, usage=DOCS_PAUSE)
    async def pause(self, ctx):
        user = ctx.message.author.name
        voice_client = ctx.voice_client
        if not voice_client:
            await ctx.send(content=self.config["ERRORS"]["BOT_NOT_IN_VCHANNEL"].format(user=user))
            logger.error("{user} requested pause".format(user=user))
            return
        if voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.send(content=self.config["MESSAGES"]["PAUSING"])
            logger.info("{user} requested pause".format(user=user))
        else:
            await ctx.send(content=self.config["MESSAGES"]["RESUMING"])
            ctx.voice_client.resume()
            logger.info("{user} requested unpause".format(user=user))

    def _play_music(self, ctx, voice_client, track):
        def after_playing(err):
            if len(self.playlist) > 0:
                self._play_music(ctx, voice_client, self.playlist.next())

        # await ctx.send(content=self.config["MESSAGES"]["PLAYING"].format(track=str(track)))
        voice_client.play(discord.FFmpegPCMAudio(track.filename), after=after_playing)

    def _create_track(self, url):
        if not YT_PATTERN.match(url):
            raise YTDownloadError("Invalid youtube link provided")
        try:
            with youtube_dl.YoutubeDL(self.config["YD_DL_OPTS"]) as ydl:
                info_dict = ydl.extract_info(url, download=False)
                video_id = info_dict.get("id", None)
                video_title = info_dict.get("title", None)
                video_duration = info_dict.get("duration", None)
                ydl.download([url])
                video_path = os.path.join(DL_DIR, "{}.{}".format(video_id, "mp3"))
                track = Track(video_id, video_title, url, video_duration, video_path)
                return track
        except youtube_dl.DownloadError as ex:
            raise YTDownloadError("Downloading error: " + str(ex))


class YTDownloadError(Exception):
    pass


class InvalidLinkError(Exception):
    pass


class HandledBotError(Exception):
    pass
