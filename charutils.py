import json
import os
import shutil
import sqlite3
from datetime import datetime
from dotenv import load_dotenv

DB_PATH = os.getenv("DB_PATH")

class Character:
    def __init__(
            self, 
            id_,
            name,
            level,
            current_xp,
            gear_id
            ):
        self.id_ = id_
        self.name = name
        self.level = level
        self.current_xp = current_xp
        self.gear_id = gear_id

class Gear:
    def __init__(
            self,
            id_,
            gearscore
            ):
        self.id_ = id_
        self.gearscore = gearscore

def save_to_db(character: Character):
    db = sqlite3.connect(DB_PATH)
    cur = db.cursor()
    if (character.id_ is None):
        cur.execute("INSERT INTO character(name,level,current_xp,gear_id) VALUES (?,?,?,?)", (character.name, character.level, character.current_xp, character.gear_id))
        print("Creating new character")
        db.commit()
    else:
        cur.execute("UPDATE character SET name = ?, level = ?, current_xp = ?, gear_id = ? WHERE id_ = ?", (character.name, character.level, character.current_xp, character.gear_id, character.id_))
        print("Updating old character")
        db.commit()

def get_from_db(name):
    db = sqlite3.connect(DB_PATH)
    cur = db.cursor()
    cur.execute("SELECT * FROM character WHERE name = ?", (name,))
    db_character = cur.fetchone()
    character = Character(db_character[0], db_character[1], db_character[2], db_character[3], db_character[4])
    return character

def create_character(name):
    new_character = Character(None, name, 0, 0, None)
    try:
        save_to_db(new_character)
        return "Saved character called " + new_character.name + " to database"
    except:
        return "Something went wrong" 

def level_up(name):
    character = get_from_db(name)
    character.level += 1
    save_to_db(character)
    return "Character " + character.name + " is now level " + str(character.level)