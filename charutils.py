import os
import sqlite3
import traceback
from rpgobjects import *
from dotenv import load_dotenv

load_dotenv()
DB_PATH = os.getenv("DB_PATH")

def save_to_db(character: CharacterDB):
    db = sqlite3.connect(DB_PATH)
    cur = db.cursor()
    if (character.id_ is None):
        cur.execute("INSERT INTO character(name,level,current_xp,class_id,gear_id) VALUES (?,?,?,?,?)", (character.name, character.level, character.current_xp, character.class_id, character.gear_id))
        print("Creating new character")
        db.commit()
    else:
        cur.execute("UPDATE character SET name = ?, level = ?, current_xp = ?, class_id = ?, gear_id = ? WHERE id_ = ?", (character.name, character.level, character.current_xp, character.class_id, character.gear_id, character.id_))
        print("Updating old character")
        db.commit()

def get_from_db(name):
    db = sqlite3.connect(DB_PATH)
    cur = db.cursor()
    cur.execute("SELECT * FROM character WHERE name = ?", (name,))
    db_character = cur.fetchone()
    character = CharacterDB(db_character[0], db_character[1], db_character[2], db_character[3], db_character[4], db_character[5])
    return character

def create_character(name, class_id):
    new_character = CharacterDB(None, name, 0, 0, class_id, None)
    #class_name = get_db_class(class_id).name
    try:
        save_to_db(new_character)
        return "Saved character called " + new_character.name + " with class id " + str(new_character.class_id) + " to database"
    except:
        traceback.print_exc()
        return "Something went wrong" 

def level_up(name):
    character = get_from_db(name)
    character.level += 1
    save_to_db(character)
    return "Character " + character.name + " is now level " + str(character.level)