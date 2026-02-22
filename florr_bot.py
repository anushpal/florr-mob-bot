import asyncio
import subprocess
import sys
from playwright.async_api import async_playwright
from discord.ext import commands
import discord
import os
import aiohttp
import traceback
from datetime import datetime

# Install dependencies AND browsers
print("[STARTUP] Installing system dependencies...")
subprocess.run(["playwright", "install-deps"], check=False, timeout=300, capture_output=True)
print("[STARTUP] Installing Playwright browsers...")
subprocess.run(["playwright", "install"], check=False, timeout=300, capture_output=True)
print("[STARTUP] Ready to go\n")

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = 1473465801536307200
CHANNEL_IDS = [1473477387642732655, 1473465801536307203]

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"\n[SUCCESS] Bot logged in as: {bot.user}")
    print(f"[INFO] Monitoring {len(CHANNEL_IDS)} channels\n")
    
    # Send startup message
    for ch_id in CHANNEL_IDS:
        try:
            guild = bot.get_guild(GUILD_ID)
            channel = guild.get_channel(ch_id)
            if channel:
                embed = discord.Embed(
                    title="Online",
                    description="Watching for super mobs",
                    color=discord.Color.green()
                )
                await channel.send(embed=embed)
        except:
            pass
    
    bot.loop.create_task(monitor_mobs())

async def monitor_mobs():
    detected = set()
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-gpu"])
            page = await browser.new_page()
            
            async def on_response(response):
                try:
                    url = response.url
                    if "petal-" in url and "-super.png" in url:
                        mob_file = url.split("/")[-1].split("?")[0]
                        if mob_file not in detected:
                            detected.add(mob_file)
                            print(f"[MOB] {mob_file}")
                            asyncio.create_task(send_alert(url, mob_file))
                except:
                    pass
            
            page.on("response", on_response)
            
            print("[INFO] Loading page...")
            await page.goto("https://mobs.ashish.top/", wait_until="networkidle")
            print("[INFO] Listening...\n")
            
            # Reload page every 2 minutes to catch new mobs
            while True:
                await asyncio.sleep(120)
                try:
                    print("[INFO] Reloading page...")
                    await page.reload(wait_until="networkidle")
                except:
                    pass
    
    except Exception as e:
        print(f"[ERROR] {e}")
        await asyncio.sleep(30)
        bot.loop.create_task(monitor_mobs())

async def send_alert(url, mob_file):
    """Send ONE clean message per mob"""
    guild = bot.get_guild(GUILD_ID)
    mob_name = clean_mob_name(mob_file)
    
    # Download image
    image_data = None
    try:
        async with aiohttp.ClientSession() as s:
            resp = await asyncio.wait_for(s.get(url, timeout=10), timeout=15)
            if resp.status == 200:
                image_data = await resp.read()
    except:
        pass
    
    # Send to both channels
    for ch_id in CHANNEL_IDS:
        try:
            channel = guild.get_channel(ch_id)
            
            # Create embed
            embed = discord.Embed(
                title="SUPER MOB SPAWN",
                description=f"**{mob_name}**",
                color=discord.Color.red()
            )
            embed.set_footer(text="Despawns in ~30 seconds")
            
            # Send with image if available
            if image_data:
                image_path = f"/tmp/{mob_file}"
                with open(image_path, "wb") as f:
                    f.write(image_data)
                with open(image_path, "rb") as f:
                    await asyncio.wait_for(
                        channel.send(f"@everyone", embed=embed, file=discord.File(f, mob_file)),
                        timeout=10
                    )
            else:
                # Just embed if no image
                await asyncio.wait_for(
                    channel.send(f"@everyone", embed=embed),
                    timeout=10
                )
            
            print(f"[SENT] {mob_name} to {ch_id}")
        except Exception as e:
            print(f"[ERROR] {ch_id}: {e}")
        
        await asyncio.sleep(0.5)

def clean_mob_name(filename):
    return filename.replace("petal-", "").replace("-super.png", "").replace("_", " ").title()

print("FLORR MOB BOT ONLINE\n")
bot.run(TOKEN)
