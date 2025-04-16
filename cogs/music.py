import asyncio
import datetime
import logging
import os
import random
import time

import discord
import mafic
from discord.ext import commands, tasks
import typing
import json
import psutil
import common
import common.parsers

default_prefix = common.parsers.GuildParser().config

class Audio(commands.Cog):
    """
    Commands for playing music and audio! Works per-server as well
    """

    def __init__(self, bot): # this is a special method that is called when the cog is loaded
        self.bot = bot
    jobs = []
    async def check_and_connect(self, voice_channel, vc):
        if voice_channel and vc is None:
            vc = await voice_channel.connect(cls=mafic.Player)
            return vc

    async def get_emoji(self, emoji, guild):
        return "🎶"

    async def add_playlist(self, songs, vc, limit):
            song_list = ""
            duration = 0
            for i in songs:
                duration += 1
                if duration <= limit:
                    logging.info("Indexed song: " + i.title)
                    
                    song_list += f'{i.title}; '
                    if vc.current is not None:
                        await vc.play(i, replace=False)
                    else:
                        self.jobs.append({vc.guild.id: i})
                    songs = str(song_list)[:90]
                else:
                    break
            logging.info(vc)
            logging.info(songs)
            return songs

    async def generate_tip(self, g):
        emoji = await self.get_emoji(emoji="sunny_idea", guild=g.id)
        json_data = json.loads(open('settings/tips.json').read())
        return f'{emoji} TIP: {random.choice(json_data)}'

    async def play_song_lavalink(self, ctx, search, limit, loop_song=False):
        vc = typing.cast(mafic.Player, ctx.voice_client)

        # Now we are going to check if the invoker of the command
        # is in the same voice channel than the voice client, when defined.
        # If not, we return an error message.
        if ctx.author.voice.channel.id != vc.channel.id:
            return await ctx.send(f"{await self.get_emoji (guild=ctx.guild.id, emoji='sunny_thinking')} | You must be in the same voice channel as the bot.")

        # Now we search for the song. You can optionally
        # pass the "source" keyword, of type "wavelink.TrackSource"
        song = await vc.fetch_tracks(query=search)

        if not song:  # In case the song is not found
            return await ctx.send(f"{await self.get_emoji (guild=ctx.guild.id, emoji='sunny_thinking')} | No song found.")  # we return an error message

        if vc.current is None:
            song_data = await self.add_playlist(songs=song, vc=vc, limit=limit)
            await ctx.send(f"{await self.get_emoji (guild=ctx.guild.id, emoji='sunny_thumbsup')} | Now playing: `{song_data}` ({limit} total songs)\n{await self.generate_tip(g=ctx.guild)}")  # and return a success message
        else:
            song_data = await self.add_playlist(songs=song, vc=vc, limit=limit)
            await ctx.send(f"{await self.get_emoji (guild=ctx.guild.id, emoji='sunny_idea')} | Added `{song_data}` to queue ({limit} total songs)\n{await self.generate_tip(g=ctx.guild)}")  # and return a success message
        logging.info(vc.current)


    # @commands.cooldown(6, 10, commands.BucketType.guild)
    # @commands.hybrid_command(name='loop',
    #                          help='loop the current audio playing, or the current song in the queue')
    # async def loop_song(self, ctx):
    #     if ctx.voice_client:
    #         vc = typing.cast(wavelink.Player, ctx.voice_client)
    #     else:
    #         vc = await self.check_and_connect(voice_channel=ctx.author.voice.channel, vc=None)
    #     if vc.current:
    #         vc.current.extras = ExtrasNamespace(
    #             {
    #                 "loop": True
    #             }
    #         )
    #         await ctx.send(
    #             f"{await self.get_emoji(guild=ctx.guild.id, emoji='sunny_thumbsup')} | Now looping: {vc.current.title}")
    #         logging.info(vc.current.extras)
    #     elif vc.queue.is_empty:
    #         await ctx.send(
    #             f"{await self.get_emoji(guild=ctx.guild.id, emoji='sunny_thinking')} | The queue is empty.")
    #     elif vc.queue.get():
    #         vc.queue.get().extras = ExtrasNamespace(
    #             {
    #                 "loop": True
    #             }
    #         )
    #         logging.info(vc.queue.get().extras)
    #         await ctx.send(
    #             f"{await self.get_emoji(guild=ctx.guild.id, emoji='sunny_thumbsup')} | Now looping: {vc.queue.get().title}")
    #     else:
    #         await ctx.send(
    #             f"{await self.get_emoji(guild=ctx.guild.id, emoji='sunny_thinking')} | Please check if there is a song in progress then try again.")

    @commands.cooldown(5, 20, commands.BucketType.guild)
    @commands.hybrid_command(name='play',
                   help='Plays a music url in a voice channel')
    async def play_audio(self, ctx, term, song_limit=1):
        song_limit_int = song_limit
        await self.check_and_connect(voice_channel=ctx.author.voice.channel, vc=ctx.voice_client)
        if song_limit_int <= 12:
            await self.play_song_lavalink(ctx=ctx, search=term, limit=song_limit_int)
        else:
            await self.play_song_lavalink(ctx=ctx, search=term, limit=12)
            await ctx.send(f"{await self.get_emoji (guild=ctx.guild.id, emoji='sunny_thinking')} | Unfortunately we limit playlists to 12 songs due to rate limits, hosting issues, etc.\nWe are very sorry for this. ***Please limit the songs to 12 or less***")
    @commands.cooldown(6, 10, commands.BucketType.guild)
    @commands.hybrid_command(name='pause',
                      help='Pause the current audio playing')
    async def pause(self, ctx):
        if ctx.voice_client is not None:
            vc = typing.cast(mafic.Player, ctx.voice_client)
            vc.pause(not vc.paused)
            await ctx.send(f"{await self.get_emoji (guild=ctx.guild.id, emoji='sunny_jamming')} | Paused currently playing audio\n{await self.generate_tip(g=ctx.guild)}")
        else:
            await ctx.send(f"{await self.get_emoji (guild=ctx.guild.id, emoji='sunny_thinking')}> | There is no audio currently playing!")
            pass


    @commands.cooldown(1, 5, commands.BucketType.guild)
    @commands.hybrid_command(name='connect',
                   help='Makes the bot join a voice channel.')
    async def connect(self, ctx):
        voice_channel = ctx.message.author.voice.channel
        try:
            await self.check_and_connect(voice_channel=voice_channel, vc=ctx.voice_client)
            await ctx.channel.send(
                f"{await self.get_emoji (guild=ctx.guild.id, emoji='sunny_thumbsup')} | Joined Voice Channel successfully!\n{await self.generate_tip(g=ctx.guild)}")
        except discord.ClientException:
            await ctx.channel.send(f"{await self.get_emoji (guild=ctx.guild.id, emoji='sunny_thinking')} | An client error happened! Try stopping and starting the song.")

    @commands.cooldown(1, 5, commands.BucketType.guild)
    @commands.hybrid_command(name='disconnect',
                   help='Makes the bot leave a voice channel.')
    async def disconnect(self, ctx):
        try:
            await ctx.voice_client.disconnect()
            await ctx.channel.send(f"{await self.get_emoji (guild=ctx.guild.id, emoji='sunny_thumbsup')} | Left voice channel\n{await self.generate_tip(g=ctx.guild)}")
        except discord.ClientException:
            await ctx.channel.send(f"{await self.get_emoji (guild=ctx.guild.id, emoji='sunny_thinking')} | An client error happened! Try stopping and starting the song.")

    @commands.hybrid_command(name='stop', help='Stop audio that is currently playing.')
    async def stop_audio(self, ctx):
        voice_channel = ctx.message.author.voice.channel
        if voice_channel:
                await ctx.voice_client.stop()
                await ctx.channel.send(f"{await self.get_emoji (guild=ctx.guild.id, emoji='sunny_jamming')} | Stopped the playing track\n{await self.generate_tip(g=ctx.guild)}")
                return
        else:
            await ctx.channel.send(f"{await self.get_emoji (guild=ctx.guild.id, emoji='sunny_thinking')} | No voice channel exists. Try reconnecting or join a different voice channel and reconnect the bot.")

    @commands.hybrid_command(name='playing', help='Sees the song that is in the queue.')
    async def get_audio_stat(self, ctx):
        if ctx.voice_client is not None:
            playing_song = ctx.voice_client.current
        else:
            playing_song = None
        if playing_song is not None:
            playing_embed = discord.Embed(
                title=f"Currently playing: {playing_song.title}",
                description=f"{str(datetime.timedelta(milliseconds=playing_song.position))} - From {playing_song.source}"
            )
            await ctx.send(f"{await self.get_emoji (guild=ctx.guild.id, emoji='sunny_jamming')} | Playing [{playing_song.title}]({playing_song.uri}) by {playing_song.author}\n{await self.generate_tip(g=ctx.guild)}", embed=playing_embed)
        else:
            await ctx.send("Song could not be found. Double check that the bot is connected to a voice channel and playing, then try again.")

    @commands.hybrid_command(name='debug', help='A user command that gets debug information about the bot.')
    async def get_audio_lag(self, ctx):
        if ctx.voice_client:
            vc = typing.cast(mafic.Player, ctx.voice_client)
            embed = discord.Embed(
                title=f"Serving on node {vc.node.label} (Ping: {vc.ping}ms)",
                description=f"Channel: {vc.channel.mention} | Position: {str(datetime.timedelta(milliseconds=vc.position))} | Playing: {vc.current.title}",
            )
            for j in self.jobs:
                i = j[ctx.guild.id]
                if i is not None:
                    embed.add_field(name=i.title,
                                    value=f"{str(datetime.timedelta(milliseconds=i.position))} - From {i.source}")
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"{await self.get_emoji (guild=ctx.guild.id, emoji='sunny_thinking')} | There is no voice client connected")

    @commands.hybrid_command(name='list', help='List all songs in queue.')
    async def list_jobs(self, ctx):
        if ctx.voice_client:
            vc = typing.cast(mafic.Player, ctx.voice_client)
            if vc.current:
                string_data = f"> {vc.current}"
            else:
                string_data = ""
            for i in self.jobs:
                string_data += f"\n{i.title}"
            await ctx.send(
                f"{await self.get_emoji(guild=ctx.guild.id, emoji='sunny_thumbsup')} | Here are all the songs in the queue:```{string_data[:2000]}```")
        else:
            await ctx.send(f"{await self.get_emoji (guild=ctx.guild.id, emoji='sunny_thinking')} | You need to be in a channel with the bot!")

    @commands.hybrid_command(name='volume', help='Sets the volume of the currently playing song.')
    async def change_song_volume(self, ctx, *, volume=50):
        if ctx.voice_client:
            vc = typing.cast(mafic.Player, ctx.voice_client)
            await vc.set_volume(volume)
            await ctx.send(f"{await self.get_emoji (guild=ctx.guild.id, emoji='sunny_thumbsup')} | Volume is now {str(volume)}!")
        else:
            await ctx.send(f"{await self.get_emoji (guild=ctx.guild.id, emoji='sunny_thinking')} | You need to be in a channel with the bot!")

    async def avatar_is_equal(self, img):
        if( self.bot.user.avatar == img) and (psutil.cpu_percent() < 70) and (datetime.date.month != 12) and (datetime.date.month != 3):
            return True


    async def update_status(self):
        total = len(self.bot.voice_clients)
        await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.playing,
                                             name=f'Music in {total} servers! | {default_prefix}help'))

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        await self.update_status()
    

    @commands.Cog.listener()
    async def track_end(self, event: mafic.TrackEndEvent):
        logging.info("Continuing next song!")
        for j in self.jobs:
            i = j[event.player.guild.id]
            if (event.player.current is None):
                event.player.play(i, replace=False)

async def setup(bot): # this is called by Pycord to setup the cog
    cog = Audio(bot)
    await bot.add_cog(cog) # add the cog to the bot
    logging.info("started auto-player")