import datetime
import json
import datetime

import discord
import logging

from click import pass_context
from discord.abc import Snowflake
from discord.ext import commands, tasks
import os


class Moderation(commands.Cog):
    """
    Commands for moderating your discord server!!
    """

    def __init__(self, bot):  # this is a special method that is called when the cog is loaded
        self.bot = bot

    muted_users = []

    @commands.hybrid_command(name='ban', help="Bans a user")
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def ban_user(self, ctx, member: discord.Member, reason="Unspecified", delete_sec=0):
        await member.ban(delete_message_seconds=delete_sec, reason=reason)
        embed = discord.Embed(
            description=f"🚓 | User {member.global_name} was banned from server {ctx.guild.name} successfully",
            title=f"User {member.display_name} was banned")
        await ctx.send(embed=embed)
        return

    @commands.hybrid_command(name='voicekick', help="Kicks a user from the voice channel")
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    async def voice_kick_user(self, ctx, member: discord.Member, reason="Unspecified"):
        await member.move_to(None)
        message = await ctx.send(content="🚓 | Kicking user...")
        embed = discord.Embed(
            description=f"🚓 | Kicked user {member.global_name} from {member.voice.channel.mention}",
            title=f"User {member.display_name} was kicked from voice"
        )
        message.edit(content="🚓 | Kicked User!", embed=embed)
        return

    @commands.hybrid_command(name='kick', help="Kicks a user from the server")
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    async def kick_user(self, ctx, member: discord.Member, reason="Unspecified"):
        await member.kick(reason=reason)
        embed = discord.Embed(
            description=f"🚓 | User {member.global_name} was kicked from server {ctx.guild.name} successfully",
            title=f"User {member.display_name} was kicked")
        await ctx.send(embed=embed)
        return

    @commands.hybrid_command(name='purge', help="Purge a certain amount of messages in a channel.")
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def purge_msgs(self, ctx, count=1, channel_id=None):
        if channel_id is not None:
            channel_obj = await self.bot.fetch_channel(int(channel_id))
        else:
            channel_obj = ctx.channel
        await channel_obj.purge(limit=count)
        embed = discord.Embed(description=f"🚓 | Purged {str(count)} messages in channel #{channel_obj.name}.",
                              title=f"<#{channel_obj.id}> - Purged {str(count)} messages")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='slowmode', help="Set the channel slowmode")
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    async def slowmode_channel(self, ctx, channel: discord.TextChannel, seconds=0,
                               reason="Unspecified"):
        await channel.edit(slowmode_delay=seconds, reason=reason)
        embed = discord.Embed(
            description=f"🚓 | Channel <#{channel.id}> had their slow mode set to {seconds} seconds successfully",
            title=f"Set slow mode for {channel.name} in server {ctx.guild.name}")
        await ctx.send(embed=embed)
        return

    @commands.hybrid_command(name='logs', help="Lists audit logs entries for a member")
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    async def view_member(self, ctx, member: discord.Member, limit=30):
        audit_log_string = ""
        message = await ctx.send("🔎 | Fetching information...", silent=True)
        async for entry in ctx.guild.audit_logs(limit=10):
            if entry.user.id == member.id and entry.user and entry.target:
                audit_log_string += f"Moderator {entry.user.name} took action {str(entry.action)} on {str(entry.target)}\nReason: {entry.reason}\n\n"
        await message.edit(content=f"```{audit_log_string[:1800]}```-------\nHere are the audit logs fetched for this user")

    async def get_member_number(self, member: discord.Member):
        member_count = 0
        for m in member.guild.members:
            if m is member:
                break
            else:
                member_count += 1
        return member_count

    @commands.hybrid_group(name="info", help="Information command for checking servers & Member", invoke_without_command=False)
    async def info(self, ctx):
        pass

    @info.command(name="member", help="Gets info about a member")
    async def get_member(self, ctx, member: discord.Member):
        embed = discord.Embed(
            description=f"🚓 | Information: {member.global_name} ({member.display_name}",
            title=f"User information for {str(member)}")
        embed.add_field(name="User Number", value=f'User {member.display_name} is member number #{await self.get_member_number(member=member)}')
        embed.add_field(name="Roles", value=f'User has the following roles: ```{str(member.roles[:300])}```')
        embed.set_footer(text=f"Member ID: {str(member.id)} | Created at: <t:{str(member.created_at.timestamp())}:F> | Server: {member.guild.name}")
        await ctx.send(embed=embed)

    @info.command(name="server", help="Gets info about the current server/guild")
    async def get_guild(self, ctx):
        embed = discord.Embed(
            description=f"🚓 | Information: {ctx.guild.name}",
            title=f"Guild information for {ctx.guild.name} owned by {str(ctx.guild.owner)}")
        embed.add_field(name="Roles", value=f'The following roles are in the guild: ```{str(ctx.guild.roles)[:100]}```')
        embed.set_footer(text=f"Server ID: {ctx.guild.id} | Created at: <t:{str(ctx.guild.created_at.timestamp())}:F>")
        await ctx.send(embed=embed)


async def setup(bot): # this is called by Pycord to setup the cog
    await bot.add_cog(Moderation(bot))  # add the cog to the bot
