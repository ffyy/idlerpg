import random
import charutils
from rpgobjects import *

QUEST_HOOKS = open("content/quests.txt").read().splitlines()
SUCCESS_DESCRIPTIONS = open("content/successes.txt").read().splitlines()
FAILURE_DESCRIPTIONS = open("content/failures.txt").read().splitlines()

def give_rewards(quest: Quest):
    if quest.quest_type == "Experience":
        for adventurer in quest.party:
            adventurer.current_xp += 5000
            charutils.update_db_character(charutils.character_to_db_character(adventurer))
    elif quest.quest_type == "Loot":
        for adventurer in quest.party:
            adventurer.gear.unattuned += 1
            charutils.update_db_gear(adventurer.gear)

def run_quest(dm_quest: Quest) -> Quest:
    completed_quest = dm_quest
    for adventurer in dm_quest.party:
        adventurer_roll = adventurer.roll_dice() + adventurer.gear.gearscore
        completed_quest.party_rolls.append(adventurer_roll)

    if sum(completed_quest.party_rolls) > dm_quest.quest_difficulty:
        completed_quest.outcome = 1
        completed_quest.quest_journal = ' '.join([completed_quest.quest_journal, "Luckily,"])
        completed_quest.quest_journal = ' '.join([completed_quest.quest_journal, random.choice(SUCCESS_DESCRIPTIONS)])
        if dm_quest.quest_type == "Experience":
            completed_quest.quest_journal = ' '.join([completed_quest.quest_journal, "This was a very valuable experience for everyone."])
        elif dm_quest.quest_type == "Loot":
            completed_quest.quest_journal = ' '.join([completed_quest.quest_journal, "Everyone found a magic item."])
        completed_quest.quest_journal = '\n'.join([completed_quest.quest_journal, str(sum(completed_quest.party_rolls))])
        completed_quest.quest_journal = '/'.join([completed_quest.quest_journal, str(dm_quest.quest_difficulty)])        
        completed_quest.quest_journal = '\n'.join([completed_quest.quest_journal, "**Success!**"])
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
    
    QUEST_TYPES = ["Experience", "Loot"]
    quest_type = random.choice(QUEST_TYPES)

    quest_hook = ' '.join(["The heroes were given an epic quest. They had to", random.choice(QUEST_HOOKS)])

    quest = Quest(quest_type, [], [], 0, quest_hook, 0)
    
    if not character_ids:
        return quest 
    
    if(len(character_ids)) == 1:
        quest.party.append(charutils.get_character_by_id(character_ids[0][0]))
    else:
        for character_id in random.sample(character_ids, k=len(character_ids)//2):
            quest.party.append(charutils.get_character_by_id(character_id[0]))   

    difficulty = random.randint(1,100*len(quest.party))
    quest.quest_difficulty = difficulty

    completed_quest = run_quest(quest)
    return completed_quest

def run_long_rest():
    character_ids = charutils.get_character_ids()

    old_characters = []
    rested_characters = []
    day_report = []
    for character_id in character_ids:
        old_characters.append(charutils.get_character_by_id(character_id[0]))

    for old_character in old_characters:
        old_character.current_xp += 3600 #with timescale 60, everyone gets 1 xp per second
        rested_characters.append(old_character.take_long_rest())

    old_characters.sort(key=lambda character: character.id_)
    rested_characters.sort(key=lambda character: character.id_)

    for i, rested_character in enumerate(rested_characters):
        charutils.update_db_character(charutils.character_to_db_character(rested_character))
        if rested_character.level != old_characters[i].level or rested_character.gear.gearscore != old_characters[i].gear.gearscore:
            personal_report = DayReport(rested_character.name, rested_character.level, rested_character.gear.gearscore)
            if rested_character.level != old_characters[i].level:
                personal_report.level_result = str(old_characters[i].level) + "->" + str(rested_character.level)
            if rested_character.gear.gearscore != old_characters[i].gear.gearscore:
                personal_report.gearscore_result = str(old_characters[i].gear.gearscore) + "->" + str(rested_character.gear.gearscore)
            day_report.append(personal_report)

    return day_report