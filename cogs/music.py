import asyncio
import datetime
import logging
import os
import random
import time

import discord
import wavelink
from discord.ext import commands, tasks
import typing
import json
import psutil
from gtts import gTTS
import common.parsers
from wavelink import ExtrasNamespace
from wavelink.types.tracks import TrackPayload, TrackInfoPayload

parsers = [common.parsers.GuildParser(), common.parsers.ConfigParser()]
default_prefix = parsers[0].config["prefix"]
config = parsers[0].config
db = parsers[0].db

class Audio(commands.Cog):
    """
    Commands for playing music and audio! Works per-server as well
    """

    def __init__(self, bot): # this is a special method that is called when the cog is loaded
        self.bot = bot
    jobs = []

    async def check_and_connect(self, voice_channel: discord.VoiceChannel, vc, tts=False):
        if voice_channel and vc is None:
            voice = await voice_channel.connect(cls=wavelink.Player, self_deaf=True)
            return voice

    async def get_emoji(self, emoji, guild):
        emoji_obj = "🎶"
        return str(emoji_obj)

    async def add_playlist(self, songs, vc, limit):
            song_list = ""
            duration = 0
            for i in songs:
                duration += 1
                if duration <= limit:
                    vc.queue.put(i)
                    song_list += f'{i.title}; '
                    songs = str(song_list)[:90]
                else:
                    break
            if not vc.playing:
                await vc.play(vc.queue.get())
            vc.current.extras = ExtrasNamespace(
                {
                    "loop": False
                }
            )
            logging.info(vc)
            logging.info(songs)
            return songs

    async def generate_tip(self, g):
        emoji = await self.get_emoji(emoji="sunny_idea", guild=g.id)
        json_data = json.loads(open('settings/tips.json').read())
        return f'{emoji} TIP: {random.choice(json_data)}'

    async def play_song_lavalink(self, ctx, search, limit, loop_song=False):
        vc = typing.cast(wavelink.Player, ctx.voice_client)

        # Now we are going to check if the invoker of the command
        # is in the same voice channel than the voice client, when defined.
        # If not, we return an error message.
        if ctx.author.voice.channel.id != vc.channel.id:
            return await ctx.send(f"{await self.get_emoji (guild=ctx.guild.id, emoji='sunny_thinking')} | You must be in the same voice channel as the bot.")

        # Now we search for the song. You can optionally
        # pass the "source" keyword, of type "wavelink.TrackSource"
        if search.split(":"):
            song = await wavelink.Playable.search(search)
        else:
            song = await wavelink.Playable.search("ytsearch:" + search)

        if not song:  # In case the song is not found
            return await ctx.send(f"{await self.get_emoji (guild=ctx.guild.id, emoji='sunny_thinking')} | No song found.")  # we return an error message

        if not vc.playing:
            song_data = await self.add_playlist(songs=song, vc=vc, limit=limit)
            await ctx.send(f"{await self.get_emoji (guild=ctx.guild.id, emoji='sunny_thumbsup')} | Now playing: `{song_data}` ({limit} total songs)\n{await self.generate_tip(g=ctx.guild)}")  # and return a success message
        else:
            song_data = await self.add_playlist(songs=song, vc=vc, limit=limit)
            await ctx.send(f"{await self.get_emoji (guild=ctx.guild.id, emoji='sunny_idea')} | Added `{song_data}` to queue ({limit} total songs)\n{await self.generate_tip(g=ctx.guild)}")  # and return a success message
        logging.info(vc.current)
        logging.info(vc.queue)


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
            vc = typing.cast(wavelink.Player, ctx.voice_client)
            await ctx.voice_client.pause(not vc.paused)
            await ctx.send(f"{await self.get_emoji (guild=ctx.guild.id, emoji='sunny_jamming')} | Paused currently playing audio\n{await self.generate_tip(g=ctx.guild)}")
        else:
            await ctx.send(f"{await self.get_emoji (guild=ctx.guild.id, emoji='sunny_thinking')}> | There is no audio currently playing!")
            pass


    @commands.cooldown(1, 5, commands.BucketType.guild)
    @commands.hybrid_command(name='connect',
                   help='Makes the bot join a voice channel.')
    async def connect(self, ctx, tts=False):
        voice_channel = ctx.message.author.voice.channel
        try:
            await self.check_and_connect(voice_channel=voice_channel, vc=ctx.voice_client, tts=tts)
            await ctx.send(
                f"{await self.get_emoji (guild=ctx.guild.id, emoji='sunny_thumbsup')} | Joined Voice Channel successfully!\n{await self.generate_tip(g=ctx.guild)}")
        except discord.ClientException:
            await ctx.channel.send(f"{await self.get_emoji (guild=ctx.guild.id, emoji='sunny_thinking')} | An client error happened! Try stopping and starting the song.")

    @commands.cooldown(1, 5, commands.BucketType.guild)
    @commands.hybrid_command(name='disconnect',
                   help='Makes the bot leave a voice channel.')
    async def disconnect(self, ctx):
        try:
            await typing.cast(wavelink.Player, ctx.voice_client).disconnect()
            await ctx.send(f"{await self.get_emoji (guild=ctx.guild.id, emoji='sunny_thumbsup')} | Left voice channel\n{await self.generate_tip(g=ctx.guild)}")
        except discord.ClientException:
            await ctx.send(f"{await self.get_emoji (guild=ctx.guild.id, emoji='sunny_thinking')} | An client error happened! Try stopping and starting the song.")

    @commands.hybrid_command(name='stop', help='Stop audio that is currently playing.')
    async def stop_audio(self, ctx):
        voice_channel = ctx.message.author.voice.channel
        if voice_channel:
                await ctx.voice_client.stop()
                await ctx.send(f"{await self.get_emoji (guild=ctx.guild.id, emoji='sunny_jamming')} | Stopped the playing track\n{await self.generate_tip(g=ctx.guild)}")
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
            vc = typing.cast(wavelink.Player, ctx.voice_client)
            if vc.current:
                embed = discord.Embed(
                    title=f"Serving on node {vc.node.identifier} (Ping: {vc.ping}ms)",
                    description=f"Channel: {vc.channel.mention} | Position: {str(datetime.timedelta(milliseconds=vc.position))} | Playing: {vc.current.title}",
                )
                for i in vc.queue:
                    if i is not None:
                        embed.add_field(name=i.title,
                                    value=f"{str(datetime.timedelta(milliseconds=i.length))} - From {i.source}")
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"{await self.get_emoji (guild=ctx.guild.id, emoji='sunny_thinking')} | Nothing is playing!")
        else:
            await ctx.send(f"{await self.get_emoji (guild=ctx.guild.id, emoji='sunny_thinking')} | There is no voice client connected")

    @commands.hybrid_command(name='list', help='List all songs in queue.')
    async def list_queue(self, ctx):
        if ctx.voice_client:
            vc = typing.cast(wavelink.Player, ctx.voice_client)
            if vc.current:
                string_data = f"> {vc.current}"
            else:
                string_data = ""
            for i in vc.queue:
                string_data += f"\n{i.title}"
            await ctx.send(
                f"{await self.get_emoji(guild=ctx.guild.id, emoji='sunny_thumbsup')} | Here are all the songs in the queue:```{string_data[:2000]}```")
        else:
            await ctx.send(f"{await self.get_emoji (guild=ctx.guild.id, emoji='sunny_thinking')} | You need to be in a channel with the bot!")

    @commands.hybrid_command(name='seek', help='Seeks to the seconds in the currently playing song.')
    async def seek_audio(self, ctx, seconds: int):
        if ctx.voice_client and ctx.voice_client.current:
            vc = typing.cast(wavelink.Player, ctx.voice_client)
            await vc.seek(seconds * 1000)
            await ctx.send(f"{await self.get_emoji (guild=ctx.guild.id, emoji='sunny_thumbsup')} | Successfully seeked to position {datetime.timedelta(milliseconds=vc.current.position)}!")
        else:
            await ctx.send(f"{await self.get_emoji (guild=ctx.guild.id, emoji='sunny_thinking')} | You need to be in a channel with the bot and playing music!")

    @commands.hybrid_command(name='clear', help='Clears all songs in queue.')
    async def reset_queue(self, ctx):
        if ctx.voice_client:
            vc = typing.cast(wavelink.Player, ctx.voice_client)
            vc.queue.reset()
            await ctx.send(f"{await self.get_emoji (guild=ctx.guild.id, emoji='sunny_thumbsup')} | Successfully cleared the queue!")
        else:
            await ctx.send(f"{await self.get_emoji (guild=ctx.guild.id, emoji='sunny_thinking')} | You need to be in a channel with the bot!")

    @commands.hybrid_command(name='remove', help='Remove a song in the queue.')
    async def remove_song(self, ctx, idx: int):
        if ctx.voice_client:
            vc = typing.cast(wavelink.Player, ctx.voice_client)
            vc.queue.delete(int(idx + 1))
            await ctx.send(f"{await self.get_emoji (guild=ctx.guild.id, emoji='sunny_thumbsup')} | Removing!")
        else:
            await ctx.send(f"{await self.get_emoji (guild=ctx.guild.id, emoji='sunny_thinking')} | You need to be in a channel with the bot!")

    @commands.hybrid_command(name='volume', help='Sets the volume of the currently playing song.')
    async def change_song_volume(self, ctx, *, volume=50):
        if ctx.voice_client:
            vc = typing.cast(wavelink.Player, ctx.voice_client)
            await vc.set_volume(volume)
            await ctx.send(f"{await self.get_emoji (guild=ctx.guild.id, emoji='sunny_thumbsup')} | Volume is now {str(vc.volume)}!")
            logging.info(vc.volume)
        else:
            await ctx.send(f"{await self.get_emoji (guild=ctx.guild.id, emoji='sunny_thinking')} | You need to be in a channel with the bot!")

    async def avatar_is_equal(self, img):
        if( self.bot.user.avatar == img) and (psutil.cpu_percent() < 70) and (datetime.date.month != 12) and (datetime.date.month != 3):
            return True

    async def update_status(self):
        total = len(self.bot.voice_clients)
        await asyncio.sleep(9)
        await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.playing,
                                             name=f'Music in {total} servers! | {default_prefix}help'))

    
    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload: wavelink.TrackEndEventPayload):
        logging.info(str(payload))
        await self.update_status()
    
    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackEndEventPayload):
        logging.info(str(payload))
        await self.update_status()
        extra_data = dict(payload.track.extras)
        if payload.player and not payload.player.playing and not payload.player.queue.is_empty and payload.player.connected:
            await payload.player.play(payload.player.queue.get())
        # elif extra_data.get("loop") is not None and extra_data.get("loop") is True:
        #     await payload.player.play(payload.track)

    @commands.Cog.listener()
    async def on_wavelink_inactive_player(self, player: wavelink.Player) -> None:
        if player and player.guild:
            await player.channel.send(f"{await self.get_emoji (guild=player.guild.id, emoji='sunny_thinking')} | The player has been inactive for `{player.inactive_timeout}` seconds. We need to disconnect due to practical reasons, hosting costs, etc. Thank you!\n{await self.generate_tip(g=player.guild)}")
            await player.disconnect()

async def setup(bot): # this is called by Pycord to setup the cog
    cog = Audio(bot)
    nodes = []
    for node in config['uris']["lavalink"]:
        nodes.append(wavelink.Node(
            identifier=node["name"],
            uri=node["host"] + ":" + str(node["port"]),
            password=node['pass'],
            inactive_player_timeout=(node.get("timeout") or 300)
        ))
    await wavelink.Pool.connect(nodes=nodes, client=bot)
    await bot.add_cog(cog) # add the cog to the bot
    logging.info("Connected to nodes!")