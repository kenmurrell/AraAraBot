import logging
import os
import sys
from datetime import datetime
import yaml
from discord.ext import commands
from music import Music
from meta import Meta

DIR_PATH = os.path.dirname(os.path.realpath(__file__))
LOGS_PATH = os.path.join(DIR_PATH, "logs")

logger = logging.getLogger('bot')
fileHandler = logging.FileHandler(os.path.join(LOGS_PATH, '{:%Y-%m-%d}.log'.format(datetime.now())), encoding="utf-8")
formatter = logging.Formatter('%(asctime)s | %(levelname)-8s | %(lineno)04d | %(message)s')
fileHandler.setFormatter(formatter)
logger.addHandler(fileHandler)
streamHandler = logging.StreamHandler(sys.stdout)
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)
logger.setLevel(logging.INFO)

cogs = [Music, Meta]

config = None
with open("config.yaml", encoding="utf-8") as configfile:
    config = yaml.load(configfile, Loader=yaml.FullLoader)
bot = commands.Bot(command_prefix=config["MAIN"]["PREFIX"])


@bot.event
async def on_ready():
    logger.info("Bot online! Logged in as {}".format(bot.user.name))


@bot.event
async def on_member_join(user):
    logger.info("{user} joined the server".format(user=user))


def run():
    for cog in cogs:
        bot.add_cog(cog(bot, config["MUSIC"]))
    if config["MAIN"]["TOKEN"] == "":
        logger.error("No token specified in the config.yaml file")
        raise ValueError("No token specified in the config.yaml file. Please specify a token.")
    bot.run(config["MAIN"]["TOKEN"])


if __name__ == "__main__":
    run()
