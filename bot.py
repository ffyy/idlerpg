import os
import discord
import initialsetup
import charutils
import dungeonmaster
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
        self.run_adventures.start()

    async def on_ready(self):
        await self.tree.sync(guild=GUILD)
        print("commands synced")
        channel = self.get_channel(CHANNEL.id)
        #await channel.send("I have awoken")

    @tasks.loop(seconds=5)
    async def run_adventures(self):
        channel = self.get_channel(CHANNEL.id)
        await channel.send(dungeonmaster.run_adventure())
        #await channel.send(self.counter)
        #self.counter += 1

    @run_adventures.before_loop
    async def before_adventuring(self):
        await self.wait_until_ready()        
        

intents = discord.Intents.default()
intents.members = True
client = RpgEngine(intents=intents)

@client.tree.command(name="levelup",description="Level up your character") #testing command
async def levelup(interaction: discord.Interaction):
    await interaction.response.send_message(charutils.level_me_up(interaction.user.id))

class DeleteView(discord.ui.View):
    def __init__(self, name):
        super().__init__(timeout=100)
        self.name = name

    @discord.ui.button(label="Delete the character", style=discord.ButtonStyle.primary, emoji="☠")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        response = charutils.delete_character(interaction.user.id)
        await interaction.response.edit_message(content=("You can always start again by using /register"), view=None)
        await interaction.channel.send(response)

    @discord.ui.button(label="Don't delete the character", style=discord.ButtonStyle.primary, emoji="😎")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content=("Keep on keeping on!"), view=None)

@client.tree.command(name="delete", description="Delete your character")
async def delete(interaction: discord.Interaction, name: str):
    current_character = charutils.get_character_by_player_id(interaction.user.id)
    if (current_character is not None) and (current_character.name) == name:
        await interaction.response.send_message("Confirm deleting the character.", view=DeleteView(name), ephemeral=True)
    elif current_character is None:
        await interaction.response.send_message("You don't have a character.\nUse /register to register a new character.", ephemeral=True)
    else:
        await interaction.response.send_message("This is not your character, you can't delete it.", ephemeral=True)

class RegisterView(discord.ui.View):
    CHARACTER_CLASSES = [
        discord.SelectOption(label="Rogue", value="1", description="Rogues need to be lucky to get ahead"),
        discord.SelectOption(label="Fighter", value="2", description="Fighters are solid in any situation")
]
    def __init__(self, name):
        super().__init__(timeout=100)
        self.name = name

    @discord.ui.select(placeholder="Select a class", options=CHARACTER_CLASSES, max_values=1)
    async def reply_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        await interaction.response.defer()
        #print(str(interaction.user.id) + " chose a class")
        response = charutils.register_character(self.name, int(select.values[0]), interaction.user.id)
        await interaction.followup.edit_message(interaction.message.id, content=("Enjoy idling!"), view=None)
        await interaction.channel.send(response)

@client.tree.command(name="register", description="Create a new character")
async def register(interaction: discord.Interaction, name: str):
    old_character = charutils.get_character_by_player_id(interaction.user.id)
    if old_character is not None:
        response = "You already have a level " + str(old_character.level) + " " + old_character.character_class.name + " called " + old_character.name + ".\nUse /delete [name] to delete your old character first."
        await interaction.response.send_message(response, ephemeral=True)
    else:
        if (charutils.is_name_valid(name)):
            await interaction.response.send_message("You need to pick a class also!", view=RegisterView(name), ephemeral=True)
        else:
            await interaction.response.send_message("The name [" + name + "] is not valid", ephemeral=True)

@client.tree.command(name="find", description="Find my character")
async def find(interaction: discord.Interaction):
    character = charutils.get_character_by_player_id(interaction.user.id)
    if character is not None:
        response = "You have a level " + str(character.level) + " " + character.character_class.name + " called " + character.name + "."
        await interaction.response.send_message(response, ephemeral=True)
    else:
        await interaction.response.send_message("You don't have a character yet.\nUse /register to start.", ephemeral=True)

print("starting bot")
client.run(TOKEN)
