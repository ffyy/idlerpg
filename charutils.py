import json
import os
import shutil

class Character:
    def __init__(
            self, 
            name,
            level,
            current_xp
            ):
        self.name = name
        self.level = level
        self.current_xp = current_xp

def save_to_disk(character: Character):
    if not os.path.exists("chars"):
        try:
            os.mkdir("chars")
        except Exception:
            print(str(Exception))

    file_name = "chars/" + character.name
    #print(file_name)
    if os.path.isfile(file_name + ".txt"): 
        shutil.copyfile(file_name + ".txt", file_name + ".bak")
    
    #print("save_to_disk_says " + str(vars(character)))
    character_json = json.dumps(vars(character))
    f = open(os.path.join(file_name + ".txt"), "w")
    f.write(character_json)
    f.close()

def create_character(name):
    new_character = Character(name, 0, 0)
    #print(json.dumps(vars(new_character)))
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
        loaded_character = Character(json_character['name'], json_character['level'], json_character['current_xp'])
        return "The name is " + loaded_character.name + " and it is level " + str(loaded_character.level)
        #return "tuut tuut"