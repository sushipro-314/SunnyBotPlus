import os
import json

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
    async def guild_exists(self, guild_id):
        return bool(await self.db.get_database("guilds").get_collection(str(guild_id)).find_one())

    async def get_guild_data(self, guild_id):
        return await self.db.get_database("guilds").get_collection(str(guild_id)).find_one()

    async def write_guild_data(self, guild_id, data):
        await self.db.get_database("guilds").get_collection(str(guild_id)).delete_many({})
        await self.db.get_database("guilds").get_collection(str(guild_id)).insert_one(data)
        return await self.get_guild_data(guild_id=guild_id)

    async def generate_prefix(self, guild, prefix):
        guild_data = await self.get_guild_data(guild_id=guild.id)
        json_data = {
            "prefix": prefix,
            "starboard": {
                "channel": guild_data["starboard"]["channel"],
                "emoji": guild_data["starboard"]["emoji"],
                "max": guild_data["starboard"]["max"]
            },
            "mod_role": guild_data["mod_role"],
            "disabled": guild_data["disabled"]
        }
        return await self.write_guild_data(guild_id=guild.id, data=json_data)

    @staticmethod
    async def generate_system_channel(guild):
        if guild.system_channel is None:
            return 0
        else:
            system_channel = guild.system_channel.id
        return system_channel

    async def generate_starboard(self, guild, channel, emoji, max_count):
        guild_data = await self.get_guild_data(guild_id=guild.id)
        sys_channel = await self.generate_system_channel(guild=guild)
        if sys_channel != 0:
            system_channel = sys_channel.id
        else:
            system_channel = 0
        json_data = {
            "prefix": guild_data["prefix"],
            "starboard": {
                "channel": system_channel,
                "emoji": emoji,
                "max": max_count
            },
            "mod_role": guild_data["mod_role"],
            "disabled": guild_data["disabled"]
        }
        return await self.write_guild_data(guild_id=guild.id, data=json_data)

    async def generate_guild_data(self, guild):
        json_data = {
            "prefix": self.default_prefix,
            "starboard": {
                "channel": await self.generate_system_channel(guild=guild),
                "emoji": "⭐",
                "max": 2
            },
            "mod_role": 0,
            "disabled": False
        }
        await self.write_guild_data(guild_id=guild.id, data=json_data)
