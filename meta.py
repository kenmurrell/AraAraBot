from discord.ext import commands
from datetime import datetime, timedelta
import logging
import sys

DOCS_UPTIME = "-> show the bot uptime"
DOCS_KILL = "-> kill her"

logger = logging.getLogger("bot")


class Meta(commands.Cog):

    def __init__(self, bot, config):
        self.bot = bot
        self.start_time = datetime.now()
        self.config = config

    @commands.command(name="uptime", pass_context=True, usage=DOCS_UPTIME)
    async def uptime(self, ctx):
        uptime = round((datetime.now() - self.start_time).total_seconds())
        logger.info("Current uptime: {seconds}".format(seconds=timedelta(seconds=uptime)))
        await ctx.send(content="Current uptime: {seconds}".format(seconds=timedelta(seconds=uptime)))

    @commands.command(name="kill", pass_context=True, usage=DOCS_KILL)
    async def kill(self, ctx):
        user = ctx.message.author.name
        logger.info("{user} killed the bot".format(user=user))
        await ctx.send(content="(×_×)⌒☆")
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
        try:
            await ctx.bot.logout()
        except Exception as ex:
            pass
        sys.exit(1)
