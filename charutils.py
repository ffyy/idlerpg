import os
import sqlite3
import traceback
from rpgobjects import *
from helpers import *
from dotenv import load_dotenv

load_dotenv()
DB_PATH = os.getenv("DB_PATH")

#DB FUNCTIONS

def update_db_character(character: CharacterDB):
    db = sqlite3.connect(DB_PATH)
    cur = db.cursor()
    cur.execute("UPDATE character SET name = ?, level = ?, current_xp = ?, class_id = ?, gear_id = ? WHERE id_ = ?", (character.name, character.level, character.current_xp, character.class_id, character.gear_id, character.id_))
    db.commit()
    cur.close()

def update_db_gear(gear: Gear):
    db = sqlite3.connect(DB_PATH)
    cur = db.cursor()
    cur.execute("UPDATE gear SET gearscore = ?, unattuned = ? WHERE id_ = ?", (gear.gearscore, gear.unattuned, gear.id_))
    db.commit()
    cur.close

def register_character(name, class_id, player_id):
    character = CharacterDB(None, name, 0, 0, class_id, None)
    class_name = get_class(class_id).name
    
    db = sqlite3.connect(DB_PATH)
    cur = db.cursor()
    try:
        if character.class_id == 3: #hobbits get a magic ring
            cur.execute("INSERT INTO gear(gearscore,unattuned) VALUES (20,0)")
        else: 
            cur.execute("INSERT INTO gear(gearscore,unattuned) VALUES (0,0)")
        character.gear_id = cur.lastrowid
        cur.execute("INSERT INTO character(name,level,current_xp,class_id,gear_id) VALUES (?,?,?,?,?)", (character.name, character.level, character.current_xp, character.class_id, character.gear_id))
        character.id_ = cur.lastrowid
        cur.execute("INSERT INTO player(discord_id, character_id) VALUES (?,?)", (player_id, character.id_))
        db.commit()
        cur.close()
        return "A hero called " + character.name + " showed up! " + character.name + " is a " + class_name + "."
    except:
        traceback.print_exc()
        return "Something went wrong"
    
def delete_character(player_id):
    db = sqlite3.connect(DB_PATH)
    cur = db.cursor()
    character = get_character_by_player_id(player_id)
    cur.execute("DELETE FROM character WHERE id_ = ?",(character.id_,))
    cur.execute("DELETE FROM gear WHERE id_ = ?", (character.gear.id_,))
    cur.execute("DELETE FROM player WHERE discord_id = ?", (player_id,))
    db.commit()
    cur.close()
    response = "Deleted character " + character.name
    return response

def register_player(player_id, character_id):
    db = sqlite3.connect(DB_PATH)
    cur = db.cursor()
    cur.execute("INSERT INTO player(discord_id,character_id)",(player_id, character_id))
    db.commit()
    cur.close()

def unregister_player(player_id):
    db = sqlite3.connect(DB_PATH)
    cur = db.cursor()
    try:
        cur.execute("DELETE FROM player WHERE player_id = ?",(player_id))
        delete_character(player_id)
        db.commit()
        cur.close()
        return "Deleted you & your character!"
    except:
        traceback.print_exc()
        return "Something went wrong."    

def get_character_by_name(name) -> Character:
    db = sqlite3.connect(DB_PATH)
    cur = db.cursor()
    cur.execute("SELECT * FROM character WHERE name = ?", (name,))
    db_character = cur.fetchone()
    cur.close()
    if db_character is None:
        return None
    else:    
        data_character = CharacterDB(db_character[0], db_character[1], db_character[2], db_character[3], db_character[4], db_character[5])
        character = db_character_to_character(data_character)
        return character

def get_character_by_id(id_) -> Character:
    db = sqlite3.connect(DB_PATH)
    cur = db.cursor()
    cur.execute("SELECT * FROM character WHERE id_ = ?", (id_,))
    db_character = cur.fetchone()
    cur.close()
    if db_character is None:
        return None
    else:    
        data_character = CharacterDB(db_character[0], db_character[1], db_character[2], db_character[3], db_character[4], db_character[5])
        character = db_character_to_character(data_character)
        return character
    
def get_discord_id_by_character(character):
    db = sqlite3.connect(DB_PATH)
    cur = db.cursor()
    cur.execute("SELECT discord_id FROM player WHERE character_id = ?", (character.id_,))
    db_player = cur.fetchone()
    cur.close()
    if db_player:
        return db_player[0]
    else:
        return None

def get_character_by_player_id(player_id) -> Character:
    db = sqlite3.connect(DB_PATH)
    cur = db.cursor()
    db_character = None
    cur.execute("SELECT character_id FROM player WHERE discord_id = ?", (player_id,))
    character_id = cur.fetchone()
    if character_id is not None:
        cur.execute("SELECT * FROM character WHERE id_ = ?", (character_id))
        db_character = cur.fetchone()
    cur.close()
    if db_character is not None:
        data_character = CharacterDB(db_character[0], db_character[1], db_character[2], db_character[3], db_character[4], db_character[5])
        character = db_character_to_character(data_character)
        return character
    else:
        return None

def get_character_ids() -> tuple:
    db = sqlite3.connect(DB_PATH)
    cur = db.cursor()
    cur.execute("SELECT id_ from CHARACTER")
    characters = cur.fetchall()
    return characters

def get_class(id) -> CharacterClass:
    db = sqlite3.connect(DB_PATH)
    cur = db.cursor()
    cur.execute("SELECT * FROM class WHERE id_ = ?", (id,))
    db_class = cur.fetchone()
    cur.close()
    character_class = CharacterClass(db_class[0], db_class[1], db_class[2], db_class[3], db_class[4], db_class[5], db_class[6])
    return character_class

def get_all_classes() -> list[CharacterClass]:
    classes = []
    db = sqlite3.connect(DB_PATH)
    cur = db.cursor()
    cur.execute("SELECT * FROM class")
    db_classes = cur.fetchall()
    for db_class in db_classes:
        classes.append(CharacterClass(db_class[0], db_class[1], db_class[2], db_class[3], db_class[4], db_class[5], db_class[6]))
    return classes

def get_gear(id) -> Gear:
    db = sqlite3.connect(DB_PATH)
    cur = db.cursor()
    cur.execute("SELECT * FROM gear WHERE id_ = ?", (id,))
    db_gear = cur.fetchone()
    cur.close()
    if db_gear is not None: 
        gear = Gear(db_gear[0], db_gear[1], db_gear[2])
        return gear
    else:
        return None

def character_to_db_character(character: Character) -> CharacterDB:
    db_character = CharacterDB(character.id_, character.name, character.level, character.current_xp, character.character_class.id_, character.gear.id_)
    return db_character

def db_character_to_character(character: CharacterDB) -> Character:
    game_class = get_class(character.class_id)
    game_gear = get_gear(character.gear_id)
    game_character = Character(character.id_, character.name, character.level, character.current_xp, game_class, game_gear)
    return game_character

def is_name_valid(name) -> str:
    db = sqlite3.connect(DB_PATH)
    cur = db.cursor()
    cur.execute("SELECT count(1) FROM character WHERE name = ?", (name,))
    count = int(cur.fetchone()[0])
    if count > 0 or len(name) > 20 or not name.isalpha():
        return False
    else:
        return True

def get_top10() -> str:
    db = sqlite3.connect(DB_PATH)
    cur = db.cursor()
    cur.execute("SELECT name, level FROM character ORDER BY level DESC LIMIT 10")
    return(str(cur.fetchall()))

#GAME OCCURRENCES

def level_up_by_id(character_id):
    character = get_character_by_id(character_id)
    character.level += 1
    update_db_character(character_to_db_character(character))
    return "Character " + character.name + " leveled up by going on an adventure and is now level " + str(character.level)

def level_me_up(player_id):
    character = get_character_by_player_id(player_id)
    if character is not None:
        character.level += 1
        db_character = character_to_db_character(character)
        update_db_character(db_character)
        return "Character " + character.name + " is now level " + str(character.level)
    else:
        return "You don't even have a character.\nUse /register to register a new character."
    
def get_leaderboard(top_x, users_list):
    characters = []
    top_characters = []
    for character_id in get_character_ids():
        characters.append(get_character_by_id(character_id[0]))
    characters.sort(key=lambda character: (-character.level, -character.gear.gearscore, -character.current_xp))
    for i, character in enumerate(characters):
        if i < top_x:
            top_characters.append(character)

    if len(top_characters) == 0:
        return ""
    else:
        leaderboard_lists = []
        leaderboard_lists.append(["Name"])
        leaderboard_lists.append(["Level"])
        leaderboard_lists.append(["Class"])
        leaderboard_lists.append(["GS"])
        leaderboard_lists.append(["XP"])
        leaderboard_lists.append(["Player"])
        for character in top_characters:
            leaderboard_lists[0].append(character.name)
            leaderboard_lists[1].append(str(character.level))
            leaderboard_lists[2].append(character.character_class.name)
            leaderboard_lists[3].append(str(character.gear.gearscore))
            leaderboard_lists[4].append(str(character.current_xp) + "/" + str(character.character_class.xp_per_level))
            player_name = [name["name"] for name in users_list if name["id"] == get_discord_id_by_character(character)]
            if player_name and player_name != "": leaderboard_lists[5].append(player_name[0])
            else: leaderboard_lists[5].append("Unknown")

        leaderboard = make_table(leaderboard_lists)
        
        return leaderboard