from discord.ext import commands
from datetime import datetime, timedelta
import logging


class Meta(commands.Cog):

    logger = logging.getLogger("bot")

    def __init__(self, bot, config):
        self.bot = bot
        self.start_time = datetime.now()
        self.config = config

    @commands.command()
    async def uptime(self, ctx):
        uptime = round((datetime.now() - self.start_time).total_seconds())
        self.logger.info("Current uptime: {seconds}".format(seconds=timedelta(seconds=uptime)))
        await ctx.send("Current uptime: {seconds}".format(seconds=timedelta(seconds=uptime)))
