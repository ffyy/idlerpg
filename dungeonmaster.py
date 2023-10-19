import random
import charutils
from rpgobjects import *

def overcome_encounter(adventurer: Character, encounter_difficulty):
    adventurer_roll = adventurer.roll_dice() + adventurer.gear.gearscore
    
    if adventurer_roll >= encounter_difficulty:
        charutils.level_up_by_id(adventurer.id_)
        return [1, adventurer_roll]
    else:
        return [0, adventurer_roll]

def run_adventure():
    adventurers = []
    character_ids = charutils.get_character_ids()
    if not character_ids:
        return "I tried to run an adventure but there were no characters around" 
    
    for character_id in character_ids:
        adventurers.append(charutils.get_character_by_id(character_id[0]))
    
    if len(adventurers) == 1:
        party = adventurers[0]
    else:
        party = random.sample(adventurers, k=len(adventurers)//2) 
    
    encounter_difficulty = random.randint(1,100)
    
    encounter_outcomes = []
    for adventurer in party:
        adventurer_outcome = (adventurer.name, overcome_encounter(adventurer, encounter_difficulty))
        encounter_outcomes.append(adventurer_outcome)

    adventure_result = "An epic adventure was had! The Encounter difficulty was: " + str(encounter_difficulty) + "\nParticipants and outcomes:"
    for outcome in encounter_outcomes:
        adventure_result = '\n'.join([adventure_result, outcome[0]])
        if outcome[1][0] == 1:
            adventure_result = ' - '.join([adventure_result, "Success!"])
            adventure_result = ' | '.join([adventure_result, "Roll: "])
            adventure_result = ''.join([adventure_result, str(outcome[1][1])])
        elif outcome[1][0] == 0:
            adventure_result = ' - '.join([adventure_result, "Failure! "])
            adventure_result = ' | '.join([adventure_result, "Roll: "])
            adventure_result = ''.join([adventure_result, str(outcome[1][1])])

    return adventure_result