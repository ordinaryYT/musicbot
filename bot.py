import os
import asyncio
import discord
from discord.ext import commands
from yt_dlp import YoutubeDL
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Voice stability workarounds
discord.opus.load_opus('libopus.so.0')
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Optimized YTDL configuration
ytdl_format = {
    'format': 'bestaudio/best',
    'extractaudio': True,
    'audioformat': 'mp3',
    'noplaylist': True,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}

ffmpeg_options = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

class VoiceConnectionError(commands.CommandError):
    pass

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="your commands"))

async def ensure_voice(ctx):
    if not ctx.author.voice:
        raise VoiceConnectionError("You need to be in a voice channel.")
    
    if ctx.voice_client:
        if ctx.voice_client.channel != ctx.author.voice.channel:
            await ctx.voice_client.move_to(ctx.author.voice.channel)
    else:
        await ctx.author.voice.channel.connect()

@bot.command()
async def play(ctx, *, query):
    """Plays audio from YouTube"""
    try:
        await ensure_voice(ctx)
        
        ytdl = YoutubeDL(ytdl_format)
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(query, download=False))
        
        if 'entries' in data:
            data = data['entries'][0]
            
        audio_source = discord.FFmpegPCMAudio(data['url'], **ffmpeg_options)
        ctx.voice_client.play(audio_source)
        
        await ctx.send(f"Now playing: {data['title']}")
    except Exception as e:
        await ctx.send(f"Error: {str(e)}")

@bot.command()
async def stop(ctx):
    """Stops playback and leaves voice"""
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
    await ctx.send("Disconnected")

bot.run(os.getenv('DISCORD_TOKEN'))
