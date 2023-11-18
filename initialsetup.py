import os
import sqlite3
import time
from dotenv import load_dotenv

def do():
    print("in 5 seconds, i will run initial setup again!\nto stop this from happening, add .conf to root dir")
    time.sleep(5)
    print("doing initial setup\n--------")

    load_dotenv()

    DB_PATH = os.getenv("DB_PATH")
    db = sqlite3.connect(str(DB_PATH))

    delete_all_tables(db)

    character_classes = [(1, "Thief", 1, 100, 0, 10000, 100, "Trust in your luck (1d100)"),
                         (2, "Fighter", 5, 20, 0, 10000, 100, "Solid in any situation (5d20)"),
                         (3, "Hobbit", 5, 10, 0, 6000, 100, "Bad at everything, but starts with a magic ring (5d10)"),
                         (4, "Elf", 5, 20, 20, 17000, 100, "Just better at everything, but levels slowly (5d20+20)"),
                         (5, "Magic User", 1, 100, 10, 10000, 80, "Powerful but squishy (1d100+10)"),
                         (6, "Cleric", 5, 20, 0, 10000, 90, "Can heal the party but is squishy (5d20)"),
                         (7, "Warlock", 5, 10, 60, 10000, 80, "Has a huge bonus which quickly runs out (5d10+60)")]

    print("creating new tables")
    cur = db.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS character(id_ INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL, level INTEGER NOT NULL, bonus INTEGER NOT NULL, current_xp INTEGER NOT NULL, current_hp INTEGER NOT NULL, class_id INTEGER NOT NULL, gear_id INTEGER)")
    cur.execute("CREATE TABLE IF NOT EXISTS deleted_character(id_ INTEGER NOT NULL PRIMARY KEY, name TEXT NOT NULL, level INTEGER NOT NULL, current_xp INTEGER NOT NULL, current_hp INTEGER NOT NULL, class_id INTEGER NOT NULL, gear_id INTEGER, player_id INTEGER, reason INTEGER)")
    cur.execute("CREATE TABLE IF NOT EXISTS class(id_ INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL, dice INTEGER NOT NULL, die_size INTEGER NOT NULL, bonus INTEGER NOT NULL, xp_per_level INTEGER NOT NULL, max_hp INTEGER NOT NULL, description TEXT NOT NULL)")
    cur.execute("CREATE TABLE IF NOT EXISTS gear(id_ INTEGER NOT NULL PRIMARY KEY, gearscore INTEGER NOT NULL, unattuned INTEGER NOT NULL)")
    cur.execute("CREATE TABLE IF NOT EXISTS player(id_ INTEGER NOT NULL PRIMARY KEY, discord_id TEXT UNIQUE NOT NULL, character_id INTEGER UNIQUE NOT NULL)")
    cur.execute("CREATE TABLE IF NOT EXISTS statistics(character_id INTEGER NOT NULL, quests_attempted INTEGER NOT NULL, quests_won INTEGER NOT NULL, ganks_attempted INTEGER NOT NULL, ganks_won INTEGER NOT NULL, defences_attempted INTEGER NOT NULL, defences_won INTEGER NOT NULL, pks INTEGER NOT NULL, personal_quests INTEGER NOT NULL, create_timestamp INTEGER NOT NULL, delete_timestamp INTEGER)")
    cur.executemany("INSERT INTO class VALUES (?, ?, ?, ?, ?, ?, ?, ?)", character_classes)
    db.commit()

    create_config()
    print("--------\ndb & .conf created")

def delete_all_tables(connection):
    print("dropping all tables")
    cur = connection.cursor()
    cur.execute("SELECT name FROM sqlite_schema WHERE type ='table'")
    tables = cur.fetchall()
    for table, in tables:
        print("dropping table " + table)
        sql = "DROP TABLE IF EXISTS " + table
        cur.execute(sql)
    cur.close()

def create_config():
    f = open(".conf", "w")
    f.write("firstrun=0")
    f.close()