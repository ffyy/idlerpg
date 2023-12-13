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
from random import randint

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = os.getenv("GUILD_ID")
CHANNEL_ID = os.getenv("CHANNEL_ID")
DAY_LENGTH = int(os.getenv("DAY_LENGTH"))
DEBUG_MODE = os.getenv("DEBUG_MODE")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

if not os.path.exists(".conf"):
    initialsetup.do()

GUILD = discord.Object(id=int(GUILD_ID))
CHANNEL = discord.Object(id=int(CHANNEL_ID))
DM = dungeonmaster.DungeonMaster()

class RpgEngine(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self) -> None:
        self.tree.copy_global_to(guild=GUILD)

    async def on_ready(self):
        await self.tree.sync(guild=GUILD)
        print("commands synced")
        await sleep(60*DAY_LENGTH/4)
        self.run_daily_events.start()
        await sleep(60*DAY_LENGTH/2)
        self.run_monthly_events.start()
        print(str(datetime.datetime.now()) + " - loops started")

    @tasks.loop(minutes=DAY_LENGTH/4)
    async def run_daily_events(self):
        print(str(datetime.datetime.now()) + " - running a random daily event")
        channel = self.get_channel(CHANNEL.id)
        event_outcomes = DM.choose_and_run_daily_event()
        await send_event_messages(channel, event_outcomes)

    @tasks.loop(minutes=DAY_LENGTH)
    async def run_monthly_events(self):
        print(str(datetime.datetime.now()) + " - running a random monthly event")
        channel = self.get_channel(CHANNEL.id)
        monthly_event_outcomes = DM.choose_and_run_monthly_event()
        await send_event_messages(channel, monthly_event_outcomes)

intents = discord.Intents.default()
intents.members = True
client = RpgEngine(intents=intents)


# DEBUG COMMANDS
if DEBUG_MODE == "1":
    @client.tree.command(name="raid",description="Run a raid boss encounter") #testing command
    async def raid(interaction: discord.Interaction):
        if interaction.user.id == ADMIN_ID:
            await interaction.response.send_message(content="Running a raid boss encounter")
            event_outcomes = DM.run_raidboss_encounter()
            await send_event_messages(interaction.channel, event_outcomes)
        else:
            await interaction.response.send_message("You are not an admin", ephemeral=True)

    @client.tree.command(name="gangbang",description="Run a group fight") #testing command
    async def gangbang(interaction: discord.Interaction):
        if interaction.user.id == ADMIN_ID:
            await interaction.response.send_message(content="Running a group fight")
            event_outcomes = DM.run_group_pvp()
            await send_event_messages(interaction.channel, event_outcomes)
        else:
            await interaction.response.send_message("You are not an admin", ephemeral=True)

    @client.tree.command(name="classquest",description="Run a class quest") #testing command
    async def classquest(interaction: discord.Interaction):
        if interaction.user.id == ADMIN_ID:
            await interaction.response.send_message(content="Running a class quest")
            event_outcomes = DM.run_class_quest()
            await send_event_messages(interaction.channel, event_outcomes)
        else:
            await interaction.response.send_message("You are not an admin", ephemeral=True)

    @client.tree.command(name="randomevent",description="Run a random event") #testing command
    async def randomevent(interaction: discord.Interaction):
        if interaction.user.id == ADMIN_ID:
            await interaction.response.send_message("Running a random event")
            event_outcomes = DM.choose_and_run_daily_event()
            await send_event_messages(interaction.channel, event_outcomes)
        else:
            await interaction.response.send_message("You are not an admin", ephemeral=True)

    @client.tree.command(name="adventure",description="Run an adventure") #testing command
    async def adventure(interaction: discord.Interaction):
        if interaction.user.id == ADMIN_ID:
            await interaction.response.send_message("Running Adventure")
            event_outcomes = DM.run_adventure()
            await send_event_messages(interaction.channel, event_outcomes)
        else:
            await interaction.response.send_message("You are not an admin", ephemeral=True)

    @client.tree.command(name="pvp",description="Run a PvP encounter") #testing command
    async def pvp(interaction: discord.Interaction):
        if interaction.user.id == ADMIN_ID:
            await interaction.response.send_message("Running PvP")
            event_outcomes = DM.run_pvp_encounter()
            await send_event_messages(interaction.channel, event_outcomes)
        else:
            await interaction.response.send_message("You are not an admin", ephemeral=True)

    @client.tree.command(name="rest",description="Take a long rest") #testing command
    async def rest(interaction: discord.Interaction):
        if interaction.user.id == ADMIN_ID:
            await interaction.response.send_message("Running a long rest")
            event_outcomes = DM.run_long_rest()
            await send_event_messages(interaction.channel, event_outcomes)
        else:
            await interaction.response.send_message("You are not an admin", ephemeral=True)

    @client.tree.command(name="restart",description="Restart the bot") #admin command
    async def restart(interaction: discord.Interaction):
        if interaction.user.id == ADMIN_ID:
            DM.load_state()
            await interaction.response.send_message("Check console")
            #exit()
        else:
            await interaction.response.send_message("You are not an admin", ephemeral=True)

#TREE COMMANDS

@client.tree.command(name="shutdown",description="Shut down the bot") #admin command
async def shutdown(interaction: discord.Interaction):
    if interaction.user.id == ADMIN_ID:
        if DM.shutdown(): await interaction.response.send_message("Shutting down")
        else: await interaction.response.send_message("Something prevented a smooth shutdown")
        await client.close()
        quit()
    else:
        await interaction.response.send_message("You are not an admin", ephemeral=True)

@client.tree.command(name="top",description="Get top X characters. Returns top 10 if no argument is given.")
async def leaderboard(interaction: discord.Interaction, top_x: typing.Optional[int], class_filter: typing.Optional[str]):
    if top_x and top_x > 0 and top_x <= 10:
        leaderboard_report = await create_leaderboard_report(top_x, class_filter)
        await interaction.response.send_message(content=leaderboard_report)
    else:
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
        deleted_character = charutils.delete_character_by_id(interaction.user.id)
        await interaction.response.edit_message(content=("You can always start again by using /register"), view=None)
        response = "**A hero has left the building!**"
        if interaction.user.nick:
            username = interaction.user.nick
        else:
            username = interaction.user.name
        clean_name = re.sub("[`>*]", "", username)
        response = "\n".join([response, clean_name])
        response = " ".join([response, "decided it was time for"])
        response = " ".join([response, deleted_character.name])
        response = " ".join([response, "to stop existing. And so it shall be."])
        await interaction.channel.send(content=response)

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
        if DEBUG_MODE == "1" and interaction.user.id == ADMIN_ID and "fake" in self.name:
            created_character = charutils.register_character(self.name, int(select.values[0]), randint(1,10000000))
        else:
            created_character = charutils.register_character(self.name, int(select.values[0]), interaction.user.id)
        await interaction.followup.edit_message(interaction.message.id, content=("Enjoy idling!"), view=None)
        response = "**A hero showed up!**"
        response = "\n".join([response, created_character.name])
        response = " ".join([response, "the"])
        response = " ".join([response, created_character.character_class.name])
        response = " ".join([response, "entered the world!"])
        response = "\n".join([response, "this character belongs to"])
        if interaction.user.nick:
            username = interaction.user.nick
        else:
            username = interaction.user.name
        response = " ".join([response, username])
        response = "".join([response, "."])
        await interaction.channel.send(response)

@client.tree.command(name="register", description="Create a new character")
async def register(interaction: discord.Interaction, name: str):
    old_character = charutils.get_character_by_player_id(interaction.user.id)
    if DEBUG_MODE == "1" and "fake" in name:
        old_character = None
    if old_character is not None:
        response = "You already have a level " + str(old_character.level) + " " + old_character.character_class.name + " called " + old_character.name + ".\nUse /delete [name] to delete your old character first."
        await interaction.response.send_message(response, ephemeral=True)
    else:
        if (charutils.is_name_valid(name)):
            await interaction.response.send_message("You need to pick a class also. Make sure to scroll the list to see more classes!", view=RegisterView(name), ephemeral=True)
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

@client.tree.command(name="dad", description="Find the previous incarnation of your current character.")
async def dad(interaction: discord.Interaction):
    current_character = charutils.get_character_by_player_id(interaction.user.id)
    if current_character:
        title_text = "The previous incarnation of your currect character:"
        results_report = charutils.parent_search(interaction.user.id)
        if results_report: await interaction.response.send_message(content=title_text + results_report)
        else: await interaction.response.send_message(content="Your character hasn't been reincarnated yet.")
    else: await interaction.response.send_message(content="You don't currently have a character. Use /register to start!", ephemeral=True)

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
        discord.SelectOption(label="PvP", value="4", description="How do characters fight each other?"),
        discord.SelectOption(label="Classes", value="5", description="What do the different classes do?"),
        discord.SelectOption(label="Raid bosses", value="6", description="How do we fight raid bosses?"),
    ]

    @discord.ui.select(placeholder="Rules section", options=rules_sections, max_values=1)
    async def reply_select(self, interaction: discord.Interaction, select: discord.ui.Select):
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
- **Be a Hunter**: Hunters will claim all gear which is dropped on party quests.
- **Do well at party quests**: If the party succeeds at a group quest, there is a chance that the party member with the highest roll is awarded a magic item. The chance for an item to be awarded scales with the ratio of the party's total roll compared to the quest difficulty, with a 100% chance if the party's total roll is double the quest difficulty, going down to 1% if the party just barely met the target number. A magic item is also always awarded if the party succeeds at the quest and the average roll in the party is above 80. For example, for a four-character party, if the total party roll is at least 320, an item is guaranteed to be awarded, as long as that roll was enough to beat the quest difficulty.
- **Kill other characters**: If a character dies in a PvP encounter, the killer is guaranteed at least one magic item. If the character who died had a gearscore higher than 1, a random number of items, up to the dead character's gearscore, is awarded to the killer.\n
Items which are found by characters are not immediately equipped. When a character finds an item, it is considered unattuned. Magic items are only equipped (the character's gearscore increased) during long rests.
                """
            case "4":
                response = """
PvP is a high-risk/high-reward catch-up activity. In PvP encounters, a character who is falling behind in levels attacks a character ahead of them in an attempt to gain bonus experience.\n
If there are enough characters in the world for tensions to develop, every game day, a PvP encounter is triggered. Only characters in the bottom half of the leaderboard are eligible to trigger PvP encounters. All characters ahead of them on the leaderboard are possible targets.\n
PvP encounters can also be triggered by two Fighters going on class quest together. Rarely, a group of characters will also group up to take on the character at the very top of the leaderboard together.\n
In the standard duel PvP encounter, characters roll off directly against each other.
- For the roll, class dice plus gearscore is used.
- The character with the higher roll wins the encounter.
- The losing character loses hp equal to the difference in rolls.
- If any character dies in the encounter, the winner loots at least one magic item from the corpse. See the 'Items' section of the rules for more info.
- If the instigator wins the encounter, they earn bonus experience. See the 'Experience' section of the rules for more info.
"""
            case "5":
                response = ""
                class_strings = []
                character_classes = charutils.get_all_classes()
                for i,character_class in enumerate(character_classes):
                    class_strings.append("")
                    class_strings[i] = "".join([class_strings[i], "**"])
                    class_strings[i] = "".join([class_strings[i], character_class.name])
                    class_strings[i] = "".join([class_strings[i], "**"])
                    class_strings[i] = "\n".join([class_strings[i], "Dice:"])
                    class_strings[i] = " ".join([class_strings[i], str(character_class.dice)])
                    class_strings[i] = " | ".join([class_strings[i], "Die size:"])
                    class_strings[i] = " ".join([class_strings[i], str(character_class.die_size)])
                    class_strings[i] = " | ".join([class_strings[i], "Bonus to rolls:"])
                    class_strings[i] = " ".join([class_strings[i], str(character_class.bonus)])
                    class_strings[i] = "\n".join([class_strings[i], "Max HP:"])
                    class_strings[i] = " ".join([class_strings[i], str(character_class.max_hp)])
                    class_strings[i] = " | ".join([class_strings[i], "XP per level:"])
                    class_strings[i] = " ".join([class_strings[i], str(character_class.xp_per_level)])
                    class_strings[i] = "".join([class_strings[i], "\n"])
                for string in class_strings:
                    response = "\n".join([response, string])
            case "6":
                response = """
Once per in-game month (30 'days'), all characters in the world will get together and try to fight a raid boss. In this fight, the characters will attack the boss in a random order.\n
If a character is higher level than the boss, they get a bonus to their roll equal to the difference between their level and the target level.\n
Characters who beat the target number deal damage to the boss depending on how much they beat the target number by. Those who fail to beat the target roll will take damage or lose items depending on the type of the boss.\n
If the character's level matches the boss target level, they take 100% of damage from the boss. If the level is less than half the target level, they take double damage. If the level is double the boss target level, they take half damage.\n
The character who gets the killing blow on the boss receives a magic item as well as an Aegis of Immortality. Having an Aegis of Immortality means that the next time the character would die, they will instead heal to full hp.\n
When a boss is defeated, all characters gain 10000 bonus experience.\n
There are two types of bosses:
- **The Dragonator** - Failing rolls against this boss hurts characters and characters can die while fighting the boss.
- **The Rust Monster** - Failing rolls against this boss reduces the character's gearscore.
"""
            case _:
                response = "Tunnel snakes rule"
        response = "\n".join([response, "Select the next section to read:"])
        await interaction.response.edit_message(content=response)

@client.tree.command(name="rules", description="Display game rules")
async def rules(interaction: discord.Interaction):
    await interaction.response.send_message("Choose a section of rules to read.", view=RulesView(), ephemeral=True)

#BOT FUNCTIONS
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

async def send_event_messages(channel, event_outcomes):
    for message in event_outcomes.outcome_messages:
        if len(message) >= 2000:
            print("message was too long:" + str(len(message)))
            message = message[:1997] + "```"
            print(message)
        await channel.send(content=message)
    if event_outcomes.deaths:
        death_notice = ""
        users_generator = client.get_all_members()
        users_list = [] #creating a new list because client.get_all_members() can only be iterated through once, but we need to do it several times
        for user in users_generator:
            users_list.append(user)
        for discord_id in event_outcomes.deaths:
            for member in users_list:
                if int(member.id) == int(discord_id):
                    user = await client.fetch_user(discord_id)
                    death_notice = " ".join([death_notice, user.mention])
        death_notice = " ".join([death_notice, "your character died and was reincarnated."])
        await channel.send(content=death_notice)

print("starting bot")
client.run(TOKEN)
