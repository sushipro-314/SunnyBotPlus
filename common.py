import discord
import logging
import json
import pymongo
import random
import string
import os

db = pymongo.AsyncMongoClient()

class CommandParser:
    # Generates an embed based on the parameters given
    async def generate_embed(self, title, desc, fields=[]):
        embed_obj = discord.Embed(
            title=title,
            description=desc,
        )
        # For loop for checking each field
        for i in fields:
            embed_obj.add_field(name=i["name"], value=i["value"])
        return embed_obj
    # Random digits function
    async def random_digits(number):
        return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(number))

class OtherParser:
    # Indexed guilds list
    indexed_guilds = []
    # Database connection object for connecting
    config = json.loads(open("./config.json").read())
    db = pymongo.AsyncMongoClient(config["uris"]["database"])

    async def index_guild(self, guild):
        # Syncs command data
        # Appends the guild id to the list of indexed guilds in the current class
        self.indexed_guilds.append(guild.id)

    async def index_guilds(self, bot):
        # Fetches all the guilds and adds their info, such as prefixes or info from other modules, to a database
        async for guild in bot.fetch_guilds():
            # Calls the function to index the bot
            await self.index_guild(guild=guild)
            logging.info("Indexed Guild! " + guild.name)
    
    async def sync_commands(self, bot, guild=None):
        # Checks if the guild exists
        if guild is not None:
            # Syncs the commands for the bot in that guild if it does exist
            logging.info(f"Syncing Application Commands... (Guild: {guild.name}))")
            await bot.tree.sync(guild.id)
        else:
            # Syncs globally if the oppisite is true
            logging.info(f"Syncing Application Commands... (This may take awhile!)")
            await bot.tree.sync()
        logging.info("Synced All Application Commands!")
    
    async def write_guild_data(self, data, gid):
        editied_data = data
        editied_data["gid"] = gid
        await db.get_database("tuna").get_collection("guilds").delete_many({"gid": gid})
        return await db.get_database("tuna").get_collection("guilds").insert_one(editied_data)
    
    async def get_guild_data(self, gid):
        return (await db.get_database("tuna").get_collection("guilds").find_one({"gid": gid}))