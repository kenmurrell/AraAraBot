import discord
import youtube_dl
import asyncio
from discord.ext import commands
from discord.errors import ClientException
import os
import sys
import logging
from datetime import datetime
import typing
import yaml
import regex as re
from playlist import Playlist, Track

#LOGGING
logger = logging.getLogger('main')
fileHandler = logging.FileHandler('{:%Y-%m-%d}.log'.format(datetime.now()))
formatter = logging.Formatter('%(asctime)s | %(levelname)-8s | %(lineno)04d | %(message)s')
fileHandler.setFormatter(formatter)
logger.addHandler(fileHandler)
streamHandler = logging.StreamHandler(sys.stdout)
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)
logger.setLevel(logging.INFO)

yaml_ob = None
with open("config.yaml", encoding="utf-8") as configfile:
    yaml_ob = yaml.load(configfile, Loader=yaml.FullLoader)

#PATHS
DIR_PATH = os.path.dirname(os.path.realpath(__file__))
DL_DIR = os.path.join(DIR_PATH, "downloads")
CACHE_DIR = os.path.join(DIR_PATH, "cache")
SOUNDS_DIR = os.path.join(DIR_PATH, "sounds")
SOUND_ARA_ARA = os.path.join(SOUNDS_DIR,"ara_ara.mp3")
SOUND_ORG = os.path.join(SOUNDS_DIR,"org.mp3")

#TOKEN
TOKEN = yaml_ob["AUTH"]["TOKEN"]

#DOCS
DOCS_JOIN = yaml_ob["DOCS"]["JOIN"]
DOCS_LEAVE = yaml_ob["DOCS"]["LEAVE"]
DOCS_PLAY =  yaml_ob["DOCS"]["PLAY"]
DOCS_PAUSE = yaml_ob["DOCS"]["PAUSE"]
DPCS_ORG = yaml_ob["DOCS"]["ORG"]

#MESSAGES
MSG_JOINING_VOICE = yaml_ob["MESSAGES"]["JOINING_VOICE"]
MSG_LEAVING_VOICE = yaml_ob["MESSAGES"]["LEAVING_VOICE"]
MSG_PLAYING = yaml_ob["MESSAGES"]["PLAYING"]
MSG_PAUSING = yaml_ob["MESSAGES"]["PAUSING"]
MSG_RESUMING = yaml_ob["MESSAGES"]["RESUMING"]
MSG_ORG = yaml_ob["MESSAGES"]["ORG"]

#ERRORS
ERROR_USER_NOT_IN_VCHANNEL = yaml_ob["ERRORS"]["USER_NOT_IN_VCHANNEL"]
ERROR_BOT_NOT_IN_VCHANNEL = yaml_ob["ERRORS"]["BOT_NOT_IN_VCHANNEL"]
ERROR_PLAYING_INVALID_LINK = yaml_ob["ERRORS"]["PLAYING_INVALID_LINK"]

#YOUTUBE DOWNLOADER OPTIONS
YD_DL_OPTS = yaml_ob["YD_DL_OPTS"]
YD_DL_OPTS["outtmpl"] = os.path.join(DL_DIR, '%(id)s.%(etx)s')
YD_DL_OPTS["download_archive"] = os.path.join(DL_DIR, "archive.txt")

YT_PATTERN = re.compile("https\:\/\/www\.youtube\.com\/watch\?v\=[a-zA-Z0-9\-\_]{11}")
playlist = Playlist(20)
bot = commands.Bot(command_prefix = "!")


@bot.event
async def on_ready():
    logger.info("Bot online!")


@bot.event
async def on_member_join(user):
  logger.info("{user} joined the server".format(user=user))


@bot.command(name="org", pass_context=True, usage=DPCS_ORG)
async def org(ctx):
    voice_client = ctx.voice_client
    user = ctx.message.author.name
    if not voice_client:
        return
    try:
        voice_client.play(discord.FFmpegPCMAudio(SOUND_ORG), after=None)
        await ctx.send(content=MSG_ORG)
        logger.info("{user} requested org".format(user=user))
    except ClientException as ex:
        logger.error("Error requesting org: {err}".format(err=ex))


@bot.command(name="join", aliases=["j"], pass_context=True, usage=DOCS_JOIN)
async def join(ctx):
    user = ctx.message.author.name
    s_voice =  ctx.message.author.voice
    if not s_voice:
        await ctx.send(content=ERROR_USER_NOT_IN_VCHANNEL.format(user=user))
        logger.error("{user} requested join to null channel".format(user=user))
        return
    s_channel = s_voice.channel
    voice_client = await s_channel.connect()
    voice_client.play(discord.FFmpegPCMAudio(SOUND_ARA_ARA), after=None)
    await ctx.send(content=MSG_JOINING_VOICE.format(channel=s_channel))
    logger.info("{user} requested join to {channel} channel".format(user=user, channel=s_channel))


@bot.command(name="leave", aliases=["kick", "exit"], pass_context=True, usage=DOCS_LEAVE)
async def leave(ctx):
    user = ctx.message.author.name
    voice_client = ctx.voice_client
    if not voice_client:
        await ctx.send(content=ERROR_BOT_NOT_IN_VCHANNEL.format(user=user))
        logger.error("{user} requested leave a null channel".format(user=user))
        return
    vchannel = voice_client.channel.name
    await voice_client.disconnect()
    await ctx.send(content=MSG_LEAVING_VOICE.format(channel=vchannel))
    logger.info("{user} requested leave from {channel} channel".format(user=user, channel=vchannel))


@bot.command(name="play", aliases=["run", "pl"], pass_context=True, usage=DOCS_PLAY)
async def play(ctx, *args):
    user = ctx.message.author.name
    if len(args) != 1 or not YT_PATTERN.match(args[0]):
        await ctx.send(content=ERROR_PLAYING_INVALID_LINK.format(user=user))
        logger.error("{user} requested to play a null link".format(user=user))
        return
    voice_client = ctx.voice_client
    if not ctx.voice_client:
        await ctx.send(content=ERROR_USER_NOT_IN_VCHANNEL.format(user=user))
        logger.error("{user} requested play but not in voice channel".format(user=user))
        return
    try:
        track = create_track(args[0])
        voice_client.play(discord.FFmpegPCMAudio(track.filename), after=None)
        await ctx.send(content=MSG_PLAYING.format(track=str(track)))
        logger.info("{user} requested song {trackdt}".format(user=user, trackdt=track.details()))
    except ClientException as ex:
        logger.error("Error requesting org: {err}".format(err=ex))


def create_track(url):
    try:
        with youtube_dl.YoutubeDL(YD_DL_OPTS) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            video_id = info_dict.get("id", None)
            video_title = info_dict.get("title", None)
            video_duration = info_dict.get("duration", None)
            ydl.download([url])
            video_path = os.path.join(DL_DIR, "{}.{}".format(video_id, "mp3"))
            track = Track(video_id, video_title, url, video_duration, video_path)
            return track
    except youtube_dl.DownloadError as ex:
        logger.error("Error requesting org: {err}".format(err=ex))


@bot.command(name="pause", aliases=["st", "stop", "yamete"], pass_context=True, usage=DOCS_PAUSE)
async def pause(ctx):
    user = ctx.message.author.name
    voice_client = ctx.voice_client
    if not voice_client:
        await ctx.send(content=ERROR_BOT_NOT_IN_VCHANNEL.format(user=user))
        logger.error("{user} requested pause".format(user=user))
        return
    if voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send(content=MSG_PAUSING)
        logger.info("{user} requested pause".format(user=user))
    else:
        await ctx.send(content=MSG_RESUMING)
        ctx.voice_client.resume()
        logger.info("{user} requested unpause".format(user=user))


bot.run(TOKEN)
