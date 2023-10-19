import os
import discord
import charutils
import initialsetup
from discord import app_commands
from dotenv import load_dotenv
from discord.ext import tasks
from discord.ext import commands

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = os.getenv("GUILD_ID") 
CHANNEL_ID = os.getenv("CHANNEL_ID")

if not os.path.exists(".conf"):
    initialsetup.do()
    
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

@client.tree.command(name="levelup",description="Level up a character by name") #testing command
async def levelup(interaction: discord.Interaction, name: str):
    await interaction.response.send_message(charutils.level_up(name))

CHARACTER_CLASSES = [
    discord.SelectOption(label="Rogue", value="1", description="Rogues need to be lucky to get ahead"),
    discord.SelectOption(label="Fighter", value="2", description="Fighters are solid in any situation")
]

class ClassView(discord.ui.View):
    def __init__(self, name):
        super().__init__(timeout=100)
        self.name = name

    @discord.ui.select(placeholder="Select a class", options=CHARACTER_CLASSES, max_values=1)
    async def reply_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        await interaction.response.defer()
        #print(str(interaction.user.id) + " chose a class")
        response_message = charutils.register_character(self.name, int(select.values[0]), interaction.user.id)
        await interaction.followup.edit_message(interaction.message.id, content=(response_message), view=None)

@client.tree.command(name="test", description="Create a new character")
async def test(interaction: discord.Interaction, name: str):
    await interaction.response.send_message("You need to pick a class also!", view=ClassView(name))

print("starting bot")
client.run(TOKEN)