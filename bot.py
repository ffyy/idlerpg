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
        channel = self.get_channel(CHANNEL.id)
        adventure_report = create_adventure_report()
        await channel.send(content=adventure_report[0])
        if len(adventure_report[1]) > 0:
            death_notice = ""
            users_generator = client.get_all_members()
            users_list = [] #creating a new list because client.get_all_members() can only be iterated through once, but we need to do it several times
            for user in users_generator:
                users_list.append(user)
            for discord_id in adventure_report[1]:
                for member in users_list:
                    if int(member.id) == int(discord_id):
                        user = await client.fetch_user(discord_id)
                        death_notice = " ".join([death_notice, user.mention])
            death_notice = " ".join([death_notice, "your character died and was reincarnated."])
            await channel.send(content=death_notice)

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
        await channel.send(content=pvp_report[0])
        if len(pvp_report[1]) > 0:
            death_notice = ""
            users_list = client.get_all_members()
            for discord_id in pvp_report[1]:
                for member in users_list:
                    if int(member.id) == int(discord_id):
                        user = await client.fetch_user(discord_id)
                        death_notice = " ".join([death_notice, user.mention])
            death_notice = " ".join([death_notice, "your character died and was reincarnated."])
            await channel.send(content=death_notice)

    @run_pvp_encounters.before_loop
    async def before_pvp(self):
        if self.run_pvp_encounters.current_loop == 0:
            sleep_time = int((TIMESCALE*60)*3/4) #timescale in seconds
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
            sleep_time = int((TIMESCALE*60)/4) #timescale in seconds
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
            await interaction.response.send_message(content=adventure_report[0])
            if len(adventure_report[1]) > 0:
                channel = interaction.channel
                death_notice = ""
                users_generator = client.get_all_members()
                users_list = [] #creating a new list because client.get_all_members() can only be iterated through once, but we need to do it several times
                for user in users_generator:
                    users_list.append(user)
                for discord_id in adventure_report[1]:
                    for member in users_list:
                        if int(member.id) == int(discord_id):
                            print("found match")
                            user = await client.fetch_user(discord_id)
                            death_notice = " ".join([death_notice, user.mention])
                        else:
                            print("no match - " + str(member.id) + " / " + str(discord_id))
                death_notice = " ".join([death_notice, "your character died and was reincarnated."])
                await channel.send(content=death_notice)
        else:
            await interaction.response.send_message("You are not an admin", ephemeral=True)

    @client.tree.command(name="pvp",description="Run a PvP encounter") #testing command
    async def pvp(interaction: discord.Interaction):
        if interaction.user.id == ADMIN_ID:
            pvp_report = create_pvp_report()
            await interaction.response.send_message(content=pvp_report[0])
            if len(pvp_report[1]) > 0: #this is broken
                for discord_id in pvp_report[1]:
                    channel = interaction.channel
                    user = await client.fetch_user(discord_id)
                    if user: await channel.send(f"{user.mention} rip your character bro")
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

@client.tree.command(name="top",description="Get top X characters. Returns top 10 if no argument is given.")
async def leaderboard(interaction: discord.Interaction, top_x: typing.Optional[int], class_filter: typing.Optional[str]):
    if top_x and top_x > 0 and top_x <= 10:
        leaderboard_report = await create_leaderboard_report(top_x, class_filter)
        await interaction.response.send_message(content=leaderboard_report)
    elif not top_x:
        leaderboard_report = await create_leaderboard_report(10, class_filter)
        await interaction.response.send_message(content=leaderboard_report)

@client.tree.command(name="graveyard",description="Get top 10 dead characters matching filters.")
async def graveyard(interaction: discord.Interaction, name: typing.Optional[str], class_filter: typing.Optional[str]):
    graveyard_report = await create_graveyard_report(name, class_filter)
    if graveyard_report:
        await interaction.response.send_message(content=graveyard_report)
    else:
        await interaction.response.send_message(content="No dead characters matching the filters were found", ephemeral=True)


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
            await interaction.response.send_message("The name [" + name + "] is not valid.\nNames can be up to 12 characters, must be unique, must include only letters and no uppercase special characters.", ephemeral=True)

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
        await interaction.response.send_message(content="The name [" + new_name + "] is not valid.\nNames can be up to 12 characters, must include only letters and no uppercase special characters.", ephemeral=True)
    elif (character is not None) and charutils.is_name_valid(new_name):
        character.name = new_name
        charutils.update_db_character(charutils.character_to_db_character(character))
        await interaction.response.send_message(content="The character formerly known as " + old_name + " is now called " + new_name + ".")
    else:
        await interaction.response.send_message(content="Something went wrong", ephemeral=True)

class RulesView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=100)

    rules_sections = [
        discord.SelectOption(label="General", value="0", description="General game rules"),
        discord.SelectOption(label="Experience", value="1", description="How do characters gain XP?"),
        discord.SelectOption(label="Questing", value="2", description="How are are quests run?"),
        discord.SelectOption(label="Gear", value="3", description="What does gear do?"),
        discord.SelectOption(label="PvP", value="4", description="How do characters fight each other?")
    ]

    @discord.ui.select(placeholder="Rules section", options=rules_sections, max_values=1)
    async def reply_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        #response = next((line for line in RULES_TEXTS if line[0] == select.values[0]), "  Oops")[2:]
        match select.values[0]:
            case "0":
                response = """
In this game, you register a character and watch it take part in heroic adventures without any further input from you. The only control you have over your character is registering, deleting, and changing its name.\n
Each real-life hour, a day passes in the game world. During each game day:
- a single random character will solve a small personal class-specific quest
- a group of characters will embark on a difficult adventure
- a lower-level character will attempt to fight a higher-level character
- all characters will take a rest.\n
The choice of class when registering has a large impact on how your character will perform. Different classes use different dice when rolling to determine the outcomes of challenges. Classes can also have different maximum hit points values and different experience targets for leveling up.\n
Losing at challenges will hurt your character. If a character's hit points (HP) run out, they will permanently die and will be reincarnated at level 0, with the same name and class.\n
If a character has earned enough experience to reach the next level, they will level up and heal to full when resting.\n
You can find the full source code for the project at <https://github.com/ffyy/idlerpg>
                """
            case "1":
                response = """
Characters can gain experience in the following ways: by completing a personal quest, by succeeding at a group quest, by ganking someone in PvP and passively throughout the day.\n
- **Personal quests**: Between 500 and 2000 XP is randomly awarded simply for being the character chosen to undertake a personal quest. This selection and the xp reward from it is the only roll in the game which doesn't use the class specific dice to determine its outcome.
- **Group quests**: XP is awarded based on the difficulty of the quest. The quest difficulty is randomly determined by the DM. The maximum XP reward is 10000 (enough for one entire level for a class with average leveling speed) and scales linearly with the average target number each party member should hit. For example, if the difficulty for a two-character quest is 200, it means both characters would need to roll a 100 to win, and they would be awarded 10000 xp each. If the quest difficulty for the same party were 60, it would mean the average target would be 30, and the xp reward would be 10000*30/100 = 3000 xp each.
- **PvP**: XP is awarded based on the level difference between the ganker and the defender. 1000 xp, up to a maximum of 10000, is awarded per each level the defender has over the ganker. The minimum xp from winning a PvP encounter is 1000, even when fighting a character of the same level.
- **Passive XP**: Each time characters rest, all characters roll to determine how much passive xp they gained during the day. The maximum amount of xp earned passively each day is 3600 and it scales linearly with the result of the passive xp roll. The class-specific dice are used for this roll, but gearscore is not used. For example, since the maximum roll a Hobbit can get is 50 (a result of 10 on each of their 5 dice), a Hobbit can gain at most 1800 xp passively each day.
"""
            case "2":
                response = """
When the DM runs a quest, an adventuring party is first randomly put together. If multiple characters exist in the world, the party size ranges from 2 to half of all characters. All characters are always eligible to go on quests.\n
The DM randomly determines the difficulty of the quest. The quest difficulty scales with party size. The DM determines the minimum average roll for the party members and multiplies it by the number of characters in the party. The minimum difficulty per party member is 20 and the maximum is 100.\n
Suceeding at the quest always awards all characters in the party with experience. If the party rolls very well, a magic item which increases gearscore can also be awarded.
- For specifics on the xp calculation, see the 'Experience' section of the rules.
- For specifics on the item rewards, see the 'Gear' section of the rules.
- If the party includes any Clerics, succeeding at a quest also heals all members of the party. With the exception of leveling up, this is the only way to regain lost hit points.\n
Failure at the quest awards nothing. All characters involved in the quest also lose hit points. The amount of hp lost scales linearly with the ratio of the party's total roll to the quest difficulty, with a theoretical maximum of 100. For example, if the quest difficulty was 100 and the party rolls total was 65, all members of the party will lose 35 hp.
"""
            case "3":
                response = """
Gear and gearscore are an abstraction of all the magical items the character has acquired throughout their adventuring career. The character's gearscore value is used in rolls which determine success at encounters (group quests and PvP).
Items can be gained in the following ways:
- **Be a Hobbit**: All Hobbits start with a gearscore of 20, because all adventuring Hobbits have a powerful magic ring.
- **Do well at party quests**: If the party succeeds at a group quest, there is a chance that the party member with the highest roll is awarded a magic item. The chance for an item to be awarded scales with the ratio of the party's total roll compared to the quest difficulty, with a 100% chance if the party's total roll is double the quest difficulty, going down to 1% if the party just barely met the target number. A magic item is also always awarded if the party succeeds at the quest and the average roll in the party is above 80. For example, for a four-character party, if the total party roll is at least 320, an item is guaranteed to be awarded, as long as that roll was enough to beat the quest difficulty.
- **Kill other characters**: If a character dies in a PvP encounter, the killer is guaranteed at least one magic item. If the character who died had a gearscore higher than 1, a random number of items, up to the dead character's gearscore, is awarded to the killer.\n
Items which are found by characters are not immediately equipped. When a character finds an item, it is considered unattuned. Magic items are only equipped (the character's gearscore increased) during long rests.
                """
            case "4":
                response = """
PvP is a high-risk/high-reward catch-up activity. In PvP encounters, a character who is falling behind in levels attacks a character ahead of them in an attempt to gain bonus experience.\n
If there are enough characters in the world for tensions to develop, every game day, a PvP encounter is triggered. Only characters in the bottom half of the leaderboard are eligible to trigger PvP encounters. All characters ahead of them on the leaderboard are possible targets.\n
In the PvP encounter, the two characters roll off directly against each other.
- For the roll, class dice plus gearscore is used.
- The character with the higher roll wins the encounter.
- The losing character loses hp equal to the difference in rolls.
- If any character dies in the encounter, the winner loots at least one magic item from the corpse. See the 'Items' section of the rules for more info.
- If the instigator wins the encounter, they earn bonus experience. See the 'Experience' section of the rules for more info.
"""
            case _:
                response = "Tunnel snakes rule"
        response = "\n".join([response, "Select the next section to read:"])
        await interaction.response.edit_message(content=response)

@client.tree.command(name="rules", description="Display game rules")
async def rules(interaction: discord.Interaction):
    await interaction.response.send_message("Choose a section of rules to read.", view=RulesView(), ephemeral=True)

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

    adventure_report = [title_text, quest_results[1]]
    adventure_report[0] = "".join([adventure_report[0], quest_results[0]])

    return adventure_report

def create_pvp_report():
    pvp_results = dungeonmaster.run_pvp_encounter()
    title_text = "**Heroes fighting heroes!**\n"

    pvp_report = [title_text, []]
    pvp_report[0] = "".join([pvp_report[0], pvp_results[0]])
    if len(pvp_results[1]) > 0:
        pvp_report[1] = pvp_results[1]
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

async def create_graveyard_report(name, class_filter):
    character_classes = charutils.get_all_classes()
    class_id = None
    title_text = "Top dead characters"

    if name:
        title_text = "Top dead characters called " + name
    if class_filter:
        character_class = next((character_class for character_class in character_classes if character_class.name.lower() == class_filter.lower()), None)
        if character_class:
            class_id = character_class.id_
            title_text = " ".join([title_text, "with class"])
            title_text = " ".join([title_text, character_class.name])

    title_text = " ".join([title_text, "in this world:"])

    members_list = client.get_all_members()
    users_list = []
    for member in members_list:
        member_name = re.sub("[`>*]", "", member.display_name)
        users_list.append({"id":member.id, "name":member_name})
    graveyard = charutils.get_graveyard(name, users_list, class_id)

    if graveyard == "":
        return None

    graveyard_report = title_text
    graveyard_report = "".join([graveyard_report, graveyard])
    return graveyard_report

print("starting bot")
client.run(TOKEN)
