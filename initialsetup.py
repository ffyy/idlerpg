import os
import sqlite3
from dotenv import load_dotenv

def do():
    load_dotenv()

    DB_PATH = os.getenv("DB_PATH")
    try:
        db = sqlite3.connect(DB_PATH + "dev.db")
    except sqlite3.OperationalError:
        os.mkdir(DB_PATH)
    finally:
        db = sqlite3.connect(DB_PATH + "dev.db")

    cur = db.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS character(id, name, level, current_xp, gear_id)")
    cur.execute("CREATE TABLE IF NOT EXISTS gear(id, gearscore)")

    create_config()
    print("db & tables created")

def create_config():
    f = open(".conf", "w")
    f.write("firstrun=0")
    f.close()