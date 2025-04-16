import logging
import random

import aiohttp
import discord
from discord.ext import commands


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

    @pokemon.command(name='get', help='Get information about a specific pokemon.', invoke_without_subcommand=False)
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

    @pokemon.command(name='type', help='Get information about a pokemon type.', invoke_without_subcommand=False)
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

    @pokemon.command(name='move', help='Get information about a pokemon move.', invoke_without_subcommand=False)
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

async def setup(bot):  # this is called by Pycord to setup the cog
    await bot.add_cog(Games(bot))  # add the cog to the bot