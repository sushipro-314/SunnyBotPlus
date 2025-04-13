import discord
from discord.ext import commands
import json
import os
import logging
from common import OtherParser, CommandParser

# Command parsing object
command_parser = CommandParser()
#Misc parsing object
other_parser = OtherParser()
# Bot Config from misc parsing object
config = other_parser.config

# Bot intents and Bot object
intents = discord.Intents.default()
intents.message_content = True
bot=commands.Bot(command_prefix=config["prefix"],intents=intents)

async def add_cogs():
        for cog in os.listdir("./commands"):
            if cog.endswith(".py"):
                await bot.load_extension("commands." + cog.replace(".py", ""))
                logging.info("Loaded extension: " + cog)

# Indexes all guilds and syncs entire command tree
@bot.event
async def on_ready():
    await other_parser.sync_commands(bot=bot)
    await other_parser.index_guilds(bot=bot)
    await add_cogs()
    logging.info(f"Logged in as {bot.user.name}")

# When the bot joins it will signal the syncing of all commands
@bot.event
async def on_guild_join(guild):
    await other_parser.sync_commands(bot=bot, guild=guild)

logging.root = logging.getLogger("discord")

bot.run(config["token"])
