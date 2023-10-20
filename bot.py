import os
import discord
import initialsetup
import charutils
import dungeonmaster
from discord import app_commands
from dotenv import load_dotenv
from discord.ext import tasks

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = os.getenv("GUILD_ID") 
CHANNEL_ID = os.getenv("CHANNEL_ID")
TIMESCALE = int(os.getenv("TIMESCALE"))
DEBUG_MODE = os.getenv("DEBUG_MODE")

if not os.path.exists(".conf"):
    initialsetup.do()
    
GUILD = discord.Object(id=int(GUILD_ID))
CHANNEL = discord.Object(id=int(CHANNEL_ID))

class RpgEngine(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.counter = 0
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self) -> None:
        self.tree.copy_global_to(guild=GUILD)
        #self.run_adventures.start()

    async def on_ready(self):
        await self.tree.sync(guild=GUILD)
        print("commands synced")
        channel = self.get_channel(CHANNEL.id)
        #await channel.send("I have awoken")

    @tasks.loop(seconds=600)
    async def run_adventures(self):
        channel = self.get_channel(CHANNEL.id)
        await channel.send(dungeonmaster.run_adventure())

    @run_adventures.before_loop
    async def before_adventuring(self):
        await self.wait_until_ready()        
        

intents = discord.Intents.default()
intents.members = True
client = RpgEngine(intents=intents)

if DEBUG_MODE == "1":
    @client.tree.command(name="levelup",description="Level up your character") #testing command
    async def levelup(interaction: discord.Interaction):
        await interaction.response.send_message(charutils.level_me_up(interaction.user.id))

    @client.tree.command(name="adventure",description="Run an adventure") #testing command
    async def adventure(interaction: discord.Interaction):
        await interaction.response.send_message("Running a quest")
        quest = dungeonmaster.run_adventure()
        quest_embed = discord.Embed(title="An epic adventure was had!", type="rich", description=quest.quest_journal)
        party_members_string = ""
        adventurer_rolls_string = ""
        for i, adventurer in enumerate(quest.party):
            party_members_string = ''.join([party_members_string, adventurer.name])
            party_members_string = ''.join([party_members_string, "\n"])
            adventurer_rolls_string = ''.join([adventurer_rolls_string, str(quest.party_rolls[i])])
            adventurer_rolls_string = ''.join([adventurer_rolls_string, "\n"])
        quest_embed.add_field(name="Heroes", value=party_members_string, inline=True)
        quest_embed.add_field(name="Rolls", value=adventurer_rolls_string, inline=True)        
        await interaction.channel.send(embed=quest_embed)

    @client.tree.command(name="testembed")
    async def testembed(interaction: discord.Interaction, name: str):
        embed_with_name = discord.Embed(title=name, type="rich", description="this is the description")
        value_field1="tuut\ntuut"
        embed_with_name.add_field(name="field 1", value=(value_field1), inline=True)
        embed_with_name.add_field(name="field 2", value=(name*2, "\u200Bsecond element", "\u200Bthird element"), inline=True)
        embed_with_name.add_field(name="inline field", value=(name, name, name, name*3), inline=True)
        await interaction.response.send_message("Sending embed", ephemeral=True)
        await interaction.channel.send(embed=embed_with_name)

@client.tree.command(name="top10",description="Get top10 characters") #make it prettier
async def top10(interaction: discord.Interaction):
    await interaction.response.send_message(charutils.get_top10())

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
        await interaction.response.send_message("This is not your character, you can't delete it. Your character is called " + current_character.name, ephemeral=True)

class RegisterView(discord.ui.View):
    CHARACTER_CLASSES = [
        discord.SelectOption(label="Rogue", value="1", description="Rogues need to be lucky to get ahead (1d100)"),
        discord.SelectOption(label="Fighter", value="2", description="Fighters are solid in any situation (5d20)"),
        discord.SelectOption(label="Hobbit", value="3", description="Hobbits are overall bad, but start with a magic ring (4d10 + 25 gearscore)")
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
            await interaction.response.send_message("The name [" + name + "] is not valid.\nNames can be up to 20 characters, must be unique and must include only letters.", ephemeral=True)

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
