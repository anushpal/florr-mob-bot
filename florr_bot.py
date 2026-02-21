import discord
from discord.ext import commands, tasks
import aiohttp
from bs4 import BeautifulSoup
import os

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Configuration
BOT_TOKEN = os.getenv("DISCORD_TOKEN")
DEST_CHANNEL_ID = 1473465801536307203
WEBSITE_URL = "https://mobs.ashish.top/"

# Track previous mob states
mob_states = {}

async def get_mob_data():
    """Fetch and parse mob data from the website"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(WEBSITE_URL, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    mobs = {}
                    
                    # Try to find mob data in the page
                    # Look for any text that contains mob names
                    text = soup.get_text().lower()
                    
                    # Common florr.io mob names to search for
                    mob_names = ['petal', 'wasp', 'bee', 'ant', 'termite', 'mosquito', 
                                 'ladybug', 'spider', 'moth', 'tick', 'fly', 'hornets',
                                 'soldier termite', 'baby termite', 'super']
                    
                    for mob in mob_names:
                        if mob in text:
                            mobs[mob] = "active"
                    
                    return mobs
    except Exception as e:
        print(f"Error fetching mob data: {e}")
    return {}

@bot.event
async def on_ready():
    print(f"{bot.user} has logged in!")
    check_mobs.start()

@tasks.loop(seconds=10)
async def check_mobs():
    """Check for new mobs every 10 seconds"""
    try:
        current_mobs = await get_mob_data()
        
        if not current_mobs:
            print("No mob data found")
            return
        
        dest_channel = bot.get_channel(DEST_CHANNEL_ID)
        if not dest_channel:
            print(f"Error: Destination channel not found")
            return
        
        # Check for new mobs
        for mob_name, status in current_mobs.items():
            if mob_name not in mob_states:
                # New mob detected!
                await dest_channel.send(f"🚨 **SUPER MOB ALERT!** 🚨\n**{mob_name}** has spawned!")
                print(f"Alert sent for: {mob_name}")
                mob_states[mob_name] = status
            elif mob_states[mob_name] != status:
                # Status changed
                await dest_channel.send(f"📢 **{mob_name}** status: {status}")
                mob_states[mob_name] = status
    
    except Exception as e:
        print(f"Error in check_mobs: {e}")

# Run the bot
if BOT_TOKEN:
    bot.run(BOT_TOKEN)
else:
    print("ERROR: DISCORD_TOKEN environment variable not set!")
