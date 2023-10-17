import os
import discord
import charutils
from discord import app_commands
from dotenv import load_dotenv
from discord.ext import tasks
from discord.ext import commands

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = os.getenv('GUILD_ID') 
CHANNEL_ID = os.getenv('CHANNEL_ID')

#lets turn guild and channel into objects we can use
GUILD = discord.Object(id=int(GUILD_ID))
CHANNEL = discord.Object(id=int(CHANNEL_ID))

class RpgEngine(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.counter = 0
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self) -> None:
        self.tree.copy_global_to(guild=GUILD)
        self.spam_messages.start()

    async def on_ready(self):
        await self.tree.sync(guild=GUILD)
        print("commands synced")

    @tasks.loop(seconds=5)
    async def spam_messages(self):
        channel = self.get_channel(CHANNEL.id)
        #print(CHANNEL_ID)
        #print(channel)
        #await channel.send(self.counter)
        #self.counter += 1

    @spam_messages.before_loop
    async def before_spamming(self):
        await self.wait_until_ready()        

intents = discord.Intents.default()
intents.members = True
client = RpgEngine(intents=intents)

@client.tree.command(name="newchar",description="Create a character")
async def newchar(interaction: discord.Interaction, name: str):
    await interaction.response.send_message(charutils.create_character(name))

@client.tree.command(name="getchar",description="Get character JSON") #testing command
async def getchar(interaction: discord.Interaction, name: str):
    await interaction.response.send_message(charutils.get_character(name))

@client.tree.command(name="updategear",description="Get character JSON") #testing command
async def updategear(interaction: discord.Interaction, name: str, value: int):
    await interaction.response.send_message(charutils.update_gear(name, value))

client.run(TOKEN)