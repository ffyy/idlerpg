import random
import charutils
from rpgobjects import *

def run_quest(dm_quest: Quest) -> Quest:
    completed_quest = dm_quest
    #print("starting to handle quest: " + str(vars(dm_quest)))
    for adventurer in dm_quest.party:
        adventurer_roll = adventurer.roll_dice() + adventurer.gear.gearscore
        print(adventurer.name + " rolled a " + str(adventurer_roll))
        completed_quest.party_rolls.append(adventurer_roll)

    if sum(completed_quest.party_rolls) > dm_quest.quest_difficulty:
        completed_quest.outcome = 1
        #also give characters rewards here depending on quest type
    else:
        completed_quest.outcome = 0

    return completed_quest

def run_adventure():
    character_ids = charutils.get_character_ids()
    
    QUEST_TYPES = ["Experience", "Gear"]
    quest_type = QUEST_TYPES[0] #do random in future

    quest = Quest(quest_type, [], [], 0, 0)
    
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

    adventure_result = "An epic adventure was had! The Encounter difficulty was: " + str(completed_quest.quest_difficulty) + "\nOutcome: "
    if completed_quest.outcome == 1: adventure_result = ''.join([adventure_result,"Success!"])
    elif completed_quest.outcome == 0: adventure_result = ''.join([adventure_result,"Failure!"])
    adventure_result = ' '.join([adventure_result, "Party total roll was:"])
    adventure_result = ' '.join([adventure_result, str(sum(completed_quest.party_rolls))])
    adventure_result = ''.join([adventure_result,"\nParticipants and rolls:"])
    for i, party_member in enumerate(completed_quest.party):
        adventure_result = '\n'.join([adventure_result, party_member.name])
        adventure_result = ' - '.join([adventure_result, str(completed_quest.party_rolls[i])])

    return adventure_result