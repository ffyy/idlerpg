import os
import sqlite3
from dotenv import load_dotenv

def do():
    load_dotenv()

    DB_PATH = os.getenv("DB_PATH")
    db = sqlite3.connect(str(DB_PATH))

    character_classes = [(1, "Rogue", "Random"),
                         (2, "Fighter", "Stable")]
    cur = db.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS character(id_ INTEGER NOT NULL PRIMARY KEY, name varchar(20) UNIQUE NOT NULL, level INTEGER NOT NULL, current_xp INTEGER NOT NULL, class_id INTEGER NOT NULL, gear_id INTEGER)")
    cur.execute("CREATE TABLE IF NOT EXISTS classes(id_ INTEGER PRIMARY KEY, name varchar(20) UNIQUE NOT NULL, tactic varchar(20) NOT NULL)")    
    cur.execute("CREATE TABLE IF NOT EXISTS gear(id_ INTEGER PRIMARY KEY, gearscore INTEGER NOT NULL)")
    #cur.executemany("INSERT INTO classes VALUES (?, ?, ?)", character_classes)
    #db.commit()

    create_config()
    print("db & tables created")

def create_config():
    f = open(".conf", "w")
    f.write("firstrun=0")
    f.close()