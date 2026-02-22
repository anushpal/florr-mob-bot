import asyncio
from playwright.async_api import async_playwright
from discord.ext import commands
import discord
import os
import aiohttp
from datetime import datetime, timedelta

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = 1473465801536307200
CHANNEL_ID = 1473477387642732655

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot logged in as {bot.user}")
    bot.loop.create_task(monitor_mobs())

async def monitor_mobs():
    """Monitor mobs.ashish.top for super mob spawns"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        detected_mobs = set()
        
        async def on_response(response):
            """Capture responses when super mobs appear"""
            url = response.url
            if "petal-" in url and "-super.png" in url:
                try:
                    mob_filename = url.split("/")[-1].split("?")[0]
                    
                    if mob_filename not in detected_mobs:
                        detected_mobs.add(mob_filename)
                        await send_spawn_notification(url, mob_filename)
                except Exception as e:
                    print(f"Error: {e}")
        
        page.on("response", on_response)
        
        try:
            await page.goto("https://mobs.ashish.top/", wait_until="networkidle")
            print("📡 Listening for petal-*-super.png spawns...")
            while True:
                await asyncio.sleep(1)
        except Exception as e:
            print(f"Monitor error: {e}")

async def send_spawn_notification(image_url, mob_filename):
    """Send Discord notification with image"""
    guild = bot.get_guild(GUILD_ID)
    if not guild:
        return
    
    channel = guild.get_channel(CHANNEL_ID)
    if not channel:
        return
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as resp:
                image_data = await resp.read()
        
        mob_name = mob_filename.replace("petal-", "").replace("-super.png", "").replace("_", " ").title()
        
        embed = discord.Embed(
            title="🚨 SUPER MOB SPAWN 🚨",
            description=f"**{mob_name}**",
            color=discord.Color.red()
        )
        embed.add_field(name="⏱️ Despawns in", value="~30 seconds", inline=False)
        
        image_path = f"/tmp/{mob_filename}"
        with open(image_path, "wb") as f:
            f.write(image_data)
        
        with open(image_path, "rb") as f:
            await channel.send(content="@everyone", embed=embed, file=discord.File(f, filename=mob_filename))
        
        print(f"✅ Sent: {mob_name}")
        
    except Exception as e:
        print(f"Error sending: {e}")
        try:
            await channel.send(f"@everyone 🚨 **{mob_filename}**")
        except:
            pass

bot.run(TOKEN)
