import os
import json
import asyncio
import discord
from discord.ext import commands

# ── Load config.json ───────────────────────────────────────────────
with open('config.json', 'r', encoding='utf-8') as f:
    cfg = json.load(f)

TOKEN  = cfg['token']
PREFIX = cfg['prefix']

# ── Bot & Intents ─────────────────────────────────────────────────
intents = discord.Intents.default()
intents.members         = True
intents.guilds          = True
intents.message_content = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents)

# ── Dynamically load ALL cogs (and await!) ────────────────────────
async def load_all_cogs():
    for fn in os.listdir('cogs'):
        if not fn.endswith('.py') or fn.startswith('_'):
            continue
        module = f'cogs.{fn[:-3]}'
        try:
            await bot.load_extension(module)
            print(f'✅ Loaded cog: {fn}')
        except Exception as e:
            print(f'❌ Failed to load {fn}: {e}')

# ── Events & Startup ──────────────────────────────────────────────
@bot.event
async def on_ready():
    print(f'📡 Bot online as {bot.user} — cogs: {list(bot.cogs.keys())}')

async def main():
    await load_all_cogs()
    await bot.start(TOKEN)

if __name__ == '__main__':
    asyncio.run(main())