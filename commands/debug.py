import logging
import discord
from discord.ext import commands
from common import CommandParser, OtherParser

embed_system = CommandParser()
parser1 = OtherParser()
# Best not to edit these!
class Debug(commands.Cog):
    @commands.hybrid_command(description="Testing command for TunaCat. Shows latency and other information")
    async def hello(self, ctx):
        # Check latency, database ping, and other information
        await ctx.send("Pinged bot successfully!", embed=(await embed_system.generate_embed(title="Pong!", desc=f"Information for {ctx.bot.user.name}", fields=[
            {
                "name": "Bot Latency",
                "value": str(round(ctx.bot.latency, 2)) + "ms"
            }
        ])))
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error: discord.DiscordException):
        # Returns error id, which contains the guild ID, message ID, and ID for the user who sent a message
        error_id = str(ctx.guild.id)
        logging.info(f'Error occurred with ID: {error_id}')
        logging.info(f"Caused by: {error.args}")
        # Sends a full report to the user on the error, including error args
        await ctx.send("An issue occurred. Error ID: " + error_id, embed=await embed_system.generate_embed(title="An unknown issue occurred", desc=str(error.args)+ f"\n\nIf this problem repeatly occurs, see [our support server]({parser1.config['invite']})"))
        # Raises an error and returns it.
        raise error

async def setup(bot):
    # Runs to check if the cog exists, since on_ready is usually called twice.
    cog_obj = Debug(bot)
    if bot.get_cog(cog_obj.__cog_name__) is None:
        logging.info(f"The Cog {cog_obj.__cog_name__} is being added...")
        await bot.add_cog(cog_obj)