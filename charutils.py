import json
import os
import shutil
from datetime import datetime

class Character:
    def __init__(
            self, 
            name,
            level,
            current_xp,
            gear
            ):
        self.name = name
        self.level = level
        self.current_xp = current_xp
        self.gear = gear

class Gear:
    def __init__(self, gearscore):
        self.gearscore = gearscore

def save_to_disk(character: Character):
    if not os.path.exists("chars"):
        try:
            os.mkdir("chars")
        except Exception:
            print(str(Exception))

    file_name = "chars/" + character.name
    #print(file_name)
    if os.path.isfile(file_name + ".txt"): 
        with open(os.path.join(file_name + ".txt"), "r") as txtfile:
            with open(os.path.join(file_name + ".bak"), "a") as bakfile:
                bakfile.write('\n\n' + str(datetime.now()) + '\n')
                shutil.copyfileobj(txtfile, bakfile)
    
    #print("save_to_disk_says " + str(vars(character)))
    character_json = json.dumps(vars(character), default=lambda x: x.__dict__)
    f = open(os.path.join(file_name + ".txt"), "w")
    f.write(character_json)
    f.close()

def create_character(name):
    new_character = Character(name, 0, 0, Gear(5))
    #print(json.dumps(vars(new_character)))
    print(vars(new_character))
    try:
        save_to_disk(new_character)
        return "Saved character called " + new_character.name + " to disk"
    except:
        raise Exception("save_to_disk failed") 
    
def get_character(name):
    file_path = os.path.join("chars/" + name + ".txt")
    f = open(file_path)
    json_character = json.load(f)
    #print(json_character) #debug
    loaded_character = Character(json_character['name'], json_character['level'], json_character['current_xp'], json_character['gear'])
    print(vars(loaded_character))
    return "The name is " + loaded_character.name + " and it has gear of level " + str(loaded_character.gear['gearscore'])

def update_gear(name, value):
    file_path = os.path.join("chars/" + name + ".txt")
    f = open(file_path)
    json_character = json.load(f)
    #print(json_character) #debug
    loaded_character = Character(json_character['name'], json_character['level'], json_character['current_xp'], Gear(json_character['gear']['gearscore']))
    print(vars(loaded_character))
    loaded_character.gear.gearscore += value
    save_to_disk(loaded_character)
    return str(loaded_character.name) + " now has a gearscore of " + str(loaded_character.gear.gearscore)