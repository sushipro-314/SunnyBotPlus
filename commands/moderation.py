import logging
import discord
from discord.ext import commands, tasks
import datetime
import uuid
from common import CommandParser, OtherParser, db

# Command Parsing Object // TODO: rename embed_system to command_ something something
embed_system = CommandParser()
#Misc parsing object
other_parser = OtherParser()

# Moderation cog. Check todo.md for information on what needs to be done!
class Moderation(commands.Cog):
    async def write_punishment_data(self, user, seconds: int, source):
        # Inserts a database entry for punishing the user
        await db.get_database("tuna").get_collection("punishments").insert_one({"uuid": str(uuid.uuid4()), "gid": user.guild.id, "uid": user.id, "duration": seconds, "type": source})
    
    async def get_punishment_data(self, uuid):
        # Get a database entry from the user
        return await db.get_database("tuna").get_collection("punishments").find_one({"uuid": uuid})
    
    async def remove_punishment_data(self, uuid):
        # Inserts a database entry for punishing the user
        return (await db.get_database("tuna").get_collection("punishments").delete_one({"uuid":uuid})).raw_result

    @commands.bot_has_guild_permissions(ban_members=True)
    # Properly checks the current guild permissions
    @commands.has_guild_permissions(ban_members=True)
    @commands.hybrid_command(description="Bans the current user!")
    async def ban(self, ctx, member: discord.Member, reason="An unknown reason!"):
        # Bans a user from the guilds.
        await ctx.guild.ban(user=member, reason=f"{member.display_name} ({member.global_name}) has been automatically banned for {reason}")
        await ctx.send(content="", embed=(await embed_system.generate_embed(title="Banned user", desc=f"***{member.display_name} has been banned***", fields=[{"name": "Reason", "value": reason}])))
    
    @commands.bot_has_guild_permissions(ban_members=True)
    # Properly checks the current guild permissions
    @commands.has_guild_permissions(ban_members=True)
    @commands.hybrid_command(description="Unbans the current user!")
    async def unban(self, ctx, user: discord.User, reason="An unknown reason!"):
        # Unbans the user from the guild
        await ctx.guild.unban(user=user, reason=f"{user.display_name} ({user.global_name}) has been unbanned for {reason}")
        await ctx.send(content="", embed=(await embed_system.generate_embed(title="Unbanned user", desc=f"***{user.display_name} has been unbanned***", fields=[{"name": "Reason", "value": reason}])))
    
    @commands.bot_has_guild_permissions(kick_members=True)
    # Properly checks the current guild permissions
    @commands.has_guild_permissions(kick_members=True)
    @commands.hybrid_command(description="Kicks the current user!")
    async def kick(self, ctx, member: discord.Member, reason="An unknown reason!"):
        # Kicks the user from the guilds
        await ctx.guild.kick(user=member, reason=f"{member.display_name} ({member.global_name}) has been automatically kicked for {reason}")
        await ctx.send(content="", embed=(await embed_system.generate_embed(title="Kicked user", desc=f"***{member.display_name} has been kicked***", fields=[{"name": "Reason", "value": reason}])))

    # TODO Make the tempban command work
    # Commented out for now. Please uncomment later

    # @commands.bot_has_guild_permissions(kick_members=True)
    # # Properly checks the current guild permissions
    # @commands.has_guild_permissions(kick_members=True)
    # @commands.hybrid_command(description="Tempbans the user.")
    # async def tempban(self, ctx, user: discord.Member, seconds=20, reason="An unknown reason!"):
    #     # Tempbans the user
    #     await ctx.guild.ban(user=user, reason=f"{user.name} has been temporarily banned for '{reason}'")
    #     #This first line writes the data for the punishment!
    #     await self.write_punishment_data(user=user, seconds=seconds, source="TEMPBAN")
    #     # Sends the embedded message telling moderators in chat
    #     await ctx.send(content="", embed=(await embed_system.generate_embed(title="Banned user", desc=f"***Temporary ban has been activated for {user.global_name}***", fields=[{"name": "Reason", "value": reason}])))


    # @tasks.loop(seconds=10)
    # async def reload_punishments(self, bot):
    #     # Checks all expired punishments, like when a tempban expires
    #     logging.info("Checking for expired punishments!")
    #     async for g in bot.fetch_guilds():
    #         # Fetching the tempbans for the current guild
    #         data_punish = await db.get_database("tuna").get_collection("punishments").find({"gid": g.id}).to_list()
    #         data_punishments = data_punish[0]
    #         logging.info(data_punishments)
    #         # Checks some information like if the punishment doesn't exist, and when it's time to unban them
    #         if (data_punishments is not None) and isinstance(data_punishments['duration'], int) and (int(data_punishments["duration"]) >= datetime.datetime.now().second):
    #             data_user = await g.fetch_member(data_punishments["uid"])
    #             try:
    #                 if data_punishments["type"] == "TEMPBAN":
    #                     g.unban(user=data_user, reason="Tempban has Expired")
    #                 await db.get_database("tuna").get_collection("punishments").delete_many({"uid": data_user.id})
    #             except:
    #                 await db.get_database("tuna").get_collection("punishments").delete_many({"uid": data_user.id})
    #                 logging.info("Error loading tempban occcurred...Clearing database")

    @commands.bot_has_guild_permissions(kick_members=True)
    # Properly checks the current guild permissions
    @commands.has_guild_permissions(kick_members=True)
    @commands.hybrid_command(description="Gives a member a warning")
    async def warn(self, ctx, member: discord.Member, reason="An unknown reason!"):
        # Writes the warnings to a database
        await self.write_punishment_data(user=member, seconds=None, source="WARN")
        await ctx.send(content="", embed=(await embed_system.generate_embed(title="Warned user", desc=f"User {member.display_name} has been warned for {reason}", fields=[{"name": "Reason", "value": reason}])))

    @commands.bot_has_guild_permissions(kick_members=True)
    # Properly checks the current guild permissions
    @commands.has_guild_permissions(kick_members=True)
    @commands.hybrid_command(description="Removes a member's warning")
    async def unwarn(self, ctx, uuid: str, reason="An unknown reason!"):
        # Removes the warnings from a database
        result = await self.get_punishment_data(uuid=uuid)
        member = await ctx.guild.fetch_member(result.get("uid"))
        await ctx.send(content="", embed=(await embed_system.generate_embed(title="Removed warn for user", desc=f"User {member.display_name} has been unwarned for {reason}", fields=[{"name": "Reason", "value": reason}])))
        await self.remove_punishment_data(uuid=uuid)

    @commands.bot_has_guild_permissions(kick_members=True)
    # Properly checks the current guild permissions
    @commands.has_guild_permissions(kick_members=True)
    @commands.hybrid_command(description="List cases for a user")
    async def cases(self, ctx, member: discord.Member):
        cursor = db.get_database("tuna").get_collection("punishments").find({"gid": ctx.guild.id, "uid": member.id})
        cases = await cursor.to_list()
        case_fields= []
        for case in cases:
            if case.get('reason') is not None:
                case_reason= case['reason']
            else:
                case_reason = "Unknown Reason"
            case_fields.append({"name": case['type'] + " -- " + str(case["uuid"]), "value": case_reason})
        await ctx.send(content="", embed=(await embed_system.generate_embed(title=f"Cases for {member.name}", desc="Here are the moderation cases", fields=case_fields)))

async def setup(bot):
    # Runs to check if the cog exists, since on_ready is usually called twice.
    cog_obj = Moderation(bot)
    if bot.get_cog(cog_obj.__cog_name__) is None:
        logging.info(f"The Cog {cog_obj.__cog_name__} is being added...")
        await bot.add_cog(cog_obj)
