import os
import sqlite3
import traceback
from rpgobjects import *
from dotenv import load_dotenv

load_dotenv()
DB_PATH = os.getenv("DB_PATH")

def update_db_character(character: CharacterDB):
    db = sqlite3.connect(DB_PATH)
    cur = db.cursor()
    cur.execute("UPDATE character SET name = ?, level = ?, current_xp = ?, class_id = ?, gear_id = ? WHERE id_ = ?", (character.name, character.level, character.current_xp, character.class_id, character.gear_id, character.id_))
    print("Updating old character")
    db.commit()
    cur.close()

def register_character(name, class_id, player_id):
    character = CharacterDB(None, name, 0, 0, class_id, None)
    class_name = get_db_class(class_id).name
    
    db = sqlite3.connect(DB_PATH)
    cur = db.cursor()
    try:
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
    cur.execute("DELETE FROM character WHERE player_id = ?",(player_id))
    db.commit()
    cur.close()

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

def get_db_character_by_name(name):
    db = sqlite3.connect(DB_PATH)
    cur = db.cursor()
    cur.execute("SELECT * FROM character WHERE name = ?", (name,))
    db_character = cur.fetchone()
    cur.close()
    character = CharacterDB(db_character[0], db_character[1], db_character[2], db_character[3], db_character[4], db_character[5])
    return character

def get_db_class(id):
    db = sqlite3.connect(DB_PATH)
    cur = db.cursor()
    cur.execute("SELECT * FROM class WHERE id_ = ?", (id,))
    db_class = cur.fetchone()
    cur.close()
    character_class = CharacterClass(db_class[0], db_class[1], db_class[2])
    return character_class

def character_to_db_object(character: Character):
    db_character = CharacterDB(character.id_, character.name, character.level, character.current_xp, character.character_class.id, character.gear.id_)
    return db_character

def character_to_db_object(character: CharacterDB):
    #game_class =
    #game_gear =
    game_character = Character(character.id_, character.name, character.level, character.current_xp)
    return game_character

def level_up(name):
    character = get_db_character_by_name(name)
    character.level += 1
    update_db_character(character)
    return "Character " + character.name + " is now level " + str(character.level)