import discord
from discord.ext import commands, tasks
import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Configuration
BOT_TOKEN = "MTQ3NDg5MTkxMzkyMzY2MjAwNg.GsgdG6.ojf0wZqh_YvUZH9dpPsGLKNgWIkT9NhGS1bB1E"
SERVER_ID = 1473465801536307200
CHANNEL_ID = 1473465801536307203
WEBSITE_URL = "https://mobs.ashish.top/"

# Store previous mob states to detect changes
mob_states = {}

async def get_mob_data():
    """Scrape mob data from the website using browser automation"""
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(WEBSITE_URL, wait_until="networkidle")
            
            # Wait for mob data to load
            await page.wait_for_timeout(2000)
            
            # Extract mob data from the page
            mob_data = await page.evaluate("""
                () => {
                    const mobs = {};
                    // Look for mob elements - adjust selectors based on actual page structure
                    const mobElements = document.querySelectorAll('[class*="mob"], [class*="status"]');
                    
                    mobElements.forEach(el => {
                        const name = el.textContent.trim();
                        const status = el.getAttribute('class') || 'unknown';
                        if (name) {
                            mobs[name] = status;
                        }
                    });
                    
                    return mobs;
                }
            """)
            
            await browser.close()
            return mob_data
    except Exception as e:
        print(f"Error scraping website: {e}")
        return {}

@bot.event
async def on_ready():
    print(f"{bot.user} has logged in!")
    monitor_mobs.start()

@tasks.loop(seconds=10)
async def monitor_mobs():
    """Check for mob changes every 10 seconds"""
    try:
        current_mobs = await get_mob_data()
        
        if not current_mobs:
            print("No mob data found")
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
