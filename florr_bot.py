import discord
from discord.ext import commands, tasks
import aiohttp
import json
from datetime import datetime

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Configuration
BOT_TOKEN = "MTQ3NDg5MTkxMzkyMzY2MjAwNg.G_snR8.ScycqvYZGwzVcdTLfMBsgjJn-XM3i7Ht52MP5A"  # Replace this with your actual token
SERVER_ID = 1473465801536307200
CHANNEL_ID = 1473465801536307203
WEBSITE_URL = "https://mobs.ashish.top/"

# Store previous mob states to detect changes
mob_states = {}

async def get_mob_data():
    """Fetch mob data from the website"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(WEBSITE_URL, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    # Try to find mob data in the HTML
                    # This is a basic approach - you may need to adjust based on actual page structure
                    return parse_mob_data(html)
    except Exception as e:
        print(f"Error fetching website: {e}")
    return {}

def parse_mob_data(html):
    """Parse mob data from HTML - adjust based on actual page structure"""
    mobs = {}
    try:
        # Look for common patterns that might contain mob data
        # This is a placeholder - you'll need to adjust based on actual HTML structure
        if "petal" in html.lower():
            mobs["petal"] = "alive"
        if "wasp" in html.lower():
            mobs["wasp"] = "alive"
        # Add more mob patterns as needed
    except Exception as e:
        print(f"Error parsing mob data: {e}")
    return mobs

@bot.event
async def on_ready():
    print(f"{bot.user} has logged in!")
    monitor_mobs.start()

@tasks.loop(seconds=15)
async def monitor_mobs():
    """Check for mob changes every 15 seconds"""
    try:
        current_mobs = await get_mob_data()
        
        if not current_mobs:
            print("No mob data found - website may be loading or structure changed")
            return
        
        # Check for new or changed mobs
        for mob_name, mob_status in current_mobs.items():
            if mob_name not in mob_states:
                # New mob spawned!
                channel = bot.get_channel(CHANNEL_ID)
                if channel:
                    await channel.send(f"🚨 **SUPER MOB ALERT!** 🚨\n{mob_name} has spawned!\nStatus: {mob_status}")
                mob_states[mob_name] = mob_status
            elif mob_states[mob_name] != mob_status:
                # Mob status changed
                channel = bot.get_channel(CHANNEL_ID)
                if channel:
                    await channel.send(f"📢 **{mob_name}** status changed to: {mob_status}")
                mob_states[mob_name] = mob_status
    
    except Exception as e:
        print(f"Error in monitor_mobs: {e}")

# Run the bot
bot.run(BOT_TOKEN)


