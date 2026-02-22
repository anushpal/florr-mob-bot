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
CHANNEL_IDS = [1473477387642732655, 1473465801536307203]  # Both channels

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"\n[SUCCESS] Bot logged in as: {bot.user}")
    print(f"[INFO] Guild ID: {GUILD_ID}")
    print(f"[INFO] Channels: {CHANNEL_IDS}\n")
    
    # Send startup message to both channels
    for ch_id in CHANNEL_IDS:
        try:
            guild = bot.get_guild(GUILD_ID)
            if guild:
                channel = guild.get_channel(ch_id)
                if channel:
                    embed = discord.Embed(
                        title="Bot Online",
                        description="Monitoring for super mobs...",
                        color=discord.Color.green()
                    )
                    await channel.send(embed=embed)
                    print(f"[SUCCESS] Sent startup message to channel {ch_id}")
        except Exception as e:
            print(f"[ERROR] Could not send startup message to {ch_id}: {e}")
    
    # Start monitoring
    bot.loop.create_task(monitor_mobs())

async def monitor_mobs():
    print("[INFO] Starting mob monitor loop...\n")
    detected = set()
    retry_count = 0
    max_retries = 10
    
    while retry_count < max_retries:
        try:
            print("[INFO] Launching Playwright browser...")
            async with async_playwright() as p:
                browser = await asyncio.wait_for(
                    p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-gpu"]),
                    timeout=45
                )
                print("[SUCCESS] Browser launched")
                
                page = await browser.new_page()
                print("[SUCCESS] Page created")
                
                async def on_response(response):
                    try:
                        url = response.url
                        if "petal-" in url and "-super.png" in url:
                            mob_file = url.split("/")[-1].split("?")[0]
                            if mob_file not in detected:
                                detected.add(mob_file)
                                print(f"\n[SUPER MOB] Detected: {mob_file}\n")
                                asyncio.create_task(send_mob_alert(url, mob_file))
                    except Exception as e:
                        print(f"[ERROR] on_response error: {e}")
                
                page.on("response", on_response)
                
                print("[INFO] Navigating to mobs.ashish.top...")
                try:
                    await asyncio.wait_for(
                        page.goto("https://mobs.ashish.top/", wait_until="networkidle", timeout=20),
                        timeout=25
                    )
                    print("[SUCCESS] Page loaded")
                except asyncio.TimeoutError:
                    print("[WARNING] Page load timeout - continuing anyway")
                except Exception as e:
                    print(f"[ERROR] Navigation failed: {e}")
                
                print("[SUCCESS] LISTENING FOR SUPER MOB SPAWNS\n")
                retry_count = 0
                
                while True:
                    await asyncio.sleep(1)
        
        except Exception as e:
            retry_count += 1
            print(f"\n[ERROR] Monitor crashed (attempt {retry_count}/{max_retries})")
            print(f"[ERROR] {e}")
            
            if retry_count < max_retries:
                wait_time = min(5 * retry_count, 30)
                print(f"[INFO] Retrying in {wait_time} seconds...\n")
                await asyncio.sleep(wait_time)

async def send_mob_alert(url, mob_file):
    """Send mob alert with 10+ fallback methods to BOTH channels"""
    guild = bot.get_guild(GUILD_ID)
    if not guild:
        print(f"[ERROR] Guild {GUILD_ID} not found")
        return
    
    mob_name = clean_mob_name(mob_file)
    
    # Send to both channels
    for ch_id in CHANNEL_IDS:
        channel = guild.get_channel(ch_id)
        if not channel:
            print(f"[ERROR] Channel {ch_id} not found")
            continue
        
        await send_to_channel(channel, url, mob_file, mob_name)
        await asyncio.sleep(1)  # Delay between channels to avoid rate limit

async def send_to_channel(channel, url, mob_file, mob_name):
    """Try 10+ methods to send message"""
    
    # METHOD 1: Full featured (embed + image + ping)
    try:
        print(f"[SEND-1] Downloading image...")
        async with aiohttp.ClientSession() as session:
            response = await asyncio.wait_for(session.get(url, timeout=10), timeout=15)
            if response.status == 200:
                image_data = await response.read()
                if image_data and len(image_data) > 0:
                    print(f"[SEND-1] Image downloaded ({len(image_data)} bytes)")
                    embed = discord.Embed(title="SUPER MOB SPAWN", description=f"**{mob_name}**", color=discord.Color.red())
                    image_path = f"/tmp/{mob_file}"
                    with open(image_path, "wb") as f:
                        f.write(image_data)
                    with open(image_path, "rb") as f:
                        await asyncio.wait_for(channel.send(content="@everyone", embed=embed, file=discord.File(f, mob_file)), timeout=10)
                    print(f"[SUCCESS] Method 1: Sent with image and ping\n")
                    return
    except Exception as e:
        print(f"[SEND-1] Failed: {e}")
    
    await asyncio.sleep(0.5)
    
    # METHOD 2: Embed + ping (no image)
    try:
        print(f"[SEND-2] Sending embed with ping...")
        embed = discord.Embed(title="SUPER MOB SPAWN", description=f"**{mob_name}**", color=discord.Color.red())
        await asyncio.wait_for(channel.send(content="@everyone", embed=embed), timeout=10)
        print(f"[SUCCESS] Method 2: Sent embed with ping\n")
        return
    except Exception as e:
        print(f"[SEND-2] Failed: {e}")
    
    await asyncio.sleep(0.5)
    
    # METHOD 3: Plain text + ping
    try:
        print(f"[SEND-3] Sending text with ping...")
        await asyncio.wait_for(channel.send(f"@everyone **SUPER MOB: {mob_name}**"), timeout=10)
        print(f"[SUCCESS] Method 3: Sent text with ping\n")
        return
    except Exception as e:
        print(f"[SEND-3] Failed: {e}")
    
    await asyncio.sleep(0.5)
    
    # METHOD 4: Text without ping
    try:
        print(f"[SEND-4] Sending text without ping...")
        await asyncio.wait_for(channel.send(f"**SUPER MOB: {mob_name}**"), timeout=10)
        print(f"[SUCCESS] Method 4: Sent text without ping\n")
        return
    except Exception as e:
        print(f"[SEND-4] Failed: {e}")
    
    await asyncio.sleep(0.5)
    
    # METHOD 5: Just the name
    try:
        print(f"[SEND-5] Sending just name...")
        await asyncio.wait_for(channel.send(f"SUPER MOB: {mob_name}"), timeout=10)
        print(f"[SUCCESS] Method 5: Sent name\n")
        return
    except Exception as e:
        print(f"[SEND-5] Failed: {e}")
    
    await asyncio.sleep(0.5)
    
    # METHOD 6: Uppercase
    try:
        print(f"[SEND-6] Sending uppercase...")
        await asyncio.wait_for(channel.send(f"ALERT: {mob_name.upper()}"), timeout=10)
        print(f"[SUCCESS] Method 6: Sent uppercase\n")
        return
    except Exception as e:
        print(f"[SEND-6] Failed: {e}")
    
    await asyncio.sleep(0.5)
    
    # METHOD 7: Code block
    try:
        print(f"[SEND-7] Sending in code block...")
        await asyncio.wait_for(channel.send(f"```\nSUPER MOB: {mob_name}\n```"), timeout=10)
        print(f"[SUCCESS] Method 7: Sent in code block\n")
        return
    except Exception as e:
        print(f"[SEND-7] Failed: {e}")
    
    await asyncio.sleep(0.5)
    
    # METHOD 8: With emoji
    try:
        print(f"[SEND-8] Sending with emoji...")
        await asyncio.wait_for(channel.send(f"ALERT {mob_name}"), timeout=10)
        print(f"[SUCCESS] Method 8: Sent with emoji\n")
        return
    except Exception as e:
        print(f"[SEND-8] Failed: {e}")
    
    await asyncio.sleep(0.5)
    
    # METHOD 9: Multiple lines
    try:
        print(f"[SEND-9] Sending multiline...")
        msg = f"SUPER MOB\n{mob_name}\nDESPAWN: 30s"
        await asyncio.wait_for(channel.send(msg), timeout=10)
        print(f"[SUCCESS] Method 9: Sent multiline\n")
        return
    except Exception as e:
        print(f"[SEND-9] Failed: {e}")
    
    await asyncio.sleep(0.5)
    
    # METHOD 10: Reaction test (just ping)
    try:
        print(f"[SEND-10] Sending ping only...")
        await asyncio.wait_for(channel.send("@everyone"), timeout=10)
        print(f"[SUCCESS] Method 10: Sent ping\n")
        return
    except Exception as e:
        print(f"[SEND-10] Failed: {e}")
    
    print(f"[CRITICAL] ALL 10 METHODS FAILED FOR {mob_name}\n")

def clean_mob_name(filename):
    return filename.replace("petal-", "").replace("-super.png", "").replace("_", " ").title()

print("\n" + "="*60)
print("FLORR MOB BOT - STARTING UP")
print("="*60 + "\n")

bot.run(TOKEN)
