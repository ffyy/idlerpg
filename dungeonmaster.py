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
            adventurer.gear.gearscore += 1
            charutils.update_db_gear(adventurer.gear)

def run_quest(dm_quest: Quest) -> Quest:
    completed_quest = dm_quest
    #print("starting to handle quest: " + str(vars(dm_quest)))
    for adventurer in dm_quest.party:
        adventurer_roll = adventurer.roll_dice() + adventurer.gear.gearscore
        print(adventurer.name + " rolled a " + str(adventurer_roll))
        completed_quest.party_rolls.append(adventurer_roll)

    if sum(completed_quest.party_rolls) > dm_quest.quest_difficulty:
        completed_quest.outcome = 1
        completed_quest.quest_journal = ' '.join([completed_quest.quest_journal, "Luckily,"])
        completed_quest.quest_journal = ' '.join([completed_quest.quest_journal, random.choice(SUCCESS_DESCRIPTIONS)])
        completed_quest.quest_journal = '\n'.join([completed_quest.quest_journal, str(sum(completed_quest.party_rolls))])
        completed_quest.quest_journal = '/'.join([completed_quest.quest_journal, str(dm_quest.quest_difficulty)])        
        completed_quest.quest_journal = '\n'.join([completed_quest.quest_journal, "**Success!**"])
        give_rewards(completed_quest)
    else:
        completed_quest.quest_journal = ' '.join([completed_quest.quest_journal, "Unfortunately,"])
        completed_quest.quest_journal = ' '.join([completed_quest.quest_journal, random.choice(FAILURE_DESCRIPTIONS)])
        completed_quest.quest_journal = '\n'.join([completed_quest.quest_journal, str(sum(completed_quest.party_rolls))])
        completed_quest.quest_journal = '/'.join([completed_quest.quest_journal, str(dm_quest.quest_difficulty)])  
        completed_quest.quest_journal = '\n'.join([completed_quest.quest_journal, "**Failure!**"])
        completed_quest.outcome = 0

    return completed_quest

def run_adventure():
    character_ids = charutils.get_character_ids()
    
    QUEST_TYPES = ["Experience", "Loot"]
    quest_type = QUEST_TYPES[0] #do random in future

    quest_hook = ' '.join(["The heroes were given an epic quest. They had to", random.choice(QUEST_HOOKS)])

    quest = Quest(quest_type, [], [], 0, quest_hook, 0)
    
    if not character_ids:
        return "I tried to run an adventure but there were no characters around" 
    
    if(len(character_ids)) == 1:
        quest.party.append(charutils.get_character_by_id(character_ids[0]))
    else:
        for character_id in random.sample(character_ids, k=len(character_ids)//2):
            quest.party.append(charutils.get_character_by_id(character_id[0]))   

    difficulty = random.randint(1,100*len(quest.party))
    quest.quest_difficulty = difficulty

    completed_quest = run_quest(quest)
    return completed_quest