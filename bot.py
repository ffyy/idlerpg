import os
import discord
import charutils
from discord import app_commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = os.getenv('GUILD_ID')

intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

@tree.command(name = "newchar", description = "Create a character", guild=discord.Object(id=GUILD_ID))
async def newchar_command(interaction: discord.Interaction, name: str):
    charutils.saveToDisk(name)
    await interaction.response.send_message(f'I created a file in /chars/ called {name}.txt')

@client.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=GUILD_ID))
    print("commands synced")

client.run(TOKEN)