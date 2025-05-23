import asyncio
import json
import os

import aiohttp
import discord
from discord.ext import commands
import gtts
import random
import common.parsers
from datetime import datetime
import logging

from googleapiclient.discovery import build
from translate import Translator
from common.parsers import GuildParser
from asyncio.subprocess import create_subprocess_exec, create_subprocess_shell

data_parser = GuildParser()

class FunOrRandom(commands.Cog):
    """
    Random Fun and Interesting Commands and features to make the bot more interesting
    """
    limits = [{}]
    def __init__(self, bot): # this is a special method that is called when the cog is loaded
        self.bot = bot

    default_prefix = common.parsers.GuildParser().default_prefix

    async def calc_time(self):
        dt_obj = datetime.strptime('20.12.2016 09:38:42,76',
                                   '%d.%m.%Y %H:%M:%S,%f')
        millisec = dt_obj.timestamp() * 1000
        return millisec

    session=aiohttp.ClientSession()

    async def create_job(self):
        random_id = random.randint(1000, 9999)
        os.mkdir(f'jobs/{random_id}')
        return f'jobs/{random_id}'

    @commands.hybrid_command(name='tts',
                      help='Says something through GTTS/text-to-speech (send an attachment with the command)')
    async def tts(self, ctx, *, text=None):
        if text is not None:
            tts = gtts.gTTS(text)
            tts.save(f'attachments/audio/{ctx.message.id}.mp3')
            file = discord.File(f'attachments/audio/{ctx.message.id}.mp3')
            await ctx.send(f"🎉 | Uploaded the text '{text}' to TTS. Here you go!", file=file)
        elif ctx.message.attachments:
            attachment = ctx.message.attachments[0]
            await attachment.save(f"attachments/audio/tts/{ctx.guild.id}_{attachment.id}-text.txt")
            tts = gtts.gTTS(open(f"attachments/audio/tts/{ctx.guild.id}_{attachment.id}-text.txt").read())
            tts.save(f'attachments/audio/{ctx.message.id}.mp3')
            file = discord.File(f'attachments/audio/{ctx.message.id}.mp3')
            await ctx.send(
                f"🎉 | Uploaded the text '{open(f'attachments/audio/tts/{ctx.guild.id}_{attachment.id}')}' from text file to TTS. Here you go!",
                file=file)
        else:
            await ctx.send(
                f'🎉 | Arguments missing: Please choose either a text file or the text in the message with quotations surrounding it')

    @commands.hybrid_command(name='avatar',
                      help="Get the user's avatar")
    async def get_avatar(self, ctx, user: discord.Member = None):
        embed = discord.Embed()
        if not user:
            user = ctx.message.author
        else:
            user = user
        embed.set_image(url=user.display_avatar.url)
        embed.title = f"Avatar for: {user.display_name}"
        await ctx.send(embed=embed)
        logging.log(level=logging.INFO, msg="received avatar")

    @commands.hybrid_command(name='8ball',
                      help="The magic 8ball command. Used for yes or no answers")
    async def eight_ball(self, ctx, *, text=None):
        data = json.loads(open("settings/8ball.json").read())
        chosen = random.choice(data)
        embed = discord.Embed(
            title="The Magic 8ball",
            description=f"Here is the information requested by <@{ctx.message.author.id}>.\n**You answered**: {text}\n***The 8ball's response***: {chosen[1]}"
        )
        await ctx.send(f"The 8ball's Response is ***{chosen[1]}***", embed=embed)

    @commands.hybrid_command(name='ping',
                      help='Pings the bot, along with latency information.')
    async def ping_bot(self, ctx):
        await ctx.send(f'🏓 | Pong! Latency is {round(self.bot.latency, 2)} milliseconds!')

    @commands.hybrid_command(name='meme',
                      help='Displays a random meme')
    async def random_meme(self, ctx):
        request = await self.session.get(url=f'https://meme-api.com/gimme')
        logging.getLogger().info("Sent request with status code: " + str(request.status))
        data = await request.read()
        logging.getLogger().info(data)
        data_json = json.loads(data)
        if data_json["nsfw"] is False:
            embed = discord.Embed(title=data_json["title"])
            embed.set_image(url=data_json["url"])
            await ctx.send(embed=embed)
        elif data_json["nsfw"] is True:
            await ctx.send("Sorry, we cannot accept NSFW memes. Try again in a few moments")

    @commands.group(name="translate", help="Translates a message based on message id or text")
    async def translate(self, ctx):
        pass

    @translate.command(name='msg',
                      help='Translate a message')
    async def translate_message(self, ctx, to_lang, message):
        message = await ctx.fetch_message(message)
        logging.info(message)
        translator = Translator(to_lang=to_lang)
        text = translator.translate(text=message.content)
        await ctx.send(f'{message.content} -> {text}')

    @translate.command(name='text',
                       help='Translate a text value')
    async def translate_message(self, ctx, to_lang, text_value):
        logging.info(text_value)
        translator = Translator(to_lang=to_lang)
        text = translator.translate(text=text_value)
        await ctx.send(f'{text_value} --> {text}')

    @commands.hybrid_command(name='buzzify',
                      help='Generates a buzz lightyear meme')
    async def generate_meme(self, ctx, top="memes", bottom="memes everywhere"):
        embed = discord.Embed(title=f'{top}, {bottom}')
        embed.set_image(url=f'https://api.memegen.link/images/buzz/{top.replace(" ", "_")}/{bottom.replace(" ", "_")}.png')
        await ctx.send(embed=embed)

    async def get_guild_data(self, guild_id):
        return json.loads(open(f"settings/guilds/{guild_id}.json", 'r+').read())

    async def write_guild_data(self, guild_id, data):
        open(f"settings/guilds/{guild_id}.json", 'w+').write(json.dumps(data))
        return await self.get_guild_data(guild_id=guild_id)

    async def generate_ship_image(self, members, edit_message):
        global ship_emojis
        ship_percentage = random.randint(0, 100)
        if ship_percentage <= 10:
            globals().update(ship_emojis="💖")
        elif ship_percentage <= 50:
            globals().update(ship_emojis="💖💖")
        elif ship_percentage <= 100:
            globals().update(ship_emojis="💖💖💖")
        else:
            globals().update(ship_emojis="")
        embed = discord.Embed(
            title=f"Ship Percentage for {members[0].name} and {members[1].name}",
            description=f"{ship_emojis}Average Ship Value: {ship_percentage}%"
        )
        await edit_message.edit(content=f"{ship_emojis} Here is how much {members[0]} and {members[1]} like each other💕💕", embeds=[embed])

    @commands.hybrid_command(name="ship", help="Ships you and another user!")
    async def ship_user(self, ctx, first_partner: discord.Member, second_partner: discord.Member):
        if second_partner:
            message = await ctx.send("Generating message...")
            await self.generate_ship_image(members=[first_partner, second_partner], edit_message=message)

    @commands.hybrid_command(name="echo", help="Makes the bot say anything, and I mean anything")
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    async def echo_message(self, ctx, *, text="Hello world!"):
        await ctx.message.delete()
        await ctx.send(text)

    async def create_directory(self, dir):
        if not os.path.exists(dir):
            os.mkdir(dir)

    async def convert_attachment(self, attachment_list, output_format, message, scale):
        file_list = []
        for attachment in attachment_list:
            await self.create_directory("jobs")
            await self.create_directory(f"jobs/{attachment.id}/")
            await attachment.save(f"jobs/{attachment.id}/{attachment.filename}")
            p = await create_subprocess_exec("ffmpeg", "-i", f"jobs/{attachment.id}/{attachment.filename}",
                                                 f"jobs/{attachment.id}/output.{output_format}")
            await p.wait()
            file_list.append(discord.File(f"jobs/{attachment.id}/output.{output_format}"))
        await message.edit(content="Your files have been processed!", attachments=file_list)

    @commands.command(name='to',
                      help='Converts one format to another')
    async def to_convert(self, ctx, format="wav", dimensions=""):
        attachment_list = ctx.message.attachments
        if len(attachment_list) <= 10:
            msg = await ctx.send(f"Processing {len(attachment_list)} attachments")
            if dimensions.find("x"):
                string = f"-s {dimensions}"
            else:
                string = ""
            await self.convert_attachment(attachment_list=attachment_list, output_format=format, message=msg, scale=string)
        else:
            await ctx.send("Error: Please specify less than 10 attachments, due to file size constraints we need to do this")

    @commands.hybrid_command(name='d',
                      help='Roles a dice between two values')
    async def roll_dice(self, ctx, number=0, to=6):
        roll = random.randint(number, to)
        await ctx.send(f"🎲 | You rolled a {roll}!")
    
    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        message = reaction.message
        data = await data_parser.get_guild_data(user.guild.id)
        starboard_embed = discord.Embed(
            title=f"{message.author.name} - Starboard Message",
            description=f"Starboard by: <@{message.author.id}>\n\n{message.content}",
        )
        logging.info(str(reaction.count))
        if reaction.count >= data["starboard"]["max"] and reaction.emoji == data["starboard"]["emoji"]:
            channel_obj = discord.utils.get(message.guild.channels, id=data["starboard"]["channel"])
            await channel_obj.send(f"⭐{reaction.count} | {message.content}", embeds=[starboard_embed])

async def setup(bot): # this is called by Pycord to setup the cog
    cog = FunOrRandom(bot)
    await bot.add_cog(cog) # add the cog to the bot
