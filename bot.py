import discord
import youtube_dl
import asyncio
from discord.ext import commands
import random as rand # using this because of weird abiguity
import os
import sys
import logging
from datetime import datetime


logger = logging.getLogger('main')
fileHandler = logging.FileHandler('{:%Y-%m-%d}.log'.format(datetime.now()))
formatter = logging.Formatter('%(asctime)s | %(levelname)-8s | %(lineno)04d | %(message)s')
fileHandler.setFormatter(formatter)
logger.addHandler(fileHandler)
streamHandler = logging.StreamHandler(sys.stdout)
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)
logger.setLevel(logging.INFO)

TOKEN = "ODE2MTM5MDA0NjQyNDU5NjU4.YD2mrQ.WdukyEdh20Wus6D7YXF0_I0nN5w"
client = commands.Bot(command_prefix = "!")
DIR_PATH = os.path.dirname(os.path.realpath(__file__))

#SOUNDS
SOUNDS_DIR = os.path.join(DIR_PATH, "sounds")
SOUND_ARA_ARA = os.path.join(SOUNDS_DIR,"ara_ara.mp3")

#DOWNLOADS
DL_DIR = os.path.join(DIR_PATH, "downloads")
CACHE_DIR = os.path.join(DIR_PATH, "cache")

#MESSAGES
MSG_JOINING_VOICE = "Joining the {channel} channel ＼(^ω^＼)"
MSG_LEAVING_VOICE = "Leaving the {channel} channel（ミ￣ー￣ミ)"
MSG_PLAYING = "Playing... (ﾉ◕ヮ◕)ﾉ*:･ﾟ✧ \n{title}"
MSG_PAUSING = "Paused... (/ω＼)	"
MSG_RESUMING = "Resuming... °˖✧◝(⁰▿⁰)◜✧˖°	"

ERROR_JOINING_VOICE = "{user}-chan, baka! You're not in a voice channel! ( ╥ω╥ )"
ERROR_PLAYING = "{user}-chan, baka! I cannot play when I'm not in a voice channel! ( ╥ω╥ )"

nhent_num_size = 6
ydl_opts = {
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

@client.event
async def on_ready():
    print("Bot online.")

@client.command(name="join", pass_context=True)
async def join(ctx):
    user = ctx.message.author
    voice = user.voice
    if voice is None:
        await ctx.send(content=ERROR_JOINING_VOICE.format(user=user.name))
    else:
        vchannel = voice.channel
        await ctx.send(content=MSG_JOINING_VOICE.format(channel=vchannel.name))
        vc = await vchannel.connect()
        vc.play(discord.FFmpegPCMAudio(SOUND_ARA_ARA), after=None)
        logger.info("{} requested join to {} channel".format(user.name, vchannel.name))

@client.command(name="leave", pass_context=True)
async def leave(ctx):
    user = ctx.message.author
    await ctx.voice_client.disconnect()
    tchannel = ctx.channel
    await ctx.send(content=MSG_LEAVING_VOICE.format(channel=tchannel.name))
    logger.info("{} request kick from {} channel".format(user.name, tchannel.name))

@client.command(name="play", pass_context=True)
async def play(ctx, url):
    user = ctx.message.author
    if ctx.voice_client is None:
        await ctx.send(content=ERROR_PLAYING.format(user=user.name))
    else:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            video_id = info_dict.get("id", None)
            video_title = info_dict.get("title", None)
            ydl.download([url])
            await ctx.send(content=MSG_PLAYING.format(title=video_title))
            video_path = os.path.join(DL_DIR, "{}.{}".format(video_id, "mp3")) #handle multiple extensions in the future
            ctx.voice_client.play(discord.FFmpegPCMAudio(video_path), after=None)
            logger.info("{user} requested song {id} - {title}".format(user=user.name, id=video_id, title=video_title))


@client.command(name="pause", pass_context=True)
async def pause(ctx):
    user = ctx.message.author
    if ctx.voice_client.is_playing():
        await ctx.send(content=MSG_PAUSING)
        ctx.voice_client.pause()
        logger.info("{} paused the current song".format(user.name))
    else:
        await ctx.send(content=MSG_RESUMING)
        ctx.voice_client.resume()
        logger.info("{} resumed the current song".format(user.name))


client.run(TOKEN)
