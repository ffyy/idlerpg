import random
import charutils
from rpgobjects import *
from helpers import *

QUEST_HOOKS = open("content/quests.txt").read().splitlines()
SUCCESS_DESCRIPTIONS = open("content/successes.txt").read().splitlines()
FAILURE_DESCRIPTIONS = open("content/failures.txt").read().splitlines()
ITEMS = open("content/items.txt").read().splitlines()

def give_rewards(quest: Quest):
    if "experience" in quest.quest_type:
        for adventurer in quest.party:
            adventurer.current_xp += int(10000*(quest.quest_difficulty/(100*len(quest.party))))
            charutils.update_db_character(charutils.character_to_db_character(adventurer))
    if "loot" in quest.quest_type:
        carry_index = quest.party_rolls.index(max(quest.party_rolls))
        quest.party[carry_index].gear.unattuned += 1
        charutils.update_db_gear(quest.party[carry_index].gear)


def run_quest(dm_quest: Quest) -> Quest:
    QUEST_ITEM_THRESHOLD = 0.8
    
    completed_quest = dm_quest
    for adventurer in dm_quest.party:
        adventurer_roll = adventurer.roll_dice() + adventurer.gear.gearscore
        completed_quest.party_rolls.append(adventurer_roll)

    party_max_roll = 100*len(dm_quest.party)
    if (random.randint(1,100) <= 100*(sum(completed_quest.party_rolls) - dm_quest.quest_difficulty)/dm_quest.quest_difficulty) or (party_max_roll * QUEST_ITEM_THRESHOLD <= sum(completed_quest.party_rolls)):
        completed_quest.quest_type.append("loot")

    if sum(completed_quest.party_rolls) > dm_quest.quest_difficulty:
        completed_quest.outcome = 1
        completed_quest.quest_journal = ' '.join([completed_quest.quest_journal, "Luckily,"])
        completed_quest.quest_journal = ' '.join([completed_quest.quest_journal, random.choice(SUCCESS_DESCRIPTIONS)])
        if "loot" in dm_quest.quest_type:
            carry_index = completed_quest.party_rolls.index(max(completed_quest.party_rolls))
            item_name = random.choice(ITEMS)
            completed_quest.quest_journal = ' '.join([completed_quest.quest_journal, completed_quest.party[carry_index].name])
            completed_quest.quest_journal = ' '.join([completed_quest.quest_journal, "also found"])
            if item_name[0] in "aeoiu":
                completed_quest.quest_journal = ' '.join([completed_quest.quest_journal, "an"])
            else:
                completed_quest.quest_journal = ' '.join([completed_quest.quest_journal, "a"])
            completed_quest.quest_journal = ' '.join([completed_quest.quest_journal, item_name])
            completed_quest.quest_journal = ''.join([completed_quest.quest_journal, "!"])
        if "experience" in dm_quest.quest_type:
            completed_quest.quest_journal = '\n'.join([completed_quest.quest_journal, "XP reward:"])
            completed_quest.quest_journal = ' '.join([completed_quest.quest_journal, str(int(10000*(completed_quest.quest_difficulty/party_max_roll)))])
        completed_quest.quest_journal = '\n'.join([completed_quest.quest_journal, str(sum(completed_quest.party_rolls))])
        completed_quest.quest_journal = '/'.join([completed_quest.quest_journal, str(dm_quest.quest_difficulty)])        
        completed_quest.quest_journal = ' - '.join([completed_quest.quest_journal, "**Success!**"])
        give_rewards(completed_quest)
    else:
        completed_quest.outcome = 0
        completed_quest.quest_journal = ' '.join([completed_quest.quest_journal, "Unfortunately,"])
        completed_quest.quest_journal = ' '.join([completed_quest.quest_journal, random.choice(FAILURE_DESCRIPTIONS)])
        completed_quest.quest_journal = '\n'.join([completed_quest.quest_journal, str(sum(completed_quest.party_rolls))])
        completed_quest.quest_journal = '/'.join([completed_quest.quest_journal, str(dm_quest.quest_difficulty)])  
        completed_quest.quest_journal = '\n'.join([completed_quest.quest_journal, "**Failure!**"])

    return completed_quest

def run_adventure() -> Quest:
    character_ids = charutils.get_character_ids()
    
    QUEST_TYPES = ["experience", "loot"]
    quest_type = ["experience"]

    quest_hook = ' '.join(["The heroes were given an epic quest. They had to", random.choice(QUEST_HOOKS)])

    quest = Quest(quest_type, [], [], 0, quest_hook, 0)

    if not character_ids:
        return quest 
    
    if(len(character_ids)) == 1:
        quest.party.append(charutils.get_character_by_id(character_ids[0][0]))
    else:
        party_size = random.randint(2,(max(2, (len(character_ids)//2))))
        for character_id in random.sample(character_ids, party_size):
            quest.party.append(charutils.get_character_by_id(character_id[0]))   

    difficulty = random.randint(1,100*len(quest.party))
    quest.quest_difficulty = difficulty

    completed_quest = run_quest(quest)
    
    completed_quest_lists = []
    completed_quest_lists.append(["Hero"])
    completed_quest_lists.append(["Class"])
    completed_quest_lists.append(["Level"])
    completed_quest_lists.append(["GS"])
    completed_quest_lists.append(["Roll"])
    
    for i,hero in enumerate(completed_quest.party):
        completed_quest_lists[0].append(hero.name)
        completed_quest_lists[1].append(hero.character_class.name)
        completed_quest_lists[2].append(str(hero.level))
        completed_quest_lists[3].append(str(hero.gear.gearscore))
        completed_quest_lists[4].append(str(completed_quest.party_rolls[i]))
    
    quest_table = make_table(completed_quest_lists)

    completed_quest.quest_journal = "".join([completed_quest.quest_journal, quest_table])

    return completed_quest

def run_pvp_encounter():
    all_characters = charutils.get_all_characters()
    if len(all_characters) < 6:
        return ["I tried to incite violence, but there weren't enough characters around for PvP.",""]
    
    all_characters.sort(key=lambda character:character.level)
    i_ganker = randint(0, len(all_characters)//2) #ganker index
    pvp_characters = []
    pvp_characters.append(all_characters[i_ganker])
    del all_characters[0:i_ganker+1]
    pvp_characters.append(random.choice(all_characters))

    pvp_rolls = []
    for character in pvp_characters:
        character_roll = character.roll_dice() + character.gear.gearscore
        pvp_rolls.append(character_roll)
    pvp_journal = [pvp_characters[0].name + " tried to gank " + pvp_characters[1].name + "!"]
    xp_reward = max(1, pvp_characters[1].level - pvp_characters[0].level) * 2000
    if pvp_rolls[0] >= pvp_rolls[1]:
        pvp_journal[0] = "\n".join([pvp_journal[0], "**Success!**"])
        pvp_journal[0] = "\n".join([pvp_journal[0], pvp_characters[0].name])
        pvp_journal[0] = " ".join([pvp_journal[0], "gained"])
        pvp_journal[0] = " ".join([pvp_journal[0], str(xp_reward)])
        pvp_journal[0] = " ".join([pvp_journal[0], "experience."])
        debug_print(pvp_characters[0].current_xp)
        pvp_characters[0].current_xp += xp_reward
        debug_print(pvp_characters[0].current_xp)
        charutils.update_db_character(charutils.character_to_db_character(pvp_characters[0]))
    elif pvp_rolls[0] < pvp_rolls[1]:
        pvp_journal[0] = "\n".join([pvp_journal[0], "**Failure!**"])
    pvp_journal[0] = "\n".join([pvp_journal[0], "Here is how it played out:"])

    pvp_report_lists = []
    pvp_report_lists.append(["Fighter"])
    pvp_report_lists.append(["Class"])
    pvp_report_lists.append(["Level"])
    pvp_report_lists.append(["GS"])
    pvp_report_lists.append(["Roll"])

    for i,fighter in enumerate(pvp_characters):
        pvp_report_lists[0].append(fighter.name)
        pvp_report_lists[1].append(fighter.character_class.name)
        pvp_report_lists[2].append(str(fighter.level))
        pvp_report_lists[3].append(str(fighter.gear.gearscore))
        pvp_report_lists[4].append(str(pvp_rolls[i]))

    pvp_journal.append(make_table(pvp_report_lists))

    return pvp_journal

def run_long_rest():
    old_characters = charutils.get_all_characters()
    rested_characters = []
    day_report = []

    for old_character in old_characters:
        old_character.current_xp += old_character.roll_for_passive_xp()
        rested_characters.append(old_character.take_long_rest())

    old_characters.sort(key=lambda character: character.id_)
    rested_characters.sort(key=lambda character: character.id_)

    for i, rested_character in enumerate(rested_characters):
        charutils.update_db_character(charutils.character_to_db_character(rested_character))
        charutils.update_db_gear(rested_character.gear)
        if rested_character.level != old_characters[i].level or rested_character.gear.gearscore != old_characters[i].gear.gearscore:
            personal_report = DayReport(rested_character.name, rested_character.level, rested_character.gear.gearscore)
            if rested_character.level != old_characters[i].level:
                personal_report.level_result = str(old_characters[i].level) + "->" + str(rested_character.level)
            if rested_character.gear.gearscore != old_characters[i].gear.gearscore:
                personal_report.gearscore_result = str(old_characters[i].gear.gearscore) + "->" + str(rested_character.gear.gearscore)
            day_report.append(personal_report)
    
    if len(day_report) == 0:
        return ""
    else:
        table_lists = []
        table_lists.append(["Character"])
        table_lists.append(["Level"])
        table_lists.append(["Gearscore"])

        for character in day_report:
            table_lists[0].append(character.character_name)
            table_lists[1].append(str(character.level_result))
            table_lists[2].append(str(character.gearscore_result))

        string_day_report = make_table(table_lists)

        return string_day_report