import os
import json
import discord
import logging
import random
import string

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
    storage_mode = (config.get("storage") or "JSON")
    db = AsyncMongoClient(config['uris']['database']) if storage_mode == "DB" else None
    default_prefix = config['prefix']
    
    async def write_json_data(self, location, data, dir=None):
        if not os.path.exists(location) and dir is not None:
            os.mkdir(dir)
        file = open(location, "w+")
        try:
            file.write(json.dumps(data))
        except Exception:
            logging.error("An error occurred writing data!")
        finally:
            file.close()
    
    async def get_json_data(self, location):
        file = open(location)
        try:
            return json.loads(file.read())
        except Exception:
            logging.error("An error occurred fetching data!")
        finally:
            file.close()
    
    async def get_member_data(self, member: discord.Member):
        logging.info("Getting member information, this may take awhile for larger servers!")
        if self.db is not None:
            return await self.db.get_database("members").get_collection(str(member.guild.id)).find_one({"uid": member.id})
    
    async def write_member_data(self, member: discord.Member, data):
        logging.info("Writing member information, this may take awhile for larger servers!")
        if self.db is not None:
            logging.info("Reinputting data")
            await self.db.get_database("members").get_collection(str(member.guild.id)).delete_many({"uid": member.id})
            logging.info("Inserting data")
            await self.db.get_database("members").get_collection(str(member.guild.id)).insert_one(data)
        elif self.storage_mode == "JSON":
            await self.write_json_data(f"./settings/members/{(member.guild.id)}/{str(member.id)}.json", data=data)
        return await self.get_member_data(member=member)
    
    async def guild_exists(self, guild_id):
        if self.db is not None:
            return bool(await self.db.get_database("guilds").get_collection(str(guild_id)).find_one())
        elif self.storage_mode == "JSON":
            return os.path.exists(f"./settings/guilds/{guild_id}")

    async def get_guild_data(self, guild_id):
        if self.db is not None:
            return await self.db.get_database("guilds").get_collection(str(guild_id)).find_one()
        elif self.storage_mode == "JSON":
            return self.get_json_data(location=f"./settings/guilds/{str(guild_id)}/guild.json")

    async def write_guild_data(self, guild_id, data):
        if self.db is not None:
            logging.info("Reinputting data")
            await self.db.get_database("guilds").get_collection(str(guild_id)).delete_many({})
            logging.info("Inserting data")
            await self.db.get_database("guilds").get_collection(str(guild_id)).insert_one(data)
            logging.info(f"Wrote guild data for guild ID: {guild_id}")
            return await self.get_guild_data(guild_id=guild_id)
        elif self.storage_mode == "JSON":
            return await self.write_json_data(location=f"./settings/guilds/{str(guild_id)}/guild.json", data=data, dir=f"./settings/guilds/{str(guild_id)}")
    
    @staticmethod
    async def generate_system_channel(guild):
        if guild.system_channel is None:
            return 0
        else:
            system_channel = guild.system_channel.id
        return system_channel

    async def generate_guild_data(self, guild):
        json_data = {
            "prefix": "sun$",
            "starboard": {
                "channel": 0,
                "emoji": ":star:",
                "max": 2
            },
            "xp_gain": 10,
            "xp_cost": 1000,
            "mod_role": 0,
            "disabled": False
        }
        await self.write_guild_data(guild_id=guild.id, data=json_data)

    async def random_digits(self, number=4):
        random_string = ''.join(random.choices(string.digits + string.ascii_lowercase, k=number))
        return random_string