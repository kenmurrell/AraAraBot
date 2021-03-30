from discord.ext import commands
from discord.ext.commands.context import Context
from discord.ext.commands.bot import Bot
import discord
from datetime import datetime, timedelta
import logging
import sys
import os
import time
import typing

DOCS_UPTIME = "-> show the bot uptime"
DOCS_KILL = "-> kill the bot"

DIR_PATH = os.path.dirname(os.path.realpath(__file__))
SOUNDS_DIR = os.path.join(DIR_PATH, "sounds")
SOUND_KILL = os.path.join(SOUNDS_DIR, "nani.mp3")

logger = logging.getLogger("bot")


class Meta(commands.Cog):

    def __init__(self, bot: Bot, config: dict):
        self.bot = bot
        self.start_time = datetime.now()
        self.config = config

    @commands.command(name="uptime", aliases=["u"], pass_context=True, usage=DOCS_UPTIME)
    async def uptime(self, ctx: Context):
        uptime = round((datetime.now() - self.start_time).total_seconds())
        logger.info("Current uptime: {seconds}".format(seconds=timedelta(seconds=uptime)))
        await ctx.send(content="Current uptime: {seconds}".format(seconds=timedelta(seconds=uptime)))

    @commands.command(name="kill", aliases=["k"], pass_context=True, usage=DOCS_KILL)
    async def kill(self, ctx: Context):
        user = ctx.message.author.name
        logger.info("{user} killed the bot".format(user=user))
        voice_client = ctx.voice_client
        await ctx.send(content=self.config["MESSAGES"]["KILL"])
        if voice_client:
            voice_client.play(discord.FFmpegPCMAudio(SOUND_KILL), after=None)
            while voice_client.is_playing():
                # best way of doing this without clogging up threads in a loop
                time.sleep(6)
            await voice_client.disconnect()
        await ctx.bot.logout()
        sys.exit(1)
