import discord
from discord.ext import commands
import os

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Configuration - Get token from environment variable
BOT_TOKEN = os.getenv("DISCORD_TOKEN")

# Source channel (where the other bot posts alerts)
SOURCE_SERVER_ID = 1464027414953857159
SOURCE_CHANNEL_ID = 1467606628173086770

# Destination channel (where we relay alerts)
DEST_CHANNEL_ID = 1473465801536307203

@bot.event
async def on_ready():
    print(f"{bot.user} has logged in!")
    print(f"Listening to channel {SOURCE_CHANNEL_ID} in server {SOURCE_SERVER_ID}")
    print(f"Relaying to channel {DEST_CHANNEL_ID}")

@bot.event
async def on_message(message):
    """Listen for messages in the source channel and relay them"""
    
    # Don't relay our own messages
    if message.author == bot.user:
        return
    
    # Check if message is from the source channel
    if message.channel.id == SOURCE_CHANNEL_ID:
        # Check if it's a mob alert (contains keywords)
        content = message.content.lower()
        if any(keyword in content for keyword in ["mob", "spawn", "alert", "super"]):
            # Get destination channel
            dest_channel = bot.get_channel(DEST_CHANNEL_ID)
            
            if dest_channel:
                # Relay the message
                await dest_channel.send(f"📢 **Mob Alert from other server:**\n{message.content}")
                print(f"Relayed message: {message.content[:50]}...")
    
    await bot.process_commands(message)

# Run the bot
if BOT_TOKEN:
    bot.run(BOT_TOKEN)
else:
    print("ERROR: DISCORD_TOKEN environment variable not set!")
