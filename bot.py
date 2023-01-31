import os
import random

import discord
from discord import app_commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = os.getenv('GUILD_ID')

intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

@tree.command(name = "sup", description = "this should be a slash sup command", guild=discord.Object(id=GUILD_ID))
async def sup_command(interaction):
    await interaction.response.send_message("sup bro")

@client.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=GUILD_ID))
    print("command synced")

client.run(TOKEN)