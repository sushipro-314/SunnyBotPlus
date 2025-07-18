import logging
import random

import aiohttp
import discord
from common.parsers import GuildParser
from discord.ext import commands

data_parser = GuildParser()

class Games(commands.Cog):
    def __init__(self, bot): # this is a special method that is called when the cog is loaded
        self.bot = bot
    session=aiohttp.ClientSession()

    """
        [BETA] Games that use APIs. (Currently only features commands for pokemon data)
    """

    @commands.hybrid_group(name='poke', help='Query Information about the pokemon franchise.',
                           invoke_without_subcommand=False)
    async def pokemon(self, ctx, name):
        pass

    @pokemon.command(name='get', help='Get information about a specific pokemon.')
    async def get_pokemon(self, ctx, pokemon_name):
        resp = await self.session.get(f"https://pokeapi.co/api/v2/pokemon/{pokemon_name}")
        json_data = await resp.json()
        poke_embed = discord.Embed(
            title=f"Pokemon Information for {json_data['name']}",
            description=f"Weight: {json_data['weight']} | ID: {json_data['id']}",
        )
        duration = 0
        for m in json_data["moves"]:
            duration += 1
            if duration <= 10:
                move = m["move"]
                poke_embed.add_field(name=move["name"], value=f"Move URL: {str(move['url'])}")
            else:
                break
        poke_embed.set_image(url=json_data["sprites"]["front_default"])
        poke_embed.set_footer(text="Powered by PokeAPI")
        await ctx.send(embeds=[poke_embed])

    @pokemon.command(name='type', help='Get information about a pokemon type.')
    async def get_type(self, ctx, type_name):
        resp = await self.session.get(f"https://pokeapi.co/api/v2/type/{str(type_name)}")
        json_data = await resp.json()
        poke_embed = discord.Embed(
            title=f"Pokemon Information for {json_data['name']}",
            description=f"Damage Class: {json_data['move_damage_class']['name'][0]} | ID: {json_data['id']}",
        )
        duration = 0
        for p in json_data["pokemon"]:
            duration += 1
            if duration <= 8:
                pokemon = p["pokemon"]
                poke_embed.add_field(name=pokemon['name'], value=f"Pokemon URL: {str(pokemon['url'])}")
            else:
                break
        poke_embed.set_footer(text="Powered by PokeAPI")
        await ctx.send(embeds=[poke_embed])

    @pokemon.command(name='move', help='Get information about a pokemon move.')
    async def get_move(self, ctx, move_name):
        resp = await self.session.get(f"https://pokeapi.co/api/v2/move/{str(move_name)}")
        json_data = await resp.json()
        poke_embed = discord.Embed(
            title=f"Pokemon Information for {json_data['name']}",
            description=f"Damage Class: {json_data['damage_class']['name'][0]} | ID: {json_data['id']}",
        )
        duration = 0
        for effect in json_data["effect_entries"]:
            pokemon = effect
            poke_embed.add_field(name=effect['language']['name'].upper(), value=f"{effect['effect']}")
        poke_embed.set_footer(text="Powered by PokeAPI")
        await ctx.send(embeds=[poke_embed])
    
    async def vaildate_json(self, user_data, member: discord.Member, guild_data):
        return (user_data is not None) and user_data["uid"] and (guild_data is not None) and (guild_data.get("xp_gain") and guild_data.get('xp_cost')) and (user_data["uid"] == member.id) and not member.bot
    
    async def fetch_user_levels(self, member: discord.Member, guild_data=None):
        json_data = await data_parser.get_member_data(member=member)
        if json_data is None:
            json_data = await data_parser.write_member_data(member=member, data={
                    "uid": member.id,
                    "xp": 0,
                    "rank": 0,
                    "created": member.created_at
                })
            return json_data
        else:
            if not guild_data:
                guild_data = await data_parser.get_guild_data(member.guild.id)
            return json_data
    
    @commands.hybrid_group(help="Configurate rank data for this server.", invoke_without_subcommand=False)
    async def rankconfig(self, ctx):
        pass
    
    @commands.hybrid_group(help="View rank information.")
    async def rank(self, ctx):
        member_obj = (ctx.message.author)
        json_data = await self.fetch_user_levels(member=member_obj)
        rank_embed = discord.Embed(
                title=f"Ranking information for **{[member_obj.name if member_obj else 'Unknown'][0]}**",
                description=f"User <@{json_data['uid']}> is currently level **{str(json_data['rank'])}**. This member has **{str(json_data['xp'])}** XP!"
            )
        await ctx.send(embeds=[rank_embed])
    
    @rankconfig.command(help="Set a channel to recieve rank-ups from members")
    @commands.has_permissions(manage_guild=True)
    async def setchannel(self, ctx, channel: discord.TextChannel):
        guild_data = await data_parser.get_guild_data(ctx.guild.id)
        if guild_data is not None:
            guild_data["rank_channel"] = channel.id
            write_data = await data_parser.write_guild_data(channel.guild.id, data=guild_data)
            await ctx.send("Successfully added rank-up channel to " + (await channel.guild.fetch_channel(write_data["rank_channel"])).name)
        else:
            logging.error("Failed to set rank channel: guild data not found")
            await ctx.send("Guild data was not found. Please try again or reinvite the bot.")
    
    @rankconfig.command(help="Remove the channel that recieves rank-ups from members")
    @commands.has_permissions(manage_guild=True)
    async def remchannel(self, ctx, channel: discord.TextChannel):
        guild_data = await data_parser.get_guild_data(ctx.guild.id)
        if guild_data is not None:
            del guild_data["rank_channel"]
            write_data = await data_parser.write_guild_data(channel.guild.id, data=guild_data)
            await ctx.send("Successfully added rank-up channel to " + (await channel.guild.fetch_channel(write_data["rank_channel"])).name)
        else:
            logging.error("Failed to set rank channel: guild data not found")
            await ctx.send("Guild data was not found. Please try again or reinvite the bot.")
    
    @rankconfig.command(help="Set the amount of XP earned per message")
    @commands.has_permissions(manage_guild=True)
    async def setgain(self, ctx, xp: int):
        guild_data = await data_parser.get_guild_data(ctx.guild.id)
        if guild_data is not None:
            guild_data["xp_gain"] = xp
            write_data = await data_parser.write_guild_data(ctx.guild.id, data=guild_data)
            await ctx.send("Successfully set xp gain amount to " + str(write_data["xp_gain"]))
        else:
            logging.error("Failed to set rank channel: guild data not found")
            await ctx.send("Guild data was not found. Please try again or reinvite the bot.")
    
    @rankconfig.command(help="Set the amount of XP required for leveling up members")
    @commands.has_permissions(manage_guild=True)
    async def setcost(self, ctx, xp: int):
        guild_data = await data_parser.get_guild_data(ctx.guild.id)
        if guild_data is not None:
            guild_data["xp_cost"] = xp
            write_data = await data_parser.write_guild_data(ctx.guild.id, data=guild_data)
            await ctx.send("Successfully set xp gain amount to " + str(write_data["xp_cost"]))
        else:
            logging.error("Failed to set rank channel: guild data not found")
            await ctx.send("Guild data was not found. Please try again or reinvite the bot.")
    
    @rankconfig.command(help="Sets the current rank for a member")
    @commands.has_permissions(manage_guild=True)
    async def set(self, ctx, member: discord.Member, rank=0):
        user_data = await self.fetch_user_levels(member=member, guild_data=ctx.guild)
        if user_data is not None:
            user_data["rank"] = rank
            write_data = await data_parser.write_member_data(member=member, data=user_data)
            await ctx.send("Successfully set member rank for"+member.name)
        else:
            logging.error("Failed to set rank channel: user data not found")
            await ctx.send("User was not found.")
    
    @rankconfig.command(help="Sets the current amount of xp for a member")
    @commands.has_permissions(manage_guild=True)
    async def setxp(self, ctx, member: discord.Member, xp=10):
        user_data = await self.fetch_user_levels(member=member, guild_data=ctx.guild)
        if user_data is not None:
            user_data["xp"] = xp
            write_data = await data_parser.write_member_data(member=member, data=user_data)
            await ctx.send(embeds=[
                discord.Embed(
                    title="Successfully set member rank for " + member.name,
                    description="User XP is now **" + str(write_data["xp"]) + "**"
                )
            ])
        else:
            logging.error("Failed to set rank channel: guild data not found")
            await ctx.send("Guild data was not found. Bot may have to rejoin the server!")
    
    @rankconfig.command(help="Adds a role for when a user levels up.")
    @commands.has_permissions(manage_guild=True)
    async def addrole(self, ctx, role: discord.Role, amount_until=100):
        guild_data = await data_parser.get_guild_data(ctx.guild.id)
        if guild_data is not None:
            if guild_data.get("rank_roles") is None:
                guild_data["rank_roles"] = [{"id": role.id, "amount": amount_until }]
            else:
                guild_data["rank_roles"].append({"id": role.id, "amount": amount_until})
            await data_parser.write_guild_data(ctx.guild.id, data=guild_data)
            await ctx.send("Added role data to ranking roles! Users can now get this role when they level up!")
        else:
            logging.error("Failed to set rank channel: guild data not found")
            await ctx.send("Guild data was not found.")

    @rankconfig.command(help="Lists all roles for leveling up users.")
    @commands.has_permissions(manage_guild=True)
    async def viewroles(self, ctx):
        guild_data = await data_parser.get_guild_data(ctx.guild.id)
        if guild_data is not None:
            rank_role_strings = []
            if guild_data.get("rank_roles") is None:
                guild_data["rank_roles"] = []
                await data_parser.write_guild_data(ctx.guild.id, data=guild_data)
            else:
                for role_data in guild_data["rank_roles"]:
                    if role_data.get("id") and role_data.get("amount"):
                        logging.info("Removing role data for matching role")
                        rank_role_strings.append(discord.Embed(
                            title=str(role_data.get("id")),
                            description=f"Users can obtain this role at level {str(role_data.get('amount'))}!"
                        ))
                    else:
                        logging.info("Skipping role because it does not match.")
                await ctx.send("The following roles are for leveling up!", embeds=rank_role_strings)
        else:
            logging.error("Failed to set rank channel: guild data not found")
            await ctx.send("Guild data was not found.")
    
    @rankconfig.command(help="Lists all roles for leveling up users.")
    @commands.has_permissions(manage_guild=True)
    async def viewinfo(self, ctx):
        guild_data = await data_parser.get_guild_data(ctx.guild.id)
        if guild_data is not None:
            rank_role_strings = ""
            if guild_data.get("rank_roles") is None:
                guild_data["rank_roles"] = []
                await data_parser.write_guild_data(ctx.guild.id, data=guild_data)
            for r in guild_data["rank_roles"]:
                rank_role_strings += "ID: " + str(r['id']) + "\nLevel: " + str(r["amount"]) + "\n"
            embed_info = discord.Embed(
                            title=f"Ranking Information for server {ctx.guild.name}",
                    )
            embed_info.add_field(name="XP Cost", value=str(guild_data['xp_cost']))
            embed_info.add_field(name="XP Gain", value=str(guild_data["xp_gain"]))
            embed_info.add_field(name="Notification Channel", value="<#" + str(guild_data['rank_channel']) + ">")
            embed_info.add_field(name="Rank-up Roles", value=rank_role_strings)
            await ctx.send(embeds=[embed_info])
        else:
            logging.error("Failed to set rank channel: guild data not found")
            await ctx.send("Guild data was not found.")

    @rankconfig.command(help="Removes a role for when a user levels up.")
    @commands.has_permissions(manage_guild=True)
    async def remrole(self, ctx, role: discord.Role):
        guild_data = await data_parser.get_guild_data(ctx.guild.id)
        if guild_data is not None:
            if guild_data.get("rank_roles") is None:
                guild_data["rank_roles"] = []
            else:
                for role_data in guild_data["rank_roles"]:
                    if role_data.get("id") and (role_data.get("id") == role.id):
                        logging.info("Removing role data for matching role")
                        guild_data["rank_roles"].remove(role_data)
                    else:
                        logging.info("Skipping role because it does not match.")
            await data_parser.write_guild_data(ctx.guild.id, data=guild_data)
            await ctx.send("Removed role data to ranking roles! Users can no longer get this role when they level up!")
        else:
            logging.error("Failed to set rank channel: guild data not found")
            await ctx.send("Guild data was not found.")

    async def level_up_user(self, json_data, guild_data, member_obj):
        json_data['xp'] = 0
        json_data['rank'] += 1
        if guild_data and guild_data.get("rank_channel"):
            await (await member_obj.guild.fetch_channel(guild_data["rank_channel"])).send(embeds=[discord.Embed(
                title=f"{member_obj.display_name} has leveled up to level " + str(json_data["rank"]),
                description=f"User <@{json_data['uid']}> is currently level **{json_data['rank']}** now! Congratulations!"
            )])

    @commands.Cog.listener()
    @commands.guild_only()
    async def on_message(self, message):
        member_obj = message.author
        logging.info("Checking levels for user... Member ID: " + str(member_obj.id))
        json_data = await self.fetch_user_levels(member=member_obj)
        guild_data = await data_parser.get_guild_data(guild_id=member_obj.guild.id)
        if (await self.vaildate_json(json_data, member_obj, guild_data)):
            json_data['xp'] += guild_data['xp_gain']
            if (guild_data.get("rank_roles") is not None) and len(guild_data["rank_roles"]) > 0:
                for role in guild_data["rank_roles"]:
                    if json_data["rank"] >= role["amount"]:
                        try:
                            await self.bot.add_roles(message.guild.get_role(role["id"]))
                        except Exception:
                            logging.warn("Unable to add role to user even though user has correct levels. Be sure the bot has proper permissions.")
            if (json_data['xp'] >= guild_data["xp_cost"]):
                await self.level_up_user(json_data=json_data, guild_data=guild_data, member_obj=member_obj)
            await data_parser.write_member_data(member=member_obj, data=json_data)
        else:
            logging.error("Could not validate leveling info for member... Member ID: " + str(json_data['uid']) + "... Displaying error information")
            logging.error(str(json_data) + "\n" + str(guild_data) + "\n" + str(member_obj))

async def setup(bot):  # this is called by Pycord to setup the cog
    await bot.add_cog(Games(bot))  # add the cog to the bot