import asyncio
from playwright.async_api import async_playwright
from discord.ext import commands
import discord
import os
import aiohttp
from datetime import datetime, timedelta

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = 1473465801536307200
CHANNEL_ID = 1473465801536307203

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
            # Look for petal-*-super.png requests
            if "petal-" in url and "-super.png" in url:
                try:
                    mob_filename = url.split("/")[-1].split("?")[0]  # Get filename without query params
                    
                    if mob_filename not in detected_mobs:
                        detected_mobs.add(mob_filename)
                        # Download the image and send notification
                        await send_spawn_notification(url, mob_filename)
                except Exception as e:
                    print(f"Error processing mob: {e}")
        
        page.on("response", on_response)
        
        try:
            await page.goto("https://mobs.ashish.top/", wait_until="networkidle")
            print("📡 Listening for super mob spawns...")
            # Keep the page open and listening
            while True:
                await asyncio.sleep(1)
        except Exception as e:
            print(f"❌ Monitor error: {e}")

async def send_spawn_notification(image_url, mob_filename):
    """Send Discord notification with image, ping everyone, and timer"""
    guild = bot.get_guild(GUILD_ID)
    if not guild:
        return
    
    channel = guild.get_channel(CHANNEL_ID)
    if not channel:
        return
    
    try:
        # Download the image
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as resp:
                image_data = await resp.read()
        
        # Parse mob name from filename (e.g., "petal-roach-super.png" -> "Roach")
        mob_name = mob_filename.replace("petal-", "").replace("-super.png", "").replace("_", " ").title()
        
        # Create embed with timer
        spawn_time = datetime.now()
        despawn_time = spawn_time + timedelta(seconds=30)  # Super mobs despawn in ~30 seconds
        
        embed = discord.Embed(
            title="🚨 SUPER MOB SPAWN 🚨",
            description=f"**{mob_name}**",
            color=discord.Color.red(),
            timestamp=spawn_time
        )
        embed.add_field(
            name="⏱️ Despawns in",
            value="~30 seconds",
            inline=False
        )
        
        # Save image temporarily
        image_path = f"/tmp/{mob_filename}"
        with open(image_path, "wb") as f:
            f.write(image_data)
        
        # Send message with ping and image
        with open(image_path, "rb") as f:
            await channel.send(
                content="@everyone",
                embed=embed,
                file=discord.File(f, filename=mob_filename)
            )
        
        print(f"✅ Notified: {mob_name}")
        
    except Exception as e:
        print(f"❌ Error sending notification: {e}")
        # Send backup message without image
        try:
            await channel.send(f"@everyone\n🚨 **SUPER MOB**: {mob_filename}")
        except:
            pass

bot.run(TOKEN)
```

5. Click **"Commit changes"** button at bottom right

---

**Step 2: Update requirements.txt**

1. Click on `requirements.txt` file
2. Click pencil (edit)
3. Replace with:
```
discord.py==2.3.2
playwright==1.40.0
aiohttp==3.9.1
