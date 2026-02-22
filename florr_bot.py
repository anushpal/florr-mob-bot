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

# Install playwright browsers on startup
print("[STARTUP] Installing Playwright browsers...")
try:
    subprocess.run(["playwright", "install"], check=True, timeout=300, capture_output=True)
    print("[STARTUP] Browsers installed successfully")
except Exception as e:
    print(f"[WARNING] Browser install issue: {e}")

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = 1473465801536307200
CHANNEL_ID = 1473477387642732655

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"\n[SUCCESS] Bot logged in as: {bot.user}")
    print(f"[INFO] Guild ID: {GUILD_ID}")
    print(f"[INFO] Channel ID: {CHANNEL_ID}\n")
    
    # Send startup message
    try:
        guild = bot.get_guild(GUILD_ID)
        if guild:
            channel = guild.get_channel(CHANNEL_ID)
            if channel:
                embed = discord.Embed(
                    title="Bot Online",
                    description="Monitoring for super mobs...",
                    color=discord.Color.green()
                )
                await channel.send(embed=embed)
                print("[SUCCESS] Sent startup message to Discord")
            else:
                print(f"[ERROR] Channel {CHANNEL_ID} not accessible")
        else:
            print(f"[ERROR] Guild {GUILD_ID} not found")
    except Exception as e:
        print(f"[ERROR] Could not send startup message: {e}")
    
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
                
                request_count = 0
                
                async def on_response(response):
                    nonlocal request_count
                    request_count += 1
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
            traceback.print_exc()
            
            if retry_count < max_retries:
                wait_time = min(5 * retry_count, 30)
                print(f"[INFO] Retrying in {wait_time} seconds...\n")
                await asyncio.sleep(wait_time)
            else:
                print("[CRITICAL] Max retries reached")
                await send_error_alert("Monitor crashed - max retries exceeded")

async def send_mob_alert(url, mob_file):
    """Send mob alert with complete fallback chain"""
    guild = bot.get_guild(GUILD_ID)
    if not guild:
        print(f"[ERROR] Guild {GUILD_ID} not found")
        return
    
    channel = guild.get_channel(CHANNEL_ID)
    if not channel:
        print(f"[ERROR] Channel {CHANNEL_ID} not found")
        return
    
    mob_name = clean_mob_name(mob_file)
    
    # METHOD 1: Send with image + embed + @everyone
    try:
        print(f"[SEND-1] Downloading image...")
        async with aiohttp.ClientSession() as s:
            async with asyncio.wait_for(s.get(url, timeout=10), timeout=15) as r:
                if r.status == 200:
                    image_data = await r.read()
                    if image_data and len(image_data) > 0:
                        print(f"[SEND-1] Image downloaded ({len(image_data)} bytes)")
                        
                        embed = discord.Embed(
                            title="SUPER MOB SPAWN",
                            description=f"**{mob_name}**",
                            color=discord.Color.red(),
                            timestamp=datetime.now()
                        )
                        embed.add_field(name="Despawn", value="~30 seconds", inline=True)
                        
                        image_path = f"/tmp/{mob_file}"
                        with open(image_path, "wb") as f:
                            f.write(image_data)
                        
                        with open(image_path, "rb") as f:
                            await channel.send(
                                content="@everyone",
                                embed=embed,
                                file=discord.File(f, mob_file)
                            )
                        print(f"[SUCCESS] Sent with image and ping: {mob_name}\n")
                        return
    except Exception as e:
        print(f"[SEND-1] Failed: {e}")
    
    # METHOD 2: Send embed without image
    try:
        print(f"[SEND-2] Sending embed without image...")
        embed = discord.Embed(
            title="SUPER MOB SPAWN",
            description=f"**{mob_name}**",
            color=discord.Color.red(),
            timestamp=datetime.now()
        )
        embed.add_field(name="Despawn", value="~30 seconds", inline=True)
        
        await asyncio.wait_for(
            channel.send(content="@everyone", embed=embed),
            timeout=10
        )
        print(f"[SUCCESS] Sent embed without image: {mob_name}\n")
        return
    except Exception as e:
        print(f"[SEND-2] Failed: {e}")
    
    # METHOD 3: Send plain message with ping
    try:
        print(f"[SEND-3] Sending plain text with ping...")
        await asyncio.wait_for(
            channel.send(f"@everyone **SUPER MOB: {mob_name}** (despawns in 30 sec)"),
            timeout=10
        )
        print(f"[SUCCESS] Sent as text with ping: {mob_name}\n")
        return
    except Exception as e:
        print(f"[SEND-3] Failed: {e}")
    
    # METHOD 4: Send without ping
    try:
        print(f"[SEND-4] Sending plain text without ping...")
        await asyncio.wait_for(
            channel.send(f"**SUPER MOB: {mob_name}** (despawns in 30 sec)"),
            timeout=10
        )
        print(f"[SUCCESS] Sent as text without ping: {mob_name}\n")
        return
    except Exception as e:
        print(f"[SEND-4] Failed: {e}")
    
    # METHOD 5: Last resort - minimal message
    try:
        print(f"[SEND-5] Last resort - minimal message...")
        await asyncio.wait_for(
            channel.send(f"SUPER MOB: {mob_name}"),
            timeout=10
        )
        print(f"[SUCCESS] Sent minimal message: {mob_name}\n")
        return
    except Exception as e:
        print(f"[SEND-5] FAILED - ALL METHODS EXHAUSTED: {e}\n")

async def send_error_alert(message):
    """Send error notification"""
    try:
        guild = bot.get_guild(GUILD_ID)
        if guild:
            channel = guild.get_channel(CHANNEL_ID)
            if channel:
                embed = discord.Embed(
                    title="Bot Error",
                    description=message,
                    color=discord.Color.red()
                )
                await channel.send(embed=embed)
    except:
        pass

def clean_mob_name(filename):
    """Extract clean mob name from filename"""
    return filename.replace("petal-", "").replace("-super.png", "").replace("_", " ").title()

print("\n" + "="*60)
print("FLORR MOB BOT - STARTING UP")
print("="*60 + "\n")

bot.run(TOKEN)
