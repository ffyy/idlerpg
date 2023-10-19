import random
import charutils
from rpgobjects import *

def encounter_outcome(adventurer):
    encounter_difficulty = 0
    adventurer_roll = 5
    if adventurer_roll >= encounter_difficulty:
        return [1, adventurer_roll, encounter_difficulty]
    else:
        return [0, adventurer_roll, encounter_difficulty]

def run_adventure():
    adventurers = []
    character_ids = charutils.get_character_ids()
    if not character_ids:
        return "I tried to run an adventure but there were no characters around" 
    
    for character_id in character_ids:
        adventurers.append(charutils.get_character_by_id(character_id[0]))
    
    party = random.choices(adventurers, weights=None, k=len(adventurers)//2) 
    
    outcomes = []
    for adventurer in party:
        adventurer_outcome = (adventurer.name, encounter_outcome(adventurer))
        outcomes.append(adventurer_outcome)

    return outcomes