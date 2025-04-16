import os

from discord.ext import commands
from pymongo import AsyncMongoClient


class Template(commands.Cog):
    def __init__(self, bot): # this is a special method that is called when the cog is loaded
        self.bot = bot

    @commands.command(name='test', help='Test command.')
    async def test_command(self, ctx, text):
        await ctx.send("Test: " + text)

async def setup(bot):  # this is called by Pycord to setup the cog
    await bot.add_cog(Template(bot))  # add the cog to the bot