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
        dest_channel = bot.get_channel(DEST_CHANNEL_ID)
        
        if not dest_channel:
            print(f"Error: Destination channel {DEST_CHANNEL_ID} not found")
            return
        
        # Check for embeds (the mob alerts are embed messages)
        if message.embeds:
            for embed in message.embeds:
                # Check if it's a super mob alert
                if embed.title and ("super" in embed.title.lower() or "spawn" in embed.title.lower()):
                    # Create a relay message
                    embed_text = f"🚨 **SUPER MOB ALERT!** 🚨\n"
                    
                    if embed.title:
                        embed_text += f"**{embed.title}**\n"
                    if embed.description:
                        embed_text += f"{embed.description}\n"
                    
                    # Add field values
                    if embed.fields:
                        for field in embed.fields:
                            embed_text += f"**{field.name}:** {field.value}\n"
                    
                    await dest_channel.send(embed_text)
                    print(f"Relayed super mob alert: {embed.title}")
        
        # Also check plain text messages just in case
        elif message.content:
            content = message.content.lower()
            if any(keyword in content for keyword in ["super", "spawn", "mob alert"]):
                await dest_channel.send(f"📢 **Mob Alert:**\n{message.content}")
                print(f"Relayed text message: {message.content[:50]}...")
    
    await bot.process_commands(message)

# Run the bot
if BOT_TOKEN:
    bot.run(BOT_TOKEN)
else:
    print("ERROR: DISCORD_TOKEN environment variable not set!")
