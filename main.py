import asyncio
import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
import json
from commands import Commands  # Import the Commands cog here
from files.junk import print_status_messages, ignore_message
from files.utils import get_prefix
from keep_alive import keep_alive

load_dotenv() # Load Discord Bot key

TOKEN = os.getenv('DISCORD_TOKEN')  # BOT token

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix=get_prefix, intents=intents, help_command=None)

# Load the prefixes when the bot is initialized
try:
    with open('prefixes.json') as f:
        bot.prefixes = json.load(f)
except FileNotFoundError:
    with open('prefixes.json', 'w') as f:
        print("Could not load prefixes file. A new one will be created.")
        json.dump({}, f)  # Create a new file with an empty dictionary

# Load the configuration file
try:
    with open('config.json') as f:
        config = json.load(f)
except FileNotFoundError:
    print("Could not load configuration file.")
    config = {}
bot.config = config  # Add this line

@bot.event
async def on_ready():
    await bot.add_cog(Commands(bot, config))  # Add the cog to the bot

    status_messages = ["Status: Ready", "Commands: Loaded"]
    print_status_messages(status_messages)  # Console stuff


@bot.event
async def close():
    with open('prefixes.json', 'w') as f:
        json.dump(bot.prefixes, f)
    await asyncio.sleep(1)  # Add a delay
    await super(type(bot), bot).close()
    print(ignore_message)

keep_alive()
bot.run(TOKEN)  # add this line at the end
