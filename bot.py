import discord
import youtube_dl
import asyncio
from discord.ext import commands
from discord.errors import ClientException
import random as rand # using this because of weird abiguity
import os
import sys
import logging
from datetime import datetime
import typing
import yaml
import regex as re


logger = logging.getLogger('main')
fileHandler = logging.FileHandler('{:%Y-%m-%d}.log'.format(datetime.now()))
formatter = logging.Formatter('%(asctime)s | %(levelname)-8s | %(lineno)04d | %(message)s')
fileHandler.setFormatter(formatter)
logger.addHandler(fileHandler)
streamHandler = logging.StreamHandler(sys.stdout)
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)
logger.setLevel(logging.INFO)

YT_PATTERN = re.compile("https\:\/\/www\.youtube\.com\/watch\?v\=[a-zA-Z0-9\-\_]{11}")
bot = commands.Bot(command_prefix = "!")
DIR_PATH = os.path.dirname(os.path.realpath(__file__))

TOKEN = None
with open("config.yaml") as configfile:
    try:
        yaml_ob = yaml.load(configfile, Loader=yaml.FullLoader)
        TOKEN = yaml_ob["TOKEN"]
    except KeyError:
        logger.error("Discord key not found, exiting")


#SOUNDS
SOUNDS_DIR = os.path.join(DIR_PATH, "sounds")
SOUND_ARA_ARA = os.path.join(SOUNDS_DIR,"ara_ara.mp3")
SOUND_ORG = os.path.join(SOUNDS_DIR,"org.mp3")

#DOWNLOADS
DL_DIR = os.path.join(DIR_PATH, "downloads")
CACHE_DIR = os.path.join(DIR_PATH, "cache")

USAGE_JOIN_CMD = "-> join the user's voice channel"
USAGE_LEAVE_CMD = "-> leave the current voice channel"
USAGE_PLAY_CMD =  "-> play the audio from a youtube video"
USAGE_PAUSE_CMD = "-> pause/unpause the current playing video"
USAGE_ORG_CMD = "-> ( ͡° ͜ʖ ͡°)"

#MESSAGES
MSG_JOINING_VOICE = "Joining the {channel} channel ＼(^ω^＼)"
MSG_LEAVING_VOICE = "Leaving the {channel} channel（ミ￣ー￣ミ)"
MSG_PLAYING = "Playing... (ﾉ◕ヮ◕)ﾉ*:･ﾟ✧ \n{title}"
MSG_PAUSING = "Paused... (/ω＼)	"
MSG_RESUMING = "Resuming... °˖✧◝(⁰▿⁰)◜✧˖°	"
MSG_ORG = "♡ σ(≧ε≦σ) ♡"

ERROR_USER_NOT_IN_VCHANNEL = "{user}-chan, baka! You're not in a voice channel! ( ╥ω╥ )"
ERROR_BOT_NOT_IN_VCHANNEL = "{user}-chan, baka! I'm not in a voice channel! ( ╥ω╥ )"
ERROR_PLAYING_INVALID_LINK = "{user}-chan, baka! I cannot play invalid youtube links! ( ╥ω╥ )"

YDL_OPTS = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    "retries": 3,
    "restrict-filenames": True,
    "cache-dir": CACHE_DIR,
    "no-playlist": True,
    'outtmpl': os.path.join(DL_DIR, '%(id)s.%(etx)s'),
    'quiet': False
}


@bot.event
async def on_ready():
    logger.info("Bot online!")


@bot.event
async def on_member_join(user):
  logger.info("{user} joined the server".format(user=user))


@bot.command(name="org", pass_context=True, usage=USAGE_ORG_CMD)
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



@bot.command(name="join", aliases=["j"], pass_context=True, usage=USAGE_JOIN_CMD)
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


@bot.command(name="leave", aliases=["kick", "exit"], pass_context=True, usage=USAGE_LEAVE_CMD)
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


@bot.command(name="play", aliases=["run", "pl"], pass_context=True, usage=USAGE_PLAY_CMD)
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
    with youtube_dl.YoutubeDL(YDL_OPTS) as ydl:
        info_dict = ydl.extract_info(args[0], download=False)
        video_id = info_dict.get("id", None)
        video_title = info_dict.get("title", None)
        ydl.download([args[0]])
        await ctx.send(content=MSG_PLAYING.format(title=video_title))
        video_path = os.path.join(DL_DIR, "{}.{}".format(video_id, "mp3")) #handle multiple extensions in the future
        try:
            voice_client.play(discord.FFmpegPCMAudio(video_path), after=None)
            logger.info("{user} requested song {id} - {title}".format(user=user, id=video_id, title=video_title))
        except ClientException as ex:
            logger.error("Error requesting org: {err}".format(err=ex))

@bot.command(name="pause", aliases=["st", "stop", "yamete"], pass_context=True, usage=USAGE_PAUSE_CMD)
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
