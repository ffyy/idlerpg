import os
import sqlite3
from dotenv import load_dotenv

def do():
    load_dotenv()

    DB_PATH = os.getenv("DB_PATH")
    try:
        db = sqlite3.connect(str(DB_PATH))
    except sqlite3.OperationalError:
        os.makedirs(DB_PATH) #fix this!!
    finally:
        db = sqlite3.connect(str(DB_PATH))

    cur = db.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS character(id_ INTEGER NOT NULL PRIMARY KEY, name varchar(20) UNIQUE NOT NULL, level INTEGER NOT NULL, current_xp INTEGER NOT NULL, gear_id INTEGER)")
    cur.execute("CREATE TABLE IF NOT EXISTS gear(id_ INTEGER PRIMARY KEY, gearscore INTEGER NOT NULL)")    

    create_config()
    print("db & tables created")

def create_config():
    f = open(".conf", "w")
    f.write("firstrun=0")
    f.close()