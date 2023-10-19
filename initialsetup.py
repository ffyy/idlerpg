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

    character_classes = [(1, "Rogue", "Random"),
                         (2, "Fighter", "Stable")]
    cur = db.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS character(id_ INTEGER NOT NULL PRIMARY KEY, name VARCHAR(20) UNIQUE NOT NULL, level INTEGER NOT NULL, current_xp INTEGER NOT NULL, class_id INTEGER NOT NULL, gear_id INTEGER)")
    cur.execute("CREATE TABLE IF NOT EXISTS class(id_ INTEGER PRIMARY KEY, name VARCHAR(20) UNIQUE NOT NULL, tactic varchar(20) NOT NULL)")    
    cur.execute("CREATE TABLE IF NOT EXISTS gear(id_ INTEGER NOT NULL PRIMARY KEY, gearscore INTEGER NOT NULL)")
    cur.execute("CREATE TABLE IF NOT EXISTS player(id_ INTEGER NOT NULL PRIMARY KEY, discord_id VARCHAR(100) UNIQUE NOT NULL, character_id INTEGER UNIQUE NOT NULL)")
    cur.executemany("INSERT INTO class VALUES (?, ?, ?)", character_classes)
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
    print("creating new tables")
    cur.close()

def create_config():
    f = open(".conf", "w")
    f.write("firstrun=0")
    f.close()