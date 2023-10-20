import os
import sqlite3
import traceback
from rpgobjects import *
from dotenv import load_dotenv

load_dotenv()
DB_PATH = os.getenv("DB_PATH")

#DB FUNCTIONS

def update_db_character(character: CharacterDB):
    db = sqlite3.connect(DB_PATH)
    cur = db.cursor()
    cur.execute("UPDATE character SET name = ?, level = ?, current_xp = ?, class_id = ?, gear_id = ? WHERE id_ = ?", (character.name, character.level, character.current_xp, character.class_id, character.gear_id, character.id_))
    print("Updating old character")
    db.commit()
    cur.close()

def update_db_gear(gear: Gear):
    db = sqlite3.connect(DB_PATH)
    cur = db.cursor()
    cur.execute("UPDATE gear SET gearscore = ?", gear.gearscore)
    db.commit()
    cur.close

def register_character(name, class_id, player_id):
    character = CharacterDB(None, name, 0, 0, class_id, None)
    class_name = get_class(class_id).name
    
    db = sqlite3.connect(DB_PATH)
    cur = db.cursor()
    try:
        if character.class_id == 3: #hobbits get a magic ring
            cur.execute("INSERT INTO gear(gearscore) VALUES (20)")
        else: 
            cur.execute("INSERT INTO gear(gearscore) VALUES (0)")
        character.gear_id = cur.lastrowid
        cur.execute("INSERT INTO character(name,level,current_xp,class_id,gear_id) VALUES (?,?,?,?,?)", (character.name, character.level, character.current_xp, character.class_id, character.gear_id))
        character.id_ = cur.lastrowid
        cur.execute("INSERT INTO player(discord_id, character_id) VALUES (?,?)", (player_id, character.id_))
        db.commit()
        cur.close()
        return "Saved character called " + character.name + " with class " + class_name + " to database"
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
    character_class = CharacterClass(db_class[0], db_class[1], db_class[2], db_class[3], db_class[4])
    return character_class

def get_gear(id) -> Gear:
    db = sqlite3.connect(DB_PATH)
    cur = db.cursor()
    cur.execute("SELECT * FROM gear WHERE id_ = ?", (id,))
    db_gear = cur.fetchone()
    cur.close()
    if db_gear is not None: 
        gear = Gear(db_gear[0], db_gear[1])
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
    print(str(count))
    if count > 0 or len(name) > 12 or not name.isalpha():
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