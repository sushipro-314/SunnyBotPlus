import asyncio
import json
import logging.handlers
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

async def random_digits(number=4):
    random_string = ''.join(random.choices(string.digits + string.ascii_lowercase, k=number))
    return random_string

global session
db = data_parser.db
config = data_parser.config

token = config['token']

async def prefix(bot, message):
    g_data = await data_parser.get_guild_data(message.guild.id)
    if (g_data is None) or (g_data is None) or (g_data.get("prefix") is None):
        return data_parser.default_prefix
    else:
        return g_data["prefix"], data_parser.default_prefix

bot = commands.AutoShardedBot(command_prefix=prefix, intents=intents, case_insensitive=False, shard_ids=config["shard_ids"], shard_count=config["shard_count"] or len(config["shard_ids"]))

async def sync_commands(guild=None):
    if guild is not None:
        await bot.tree.sync(guild=guild)
    else:
        await bot.tree.sync()
    logging.info("Command tree synced")

@commands.cooldown(2, 7.3, commands.BucketType.guild)
@bot.hybrid_command(name="config", help_command="Changes the server configuration.")
@commands.has_permissions(manage_guild=True)
async def update_config(ctx, value, setting=""):
        g_data = await data_parser.get_guild_data(ctx.guild.id)
        if g_data is not None:
            g_data[setting] = value
            g_data_new = await data_parser.write_guild_data(ctx.guild.id, g_data)
            if g_data_new:
                await ctx.send(f"Updated Configuration for server {ctx.guild.name}, value is now {value}")
            else:
                await ctx.send(f"Updated Configuration for server {ctx.guild.name}, value is now **Unknown**")
        else:
            await ctx.send("An unknown error occurred and we couldn't find your guild data. Please try again later!")

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
                await dev_announce_channel.send(embed=embed)
        except ():
            logging.info(f"Could not send data to guild {g.name}")
    await message.edit(content=f"Sent to all guilds!")

@bot.hybrid_command(name="announce", help_command="Developer Only.")
@commands.has_permissions(manage_guild=True)
async def dev_announce_send(ctx, message):
    if ctx.message.author.name in open('settings/developers.txt').readline():
        msg = await ctx.send("Sending message" + message + "to all guilds!")
        await send_all_guilds(content=message, message=msg, developer=ctx.author.name)
    else:
        await ctx.send("You do not have permission to use this command.")

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
async def ban_server(ctx, guild_id):
    if ctx.message.author.name in open('settings/developers.txt').readline():
        gdata = await data_parser.get_guild_data(guild_id=guild_id)
        gdata["disabled"] = True
        written = await data_parser.write_guild_data(guild_id=guild_id, data=gdata)
        await send_banned_embed(guild=await bot.fetch_guild(guild_id))
        await ctx.send("Guild data banned. Banned value is set to " + str(written["disabled"]))
    else:
        await ctx.send("You do not have permission to use this command.")

@bot.hybrid_command(name="unexclude", help_command="Developer Only.")
@commands.has_permissions(manage_guild=True)
async def unban_server(ctx, guild_id):
    if ctx.message.author.name in open('settings/developers.txt').readline():
        gdata = await data_parser.get_guild_data(guild_id=guild_id)
        gdata["disabled"] = False
        written = await data_parser.write_guild_data(guild_id=guild_id, data=gdata)
        await send_banned_embed(guild=await bot.fetch_guild(guild_id))
        await ctx.send("Guild data unbanned. Banned value is set to " + str(written["disabled"]))
    else:
        await ctx.send("You do not have permission to use this command.")

@bot.hybrid_command(name="eval", help_command="Developer Only.")
@commands.has_permissions(manage_guild=True)
async def eval_code(ctx, code, awaitable=False):
    developers = open('settings/developers.txt').readline()
    if ctx.message.author.name in developers:
        if awaitable:
            await eval(code)
        else:
            eval(code)
        await ctx.send("Evaluated Code Successfully! Result: " + eval(code))
    else:
        await ctx.send(f"Congrats!! You found the eval command, allowing people to directly run code on the host machine. Such a shame it only works for {random.choice(developers)} though...")

@bot.hybrid_command(name="viewdb", help_command="Developer Only.")
@commands.has_permissions(manage_guild=True)
async def view_database(ctx, data="guilds"):
    developers = open('settings/developers.txt').readline()
    if ctx.message.author.name in developers:
       if data:
           entries = await db.get_database(data).list_collection_names()
           await ctx.send("Listing all database collection names\n```" + str(entries).replace(",", "\n") + "```")
    else:
        await ctx.send(f"Congrats!! You found the view db command, revealing all the data in the bot's internal database. Such a shame it only works for {random.choice(developers)} though...")

@bot.hybrid_command(name="searchdb", help_command="Developer Only.")
@commands.has_permissions(manage_guild=True)
async def search_database(ctx, collection, data="guilds"):
    developers = open('settings/developers.txt').readline()
    if ctx.message.author.name in developers:
       if data:
           collection = await db.get_database(data).get_collection(collection).find({}).to_list()
           await ctx.send("Listing all database collection entries\n```" + str(collection).replace(",", "\n") + "```")
    else:
        await ctx.send(f"Congrats!! You found the get db command, allowing people to search the entire database. Such a shame it only works for {random.choice(developers)} though...")

@bot.hybrid_command(name="sync", help_command="Developer Only.")
async def sync_command(ctx):
    if ctx.message.author.name in open('settings/developers.txt').readline():
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
    if system_channel != 0:
        await system_channel_obj.send(embed=embed)

@bot.event
async def on_guild_remove(guild):
    logging.info("removing guild data for... " + str(guild.name))
    await db.get_database("guilds").get_collection(str(guild.id)).delete_many({})

async def index_cogs():
    cog_list = os.listdir("cogs")
    for i in cog_list:
        if i.endswith(".py"):
            if ("disabled" not in i) and ((bot.get_cog("cogs." + i.split('.')[0])) is None):
                await bot.load_extension(f"cogs.{i.split('.')[0]}")
                logging.info(f"indexed and loaded extension with path: {i}")
            elif ((bot.get_cog("cogs." + i.split('.')[0])) is not None):
                await bot.unload_extension(f"cogs.{i.split('.')[0]}")
            else:
                logging.warning(f"Ignoring extension: {i}, extension disabled or has already been loaded!")


async def index_guilds():
    indexed_guilds = asyncio.Queue()
    index = 0
    async for g in bot.fetch_guilds():
        index += 1
        if not await data_parser.guild_exists(g.id):
            await data_parser.generate_guild_data(guild=g)
            system_c = await data_parser.generate_system_channel(guild=g)
            await data_parser.generate_starboard(guild=g, channel=system_c, emoji="⭐",
                                     max_count=2)
        indexed_guilds.put_nowait(g)
    return indexed_guilds
@bot.event
async def on_shard_ready(shard_id):
    logging.info(f'Shard #{shard_id} is ready')

@bot.event
async def on_ready():
    if os.path.exists("jobs"):
        shutil.rmtree("jobs")
    os.mkdir("jobs")
    guilds_all = await index_guilds()
    logging.info("Guild index successful!")
    await index_cogs()
    logging.info("Modules/Cogs loaded!")
    await sync_commands()
    logging.info("Slash commands synced!")
    db_address = await db.address
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

{len(bot.voice_clients)} voice clients, {guilds_all.qsize()} guild(s) indexed, Database running at {db_address[0]}:{db_address[1]}
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
    error_id = await random_digits()
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
