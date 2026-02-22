import asyncio
from playwright.async_api import async_playwright
from discord.ext import commands
import discord
import os
import aiohttp

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = 1473465801536307200
CHANNEL_ID = 1473477387642732655

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot online: {bot.user}")
    bot.loop.create_task(monitor_mobs())

async def monitor_mobs():
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            detected = set()
            
            print("Opening mobs.ashish.top...")
            
            async def on_response(response):
                url = response.url
                if "petal-" in url and "-super.png" in url:
                    mob_file = url.split("/")[-1].split("?")[0]
                    if mob_file not in detected:
                        detected.add(mob_file)
                        print(f"SUPER MOB FOUND: {mob_file}")
                        asyncio.create_task(send_msg(url, mob_file))
            
            page.on("response", on_response)
            
            try:
                await asyncio.wait_for(page.goto("https://mobs.ashish.top/", wait_until="networkidle"), timeout=15)
            except asyncio.TimeoutError:
                print("Page load timeout, continuing anyway...")
            
            print("LISTENING FOR SUPER MOBS...")
            while True:
                await asyncio.sleep(1)
    except Exception as e:
        print(f"Monitor crashed: {e}")

async def send_msg(url, mob_file):
    try:
        guild = bot.get_guild(GUILD_ID)
        channel = guild.get_channel(CHANNEL_ID)
        
        async with aiohttp.ClientSession() as s:
            async with s.get(url) as r:
                data = await r.read()
        
        name = mob_file.replace("petal-", "").replace("-super.png", "").title()
        embed = discord.Embed(title="SUPER MOB SPAWN", description=name, color=discord.Color.red())
        
        with open(f"/tmp/{mob_file}", "wb") as f:
            f.write(data)
        
        with open(f"/tmp/{mob_file}", "rb") as f:
            await channel.send(f"@everyone", embed=embed, file=discord.File(f, mob_file))
        print(f"Sent to Discord: {name}")
    except Exception as e:
        print(f"Send error: {e}")

bot.run(TOKEN)
