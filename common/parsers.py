import os
import json
import discord
import logging

from pymongo import AsyncMongoClient


class ConfigParser:
    @staticmethod
    async def parse_options(config: dict, find: str):
        options = []
        for option in find.split("."):
            options.append(config[option])
        return options 

class GuildParser:
    config = json.loads(open("./config.json").read())
    db = AsyncMongoClient(config['uris']['database'])
    default_prefix = config['prefix']
        
    async def get_member_data(self, member: discord.Member):
        logging.info("Getting member information, this may take awhile for larger servers!")
        return await self.db.get_database("members").get_collection(str(member.guild.id)).find_one({"uid": member.id})
    
    async def write_member_data(self, member: discord.Member, data):
        logging.info("Writing member information, this may take awhile for larger servers!")
        logging.info("Reinputting data")
        await self.db.get_database("members").get_collection(str(member.guild.id)).delete_many({"uid": member.id})
        logging.info("Inserting data")
        await self.db.get_database("members").get_collection(str(member.guild.id)).insert_one(data)
        return await self.get_member_data(member=member)
    
    async def guild_exists(self, guild_id):
        return bool(await self.db.get_database("guilds").get_collection(str(guild_id)).find_one())

    async def get_guild_data(self, guild_id):
        return await self.db.get_database("guilds").get_collection(str(guild_id)).find_one()

    async def write_guild_data(self, guild_id, data):
        logging.info("Reinputting data")
        await self.db.get_database("guilds").get_collection(str(guild_id)).delete_many({})
        logging.info("Inserting data")
        await self.db.get_database("guilds").get_collection(str(guild_id)).insert_one(data)
        logging.info(f"Wrote guild data for guild ID: {guild_id}")
        return await self.get_guild_data(guild_id=guild_id)
    
    @staticmethod
    async def generate_system_channel(guild):
        if guild.system_channel is None:
            return 0
        else:
            system_channel = guild.system_channel.id
        return system_channel

    async def generate_guild_data(self, guild):
        json_data = json.loads(open("../settings/default_server_config.json").read())
        await self.write_guild_data(guild_id=guild.id, data=json_data)
