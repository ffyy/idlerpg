import random
import charutils
from rpgobjects import *

def overcome_encounter(party: list[Character], encounter_difficulty):
    party_roll = 0
    encounter_results = []

    for adventurer in party:
        adventurer_roll = adventurer.roll_dice() + adventurer.gear.gearscore
        party_roll += adventurer_roll
        encounter_results.append([adventurer.name, str(adventurer_roll)])
    
    if party_roll >= encounter_difficulty:
        for adventurer in party:
            charutils.level_up_by_id(adventurer.id_)
        return [1, encounter_results]
    else:
        return [0, encounter_results]

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
    
    encounter_difficulty = random.randint(1,100*len(party))

    encounter_outcome = overcome_encounter(party, encounter_difficulty)

    adventure_result = "An epic adventure was had! The Encounter difficulty was: " + str(encounter_difficulty) + "\nOutcome: "
    if encounter_outcome[0] == 1: adventure_result = ''.join([adventure_result,"Success!"])
    elif encounter_outcome[0] == 0: adventure_result = ''.join([adventure_result,"Failure!"])
    adventure_result = ''.join([adventure_result,"\nParticipants and rolls:"])
    for participant in encounter_outcome[1]:
        adventure_result = '\n'.join([adventure_result, participant[0]])
        adventure_result = ' - '.join([adventure_result, participant[1]])

    return adventure_result