from asyncio import sleep
import os
import datetime
import discord
import initialsetup
import charutils
import dungeonmaster
import typing
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
        adventure_embed = create_adventure_embed()
        await channel.send(content=adventure_embed.title + adventure_embed.description)

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
        day_embed = create_day_report_embed()
        await channel.send(content=day_embed.title + day_embed.description)

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
        pvp_embed = create_pvp_embed()
        await channel.send(content=pvp_embed.title + pvp_embed.description)

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
            await interaction.response.send_message(content="**A hero did something!**\n" + quest_journal, ephemeral=True)
        else:
            await interaction.response.send_message("You are not an admin", ephemeral=True)

    @client.tree.command(name="adventure",description="Run an adventure") #testing command
    async def adventure(interaction: discord.Interaction):
        if interaction.user.id == ADMIN_ID:
            await interaction.response.send_message("Running a quest")
            quest_embed = create_adventure_embed()
            await interaction.channel.send(content=quest_embed.title + quest_embed.description)
        else:
            await interaction.response.send_message("You are not an admin", ephemeral=True)

    @client.tree.command(name="pvp",description="Run a PvP encounter") #testing command
    async def pvp(interaction: discord.Interaction):
        if interaction.user.id == ADMIN_ID:
            pvp_embed = create_pvp_embed()
            await interaction.response.send_message(content=pvp_embed.title + pvp_embed.description)
        else:
            await interaction.response.send_message("You are not an admin", ephemeral=True)

    @client.tree.command(name="rest",description="Take a long rest") #testing command
    async def rest(interaction: discord.Interaction):
        if interaction.user.id == ADMIN_ID:
            await interaction.response.send_message("Leveling up characters & gear")
            day_embed = create_day_report_embed()
            await interaction.channel.send(content=day_embed.title + day_embed.description)
        else:
            await interaction.response.send_message("You are not an admin", ephemeral=True)

#TREE COMMANDS

@client.tree.command(name="top",description="Get top X characters. Returns top 10 if no argument is given.") #make it prettier
async def leaderboard(interaction: discord.Interaction, top_x: typing.Optional[int]):
    if top_x and top_x > 0 and top_x <= 10:
        leaderboard_embed = await create_leaderboard_embed(top_x)
        await interaction.response.send_message(content=leaderboard_embed.title + leaderboard_embed.description)
    elif not top_x:
        leaderboard_embed = await create_leaderboard_embed(10)
        await interaction.response.send_message(content=leaderboard_embed.title + leaderboard_embed.description)
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

@client.tree.command(name="find", description="Find a character. Returns your own character if no name is given.") #TODO: this doesn't need to be an embed anymore
async def find(interaction: discord.Interaction, name: typing.Optional[str]):
    results_embed = discord.Embed(title="Search results")
    if name is None:
        results_report = charutils.character_search(name, [{"id":interaction.user.id, "name":interaction.user.display_name}])
        results_embed.title = "Your character"
        results_embed.description = results_report
        await interaction.response.send_message(content=results_embed.title + results_embed.description)
    elif name:
        members_list = client.get_all_members()
        users_list = []
        for member in members_list:
            if len(member.display_name) > 10:
                member_name = member.display_name[:6]+"..."
            else:
                member_name = member.display_name
            users_list.append({"id":member.id, "name":member_name})
        results_report = charutils.character_search(name, users_list)
        results_embed.title = "Stats for character " + name + ":"
        results_embed.description = results_report
        await interaction.response.send_message(content=results_embed.title + results_embed.description)

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
def create_day_report_embed():
    day_report = dungeonmaster.run_long_rest()
    day_embed = discord.Embed(title="**The adventurers took a long rest.**\n", type="rich", description="During the night, they thought about experiences they had had during the day and attuned new magic items. Character statistics in the morning:" + day_report)
    if day_report == "":
        day_embed.description="After sitting down to rest they found out that they weren't all that tired, and just kept going without leveling anything up."
        return day_embed
    return day_embed

def create_adventure_embed():
    quest = dungeonmaster.run_adventure()
    if len(quest.party) == 0:
        quest_embed = discord.Embed(title="I tried to run an adventure, but nobody showed up.")
        return quest_embed
    quest_embed = discord.Embed(title="**An epic adventure was had!**\n", type="rich", description=quest.quest_journal)
    return quest_embed

def create_pvp_embed():
    pvp_encounter = dungeonmaster.run_pvp_encounter()
    pvp_embed = discord.Embed(title="**Heroes fighting heroes!**\n", type="rich", description=pvp_encounter[0] + pvp_encounter[1])
    return pvp_embed

async def create_leaderboard_embed(top_x):
    members_list = client.get_all_members()
    users_list = []
    for member in members_list:
        if len(member.display_name) > 10:
            member_name = member.display_name[:6]+"..."
        else:
            member_name = member.display_name
        users_list.append({"id":member.id, "name":member_name})
    leaderboard = charutils.get_leaderboard(top_x, users_list)
    if leaderboard == "":
        leaderboard_embed = discord.Embed(title="There are no characters yet.")
        return leaderboard_embed
    leaderboard_embed = discord.Embed(title="Top " + str(top_x) + " characters in this world:", description=leaderboard)
    return leaderboard_embed

print("starting bot")
client.run(TOKEN)
