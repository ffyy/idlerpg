from asyncio import sleep
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

        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self) -> None:
        self.tree.copy_global_to(guild=GUILD)

    async def on_ready(self):
        await self.tree.sync(guild=GUILD)
        print("commands synced")
        self.run_adventures.start()
        self.run_long_rests.start()
        print("loops started")

    @tasks.loop(minutes=(TIMESCALE))
    async def run_adventures(self):
        print("running adventure " + str(self.run_adventures.current_loop))
        if self.run_adventures.current_loop == 0:
            self.run_adventures.change_interval(minutes=TIMESCALE)
        channel = self.get_channel(CHANNEL.id)
        await channel.send(embed=create_adventure_embed())

    @run_adventures.before_loop
    async def before_adventuring(self):
        if self.run_adventures.current_loop == 0:
            sleep_time = TIMESCALE*60//2 #half of timescale in seconds
            print(str(self.run_adventures) + " waiting until start: " + str(sleep_time))
            await sleep(sleep_time)
            await self.wait_until_ready()
        else:
            await self.wait_until_ready()

    @tasks.loop(minutes=TIMESCALE)
    async def run_long_rests(self):
        print("running rest " + str(self.run_long_rests.current_loop))
        channel = self.get_channel(CHANNEL.id)
        await channel.send(embed=create_day_report_embed())

    @run_long_rests.before_loop
    async def before_resting(self):
        if self.run_long_rests.current_loop == 0:
            sleep_time = TIMESCALE*60 #timescale in seconds
            print(str(self.run_long_rests) + " waiting until start: " + str(sleep_time))
            await sleep(sleep_time)
            await self.wait_until_ready()
        else:
            await self.wait_until_ready()
       

intents = discord.Intents.default()
intents.members = True
client = RpgEngine(intents=intents)


# DEBUG COMMANDS
if DEBUG_MODE == "1":
    @client.tree.command(name="levelup",description="Level up your character") #testing command
    async def levelup(interaction: discord.Interaction):
        await interaction.response.send_message(charutils.level_me_up(interaction.user.id))

    @client.tree.command(name="startloops",description="Start loops") #testing command
    async def startloops(interaction: discord.Interaction):
        client.run_adventures.start()
        client.run_long_rests.start()
        await interaction.response.send_message("Started loops")

    @client.tree.command(name="stoploops",description="Stop loops") #testing command
    async def stoploops(interaction: discord.Interaction):
        client.run_adventures.stop()
        client.run_long_rests.stop()
        await interaction.response.send_message("Stopped loops")

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

    @client.tree.command(name="rest",description="Take a long rest") #testing command
    async def rest(interaction: discord.Interaction):
        await interaction.response.send_message("Leveling up characters & gear")
        day_report = dungeonmaster.run_long_rest()
        day_embed = discord.Embed(title="The adventurers took a long rest.", type="rich", description="During they rest, they leveled up and attuned new magic items. As a result, the following stats changed:")
        characters_string = ""
        levels_string = ""
        gearscore_string = ""
        for character in day_report:
            characters_string = ''.join([characters_string, character.character_name])
            characters_string = ''.join([characters_string, "\n"])
            levels_string = ''.join([levels_string, str(character.level_result)])
            levels_string = ''.join([levels_string, "\n"])
            gearscore_string = ''.join([gearscore_string, str(character.gearscore_result)])
            gearscore_string = ''.join([gearscore_string, "\n"])
        day_embed.add_field(name="Characters", value=characters_string, inline=True)
        day_embed.add_field(name="Level", value=levels_string, inline=True)        
        day_embed.add_field(name="Gearscore", value=gearscore_string, inline=True)
        await interaction.channel.send(embed=day_embed)

#TREE COMMANDS

@client.tree.command(name="leaderboard",description="Get top X characters") #make it prettier
async def leaderboard(interaction: discord.Interaction, top_x: int):
    if top_x > 0 and top_x <= 10:
        await interaction.response.send_message("Showing leaderboard", ephemeral=True)
        leaderboard_embed = await create_leaderboard_embed(top_x)
        await interaction.channel.send(embed=leaderboard_embed)
    else:
        await interaction.response.send_message("You need to enter a number between 0 and 10", ephemeral=True)

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
        discord.SelectOption(label="Rogue", value="1", description="Trust in your luck (1d100)"),
        discord.SelectOption(label="Fighter", value="2", description="Solid in any situation (5d20)"),
        discord.SelectOption(label="Hobbit", value="3", description="Generally bad, but has a magic ring (4d10+20 gs)")
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

#LOOP FUNCTIONS
def create_day_report_embed():
    day_report = dungeonmaster.run_long_rest()
    day_embed = discord.Embed(title="The adventurers took a long rest.", type="rich", description="During they rest, they leveled up and attuned new magic items. As a result, the following stats changed:")
    if len(day_report) == 0:
        day_embed.add_field(name="Absolutely nothing", value="")
        return day_embed
    characters_string = ""
    levels_string = ""
    gearscore_string = ""
    for character in day_report:
        characters_string = ''.join([characters_string, character.character_name])
        characters_string = ''.join([characters_string, "\n"])
        levels_string = ''.join([levels_string, str(character.level_result)])
        levels_string = ''.join([levels_string, "\n"])
        gearscore_string = ''.join([gearscore_string, str(character.gearscore_result)])
        gearscore_string = ''.join([gearscore_string, "\n"])
    day_embed.add_field(name="Characters", value=characters_string, inline=True)
    day_embed.add_field(name="Level", value=levels_string, inline=True)        
    day_embed.add_field(name="Gearscore", value=gearscore_string, inline=True)
    return day_embed

def create_adventure_embed():
    quest = dungeonmaster.run_adventure()
    if len(quest.party) == 0:
        quest_embed = discord.Embed(title="I tried to run an adventure, but nobody showed up.")
        return quest_embed
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
    return quest_embed

async def create_leaderboard_embed(top_x):
    leaderboard = charutils.get_leaderboard(top_x)
    if len(leaderboard) == 0:
        leaderboard_embed = discord.Embed(title="There are no characters yet.")
        return leaderboard_embed
    leaderboard_embed = discord.Embed(title="Top " + str(top_x) + " characters in this world:")
    character_names_string = ""
    character_stats_string = ""
    player_names_string = ""
    discord_names = []
    for player in leaderboard:
        player = await client.fetch_user(player.player_id)
        player_name = player.display_name
        discord_names.append(player_name)
    for i,character in enumerate(leaderboard):
        character_names_string = ''.join([character_names_string, character.character_name])
        character_names_string = ''.join([character_names_string, "\n"])
        character_stats_string = ''.join([character_stats_string, str(character.level)])
        character_stats_string = ''.join([character_stats_string, "/"])
        character_stats_string = ''.join([character_stats_string, str(character.gearscore)])
        character_stats_string = ''.join([character_stats_string, "\n"])
        player_names_string = ''.join([player_names_string, discord_names[i]])
        player_names_string = ''.join([player_names_string, "\n"])
    leaderboard_embed.add_field(name="Character", value=character_names_string, inline=True)
    leaderboard_embed.add_field(name="Level/Gearscore", value=character_stats_string, inline=True)
    leaderboard_embed.add_field(name="Player", value=player_names_string, inline=True)

    return leaderboard_embed
       
print("starting bot")
client.run(TOKEN)
