import asyncio
import json
import logging
import os
import random
import shutil
import string

import discord
import traceback

from discord.ext import commands

import common.parsers

intents = discord.Intents.all()


data_parser = common.parsers.GuildParser()

total_guilds = []

global session
db = data_parser.db
config = data_parser.config

token = config['token']

if data_parser.storage_mode == "JSON":
    if not os.path.exists("./settings/guilds"):
        os.mkdir("guilds")
    if not os.path.exists("./settings/members"):
        os.mkdir("members")

async def prefix(bot, message):
    if message.guild:
        g_data = await data_parser.get_guild_data(message.guild.id)
    else:
        g_data = None
    if (g_data is None) or (g_data is None) or (g_data.get("prefix") is None):
        return data_parser.default_prefix
    else:
        return g_data["prefix"], data_parser.default_prefix

bot = commands.AutoShardedBot(command_prefix=prefix, intents=intents, case_insensitive=False, shard_ids=config["shard_ids"], shard_count=config["shard_count"] or len(config["shard_ids"]), activity=discord.Activity(type=discord.ActivityType.listening,
                                             name=f'music across all servers | {data_parser.default_prefix}help'))

async def sync_commands(guild=None):
    if guild is not None:
        await bot.tree.sync(guild=guild)
    else:
        await bot.tree.sync()
    logging.info("Command tree synced")

@commands.cooldown(2, 7.3, commands.BucketType.guild)
@bot.hybrid_command(name="prefix", help_command="Changes the server's prefix")
@commands.has_permissions(manage_guild=True)
async def update_prefix(ctx, prefix):
    g_data = await data_parser.get_guild_data(ctx.guild.id)
    if g_data is not None:
        g_data["prefix"] = prefix
        wg_data = await data_parser.write_guild_data(ctx.guild.id, g_data)
        await ctx.send(f"Updated Configuration for server {ctx.guild.name}, value is now {wg_data['prefix']}")

async def send_all_guilds(message, content, developer):
    async for g in bot.fetch_guilds():
        guild_data = await data_parser.get_guild_data(g.id)
        try:
            dev_announce_id = guild_data.get("dev_announce")
            if dev_announce_id is not None:
                dev_announce_channel = await bot.fetch_channel(dev_announce_id)
                embed = discord.Embed(
                    title=f"Announcement from developer {developer}",
                    description=content
                )
                logging.info(f"Sent data to {g.name}")
                if isinstance(dev_announce_channel, discord.TextChannel):
                    await dev_announce_channel.send(embed=embed)
        except ():
            logging.info(f"Could not send data to guild {g.name}")
    await message.edit(content=f"Sent to all guilds!")

@bot.hybrid_command(name="announce", help_command="Developer Only.")
@commands.has_permissions(manage_guild=True)
@commands.is_owner()
async def dev_announce_send(ctx, message):
    msg = await ctx.send("Sending message" + message + "to all guilds!")
    await send_all_guilds(content=message, message=msg, developer=ctx.author.name)

async def send_banned_embed(guild):
    bannedembed = discord.Embed(
        title=f"{guild.name} - Safety message",
        description=f"You're server has been remotely disabled by a developer or another staff member! If you wish to appeal, please see the (discord server)[https://discord.gg/TCE7KWjc9R]. Thank you for your cooperation!",
    )
    if guild.system_channel:
        await guild.system_channel.send(embed=bannedembed)
    elif guild.owner:
        await guild.owner.send(embed=bannedembed)

@bot.hybrid_command(name="exclude", help_command="Developer Only.")
@commands.has_permissions(manage_guild=True)
@commands.is_owner()
async def ban_server(ctx, guild_id, excluded=True):
    gdata = await data_parser.get_guild_data(guild_id=guild_id)
    gdata["disabled"] = excluded
    written = await data_parser.write_guild_data(guild_id=guild_id, data=gdata)
    await send_banned_embed(guild=await bot.fetch_guild(guild_id))
    await ctx.send("Guild data banned. Banned value is set to " + str(written["disabled"]))

@bot.hybrid_command(name="eval", help_command="Developer Only.")
@commands.has_permissions(manage_guild=True)
@commands.is_owner()
async def eval_code(ctx, code):
    eval(code)
    await ctx.send("Evaluated Code Successfully! Result: " + str(eval(code)))

@bot.hybrid_command(name="viewdb", help_command="Developer Only.")
@commands.has_permissions(manage_guild=True)
@commands.is_owner()
async def view_database(ctx, data="guilds"):
    if data:
           entries = await db.get_database(data).list_collection_names()
           await ctx.send("Listing all database collection names\n```" + str(entries).replace(",", "\n") + "```")

@bot.hybrid_command(name="searchdb", help_command="Developer Only.")
@commands.has_permissions(manage_guild=True)
@commands.is_owner()
async def search_database(ctx, collection, data="guilds"):
    if data:
           collection = await db.get_database(data).get_collection(collection).find({}).to_list()
           await ctx.send("Listing all database collection entries\n```" + str(collection).replace(",", "\n") + "```")

@bot.hybrid_command(name="sync", help_command="Developer Only.")
@commands.is_owner()
async def sync_command(ctx):
    await sync_commands()
    await ctx.send("Synced.")

@bot.event
async def on_guild_join(guild):
    embed = discord.Embed(
        title=f"Thank you for inviting {bot.user.name}!",
        description=f"Thank you for using {bot.user.name}, it helps grow our bot and support our services!"
    )
    logging.info("creating guild data for... " + guild.name)
    await sync_commands(guild=guild)
    await data_parser.generate_guild_data(guild=guild)
    system_channel = await data_parser.generate_system_channel(guild=guild)
    system_channel_obj = await bot.fetch_channel(system_channel)
    if system_channel != 0 and isinstance(system_channel_obj, discord.TextChannel):
        await system_channel_obj.send(embed=embed)

async def index_cogs():
    cog_list = os.listdir("cogs")
    for i in cog_list:
        if i.endswith(".py"):
            try:
                if ("disabled" not in i):
                    await bot.load_extension(f"cogs.{i.split('.')[0]}")
                    logging.info(f"indexed and loaded extension with path: {i}")
                elif("disabled" in i):
                    logging.warning(f"Ignoring extension: {i}, extension disabled!")
            except commands.ExtensionAlreadyLoaded:
                logging.error("Failed to load extension: Extension has already been loaded. This could be due to a reconnect or other internal issues.")


async def index_guilds():
    index = 0
    indexed_guilds = asyncio.Queue()
    async for g in bot.fetch_guilds():
        index += 1
        if not await data_parser.guild_exists(g.id):
            await data_parser.generate_guild_data(guild=g)
        await indexed_guilds.put(g)
    return indexed_guilds
@bot.event
async def on_shard_ready(shard_id):
    logging.info(f'Shard #{shard_id} is ready')

@bot.event
async def on_ready():
    await bot.wait_until_ready()
    if os.path.exists("jobs"):
        shutil.rmtree("jobs")
    os.mkdir("jobs")
    guilds_all = await index_guilds()
    logging.info("Guild index successful!")
    await index_cogs()
    logging.info("Modules/Cogs loaded!")
    await sync_commands()
    logging.info("Slash commands synced!")
    if data_parser.db is not None:
        db_address = f"Database running at {(await db.address)[0]}:{(await db.address)[1]}"
    else:
        db_address = "No database"
    logging.info(str(f"""



  .--.--.                                                     ,---,.               ___     
 /  /    '.                                                 ,'  .'  \            ,--.'|_   
|  :  /`. /          ,--,      ,---,      ,---,           ,---.' .' |   ,---.    |  | :,'  
;  |  |--`         ,'_ /|  ,-+-. /  | ,-+-. /  |          |   |  |: |  '   ,'    :  : ' :  
|  :  ;_      .--. |  | : ,--.'|'   |,--.'|'   |     .--, :   :  :  / /   /   |.;__,'  /   
 \  \    `. ,'_ /| :  . ||   |  ,"' |   |  ,"' |   /_ ./| :   |    ; .   ; ,. :|  |   |    
  `----.   \|  ' | |  . .|   | /  | |   | /  | |, ' , ' : |   :      '   | |: ::__,'| :    
  __ \  \  ||  | ' |  | ||   | |  | |   | |  | /___/ \: | |   |   . |'   | .; :  '  : |__  
 /  /`--'  /:  | : ;  ; ||   | |  |/|   | |  |/ .  \  ' | '   :  '; ||   :    |  |  | '.'| 
'--'.     / '  :  `--'   \   | |--' |   | |--'   \  ;   : |   |  | ;  \   \  /   ;  :    ; 
  `--'---'  :  ,      .-./   |/     |   |/        \  \  ; |   :   /    `----'    |  ,   /  
             `--`----'   '---'      '---'          :  \  \|   | ,'                ---`-'   
                                                    \  ' ;`----'                           
                                                     `--`                                  

{len(bot.voice_clients)} voice clients, {guilds_all.qsize()} guild(s) indexed, {db_address}
"""))
    logging.info(f"Started bot as {bot.user.name}")

@bot.event
async def on_command_error(ctx, error: discord.DiscordException):
    errors = [
        {
            "message": "This command is currently on cooldown!",
            "type": commands.CommandOnCooldown
        },
        {
            "message": "Please have the bot rejoin vc",
            "type": BrokenPipeError
        },
        {
            "message": "Please have the bot rejoin vc",
            "type": AttributeError
        },
        {
            "message": "Try running this command with elevated permissions for both you and the bot",
            "type": commands.MissingPermissions
        },
        {
            "message": "Try running this command again",
            "type": commands.CommandInvokeError
        },
        {
            "message": "Try running this command again",
            "type": commands.CommandInvokeError
        },
        {
            "message": "Try running this command with different arguments or in a different channel",
            "type": commands.CommandError
        }
    ]
    for i in errors:
        if isinstance(error, i["type"]):
            err_msg = i["message"]
            break
        else:
            err_msg = "Cannot explain this error"
    error_id = await data_parser.random_digits()
    await ctx.send(
        f"An error occurred: ```{error}``` {err_msg}. If this error happens continually, contact the support server! (Crash ID: {error_id})")
    error_json = {
        "id": error_id,
        "error": error.args
    }
    await db.get_database("errors").get_collection(error_id).insert_one({'data': error_json})
    await db.get_database("errors").get_collection(error_id).insert_one({'trace': ''.join(traceback.TracebackException.from_exception(error).format())})
    raise error

logging.root = logging.getLogger("discord")

bot.run(token)
