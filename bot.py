from asyncio import sleep
import os
import datetime
import discord
import initialsetup
import charutils
import dungeonmaster
import typing
import re
from discord import app_commands
from dotenv import load_dotenv
from discord.ext import tasks

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = os.getenv("GUILD_ID")
CHANNEL_ID = os.getenv("CHANNEL_ID")
TIMESCALE = int(os.getenv("TIMESCALE"))
DEBUG_MODE = os.getenv("DEBUG_MODE")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

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
        self.run_personal_quests.start()
        self.run_adventures.start()
        self.run_pvp_encounters.start()
        self.run_long_rests.start()
        print(str(datetime.datetime.now()) + " - loops started")

    @tasks.loop(minutes=(TIMESCALE))
    async def run_adventures(self):
        print(str(datetime.datetime.now()) + " - running adventure " + str(self.run_adventures.current_loop))
        if self.run_adventures.current_loop == 0:
            self.run_adventures.change_interval(minutes=TIMESCALE)
        channel = self.get_channel(CHANNEL.id)
        adventure_report = create_adventure_report()
        await channel.send(content=adventure_report)

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
        print(str(datetime.datetime.now()) + " - running rest " + str(self.run_long_rests.current_loop))
        channel = self.get_channel(CHANNEL.id)
        rest_report = create_rest_report()
        await channel.send(content=rest_report)

    @run_long_rests.before_loop
    async def before_resting(self):
        if self.run_long_rests.current_loop == 0:
            sleep_time = TIMESCALE*60 #timescale in seconds
            print(str(self.run_long_rests) + " waiting until start: " + str(sleep_time))
            await sleep(sleep_time)
            await self.wait_until_ready()
        else:
            await self.wait_until_ready()

    @tasks.loop(minutes=TIMESCALE)
    async def run_pvp_encounters(self):
        print(str(datetime.datetime.now()) + " - running pvp " + str(self.run_pvp_encounters.current_loop))
        channel = self.get_channel(CHANNEL.id)
        pvp_report = create_pvp_report()
        await channel.send(content=pvp_report)

    @run_pvp_encounters.before_loop
    async def before_pvp(self):
        if self.run_pvp_encounters.current_loop == 0:
            sleep_time = int((TIMESCALE*60)*2/3) #timescale in seconds
            print(str(self.run_pvp_encounters) + " waiting until start: " + str(sleep_time))
            await sleep(sleep_time)
            await self.wait_until_ready()
        else:
            await self.wait_until_ready()

    @tasks.loop(minutes=TIMESCALE)
    async def run_personal_quests(self):
        print(str(datetime.datetime.now()) + " - running personal quest " + str(self.run_personal_quests.current_loop))
        channel = self.get_channel(CHANNEL.id)
        personal_quest_content = dungeonmaster.run_personal_quest()
        await channel.send(content="**A hero did something!**\n" + personal_quest_content)

    @run_personal_quests.before_loop
    async def before_personal_quest(self):
        if self.run_personal_quests.current_loop == 0:
            sleep_time = int((TIMESCALE*60)/3) #timescale in seconds
            print(str(self.run_personal_quests) + " waiting until start: " + str(sleep_time))
            await sleep(sleep_time)
            await self.wait_until_ready()
        else:
            await self.wait_until_ready()


intents = discord.Intents.default()
intents.members = True
client = RpgEngine(intents=intents)


# DEBUG COMMANDS
if DEBUG_MODE == "1":
    @client.tree.command(name="personalquest",description="Run a personal quest") #testing command
    async def personalquest(interaction: discord.Interaction):
        if interaction.user.id == ADMIN_ID:
            quest_journal = dungeonmaster.run_personal_quest()
            await interaction.response.send_message(content="**A hero did something!**\n" + quest_journal)
        else:
            await interaction.response.send_message("You are not an admin", ephemeral=True)

    @client.tree.command(name="adventure",description="Run an adventure") #testing command
    async def adventure(interaction: discord.Interaction):
        if interaction.user.id == ADMIN_ID:
            adventure_report = create_adventure_report()
            await interaction.response.send_message(content=adventure_report)
        else:
            await interaction.response.send_message("You are not an admin", ephemeral=True)

    @client.tree.command(name="pvp",description="Run a PvP encounter") #testing command
    async def pvp(interaction: discord.Interaction):
        if interaction.user.id == ADMIN_ID:
            pvp_report = create_pvp_report()
            await interaction.response.send_message(content=pvp_report)
        else:
            await interaction.response.send_message("You are not an admin", ephemeral=True)

    @client.tree.command(name="rest",description="Take a long rest") #testing command
    async def rest(interaction: discord.Interaction):
        if interaction.user.id == ADMIN_ID:
            rest_report = create_rest_report()
            await interaction.response.send_message(content=rest_report)
        else:
            await interaction.response.send_message("You are not an admin", ephemeral=True)

#TREE COMMANDS

@client.tree.command(name="top",description="Get top X characters. Returns top 10 if no argument is given.") #make it prettier
async def leaderboard(interaction: discord.Interaction, top_x: typing.Optional[int], class_filter: typing.Optional[str]):
    if top_x and top_x > 0 and top_x <= 10:
        leaderboard_report = await create_leaderboard_report(top_x, class_filter)
        await interaction.response.send_message(content=leaderboard_report)
    elif not top_x:
        leaderboard_report = await create_leaderboard_report(10, class_filter)
        await interaction.response.send_message(content=leaderboard_report)

class DeleteView(discord.ui.View):
    def __init__(self, name):
        super().__init__(timeout=100)
        self.name = name

    @discord.ui.button(label="Delete the character", style=discord.ButtonStyle.primary, emoji="☠")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        response = charutils.delete_character_by_id(interaction.user.id)
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
    character_classes = []
    configured_classes = charutils.get_all_classes()
    for character_class in configured_classes:
        character_classes.append(discord.SelectOption(label=character_class.name, value=character_class.id_, description=character_class.description))

    def __init__(self, name):
        super().__init__(timeout=100)
        self.name = name

    @discord.ui.select(placeholder="Select a class", options=character_classes, max_values=1)
    async def reply_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        await interaction.response.defer()
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
            await interaction.response.send_message("The name [" + name + "] is not valid.\nNames can be up to 12 characters, must be unique and must include only letters.", ephemeral=True)

@client.tree.command(name="find", description="Find a character. Returns your own character if no name is given.")
async def find(interaction: discord.Interaction, name: typing.Optional[str]):
    title_text = "Search results"
    if name is None:
        member_name = re.sub("[`>*]", "", interaction.user.display_name)
        results_report = charutils.character_search(name, [{"id":interaction.user.id, "name":member_name}])
        title_text = "Your character:"
    elif name:
        members_list = client.get_all_members()
        users_list = []
        for member in members_list:
            member_name = member.display_name
            member_name = re.sub("[`>*]", "", member_name)
            users_list.append({"id":member.id, "name":member_name})
        results_report = charutils.character_search(name, users_list)
        title_text = "Search results for " + name + ":"

    await interaction.response.send_message(content=title_text + results_report)

@client.tree.command(name="changename", description="Rename your character")
async def changename(interaction: discord.Interaction, new_name: str):
    character = charutils.get_character_by_player_id(interaction.user.id)
    old_name = character.name
    if old_name == new_name:
        await interaction.response.send_message(content="That is already your name.", ephemeral=True)
    elif character is None:
        await interaction.response.send_message(content="You don't have a character.\nUse /register to register a new character.", ephemeral=True)
    elif not charutils.is_name_valid(new_name):
        await interaction.response.send_message(content="The name [" + new_name + "] is not valid.\nNames can be up to 12 characters, must be unique and must include only letters.", ephemeral=True)
    elif (character is not None) and charutils.is_name_valid(new_name):
        character.name = new_name
        charutils.update_db_character(charutils.character_to_db_character(character))
        await interaction.response.send_message(content="The character formerly known as " + old_name + " is now called " + new_name + ".")
    else:
        await interaction.response.send_message(content="Something went wrong", ephemeral=True)

#LOOP FUNCTIONS
def create_rest_report():
    rest_results = dungeonmaster.run_long_rest()
    title_text = "**The adventurers took a long rest.**\n"
    report_fluff = "During the night, they thought about experiences they had had during the day and attuned new magic items. Character statistics in the morning:"
    if rest_results == "":
        report_fluff = "After sitting down to rest they found out that they weren't all that tired, and just kept going without leveling anything up."

    rest_report = title_text
    rest_report = "".join([rest_report, report_fluff])
    rest_report = "".join([rest_report, rest_results])

    return rest_report

def create_adventure_report():
    quest_results = dungeonmaster.run_adventure()
    title_text = "**An epic adventure was had!**\n"

    adventure_report = title_text
    adventure_report = "".join([adventure_report, quest_results])

    return adventure_report

def create_pvp_report():
    pvp_results = dungeonmaster.run_pvp_encounter()
    title_text = "**Heroes fighting heroes!**\n"

    pvp_report = title_text
    pvp_report = "".join([pvp_report, pvp_results])
    return pvp_report

async def create_leaderboard_report(top_x, class_filter):
    character_classes = charutils.get_all_classes()
    class_id = None
    title_text = "Top " + str(top_x) + " characters in this world:"

    if class_filter:
        character_class = next((character_class for character_class in character_classes if character_class.name.lower() == class_filter.lower()), None)
        if character_class:
            class_id = character_class.id_
            title_text = "Top " + str(top_x) + " characters of class " + character_class.name + " in this world:"

    members_list = client.get_all_members()
    users_list = []
    for member in members_list:
        member_name = re.sub("[`>*]", "", member.display_name)
        users_list.append({"id":member.id, "name":member_name})
    leaderboard = charutils.get_leaderboard(top_x, users_list, class_id)

    if leaderboard == "":
        title_text = "There are no characters yet."

    leaderboard_report = title_text
    leaderboard_report = "".join([leaderboard_report, leaderboard])
    return leaderboard_report

print("starting bot")
client.run(TOKEN)
