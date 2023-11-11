import datetime
import os
import sqlite3
import traceback
import time
from rpgobjects import *
from helpers import *
from dotenv import load_dotenv

load_dotenv()
DB_PATH = os.getenv("DB_PATH")

#DB FUNCTIONS

def update_db_character(character: CharacterDB):
    db = sqlite3.connect(DB_PATH)
    cur = db.cursor()
    cur.execute("UPDATE character SET name = ?, level = ?, current_xp = ?, current_hp = ?, class_id = ?, gear_id = ? WHERE id_ = ?", (character.name, character.level, character.current_xp, character.current_hp, character.class_id, character.gear_id, character.id_))
    db.commit()
    cur.close()

def update_db_gear(gear: Gear):
    db = sqlite3.connect(DB_PATH)
    cur = db.cursor()
    cur.execute("UPDATE gear SET gearscore = ?, unattuned = ? WHERE id_ = ?", (gear.gearscore, gear.unattuned, gear.id_))
    db.commit()
    cur.close

def get_character_statistics(character: Character) -> CharacterStatistics:
    db = sqlite3.connect(DB_PATH)
    cur = db.cursor()
    cur.execute("SELECT * FROM statistics WHERE character_id = ?", (character.id_,))
    db_stats = cur.fetchone()
    cur.close()
    stats = CharacterStatistics(db_stats[0], db_stats[1], db_stats[2], db_stats[3], db_stats[4], db_stats[5], db_stats[6], db_stats[7], db_stats[8], db_stats[9], db_stats[10])
    return stats

def get_character_statistics_by_id(id_) -> CharacterStatistics:
    db = sqlite3.connect(DB_PATH)
    cur = db.cursor()
    cur.execute("SELECT * FROM statistics WHERE character_id = ?", (id_,))
    db_stats = cur.fetchone()
    cur.close()
    stats = CharacterStatistics(db_stats[0], db_stats[1], db_stats[2], db_stats[3], db_stats[4], db_stats[5], db_stats[6], db_stats[7], db_stats[8], db_stats[9], db_stats[10])
    return stats

def update_character_statistics(stats: CharacterStatistics):
    db = sqlite3.connect(DB_PATH)
    cur = db.cursor()
    cur.execute("UPDATE statistics SET quests_attempted = ?, quests_won = ?, ganks_attempted = ?, ganks_won = ?, defences_attempted = ?, defences_won = ?, pks = ?, personal_quests = ? WHERE character_id = ?", (stats.quests_attempted, stats.quests_won, stats.ganks_attempted, stats.ganks_won, stats.defences_attempted, stats.defences_won, stats.pks, stats.personal_quests, stats.character_id))
    db.commit()
    cur.close

def register_character(name, class_id, player_id):
    character = CharacterDB(None, name, 0, 0, 0, class_id, None)
    character_class = get_class(class_id)
    class_name = character_class.name

    db = sqlite3.connect(DB_PATH)
    cur = db.cursor()
    try:
        if character.class_id == 3: #hobbits get a magic ring
            cur.execute("INSERT INTO gear(gearscore,unattuned) VALUES (20,0)")
        else:
            cur.execute("INSERT INTO gear(gearscore,unattuned) VALUES (0,0)")
        character.gear_id = cur.lastrowid
        cur.execute("INSERT INTO character(name,level,current_xp,current_hp,class_id,gear_id) VALUES (?,?,?,?,?,?)", (character.name, character.level, character.current_xp, character_class.max_hp, character.class_id, character.gear_id))
        character.id_ = cur.lastrowid
        cur.execute("INSERT INTO player(discord_id, character_id) VALUES (?,?)", (player_id, character.id_))
        cur.execute("INSERT INTO statistics(character_id, quests_attempted, quests_won, ganks_attempted, ganks_won, defences_attempted, defences_won, pks, personal_quests, create_timestamp) VALUES (?,?,?,?,?,?,?,?,?,?)", (character.id_, 0, 0, 0, 0, 0, 0, 0, 0, int(time.time())))
        db.commit()
        cur.close()
        return "A hero called " + character.name + " showed up! " + character.name + " is a " + class_name + "."
    except:
        traceback.print_exc()
        return "Something went wrong"

def delete_character_by_id(player_id):
    db = sqlite3.connect(DB_PATH)
    cur = db.cursor()
    character = get_character_by_player_id(player_id)
    cur.execute("UPDATE statistics SET delete_timestamp = ? WHERE character_id = ?", (int(time.time()), character.id_))
    cur.execute("INSERT INTO deleted_character(id_,name,level,current_xp,current_hp,class_id,gear_id,player_id) VALUES (?,?,?,?,?,?,?,?)", (character.id_, character.name, character.level, character.current_xp, "0", character.character_class.id_, character.gear.id_, player_id))
    cur.execute("DELETE FROM character WHERE id_ = ?",(character.id_,))
    cur.execute("DELETE FROM player WHERE discord_id = ?", (player_id,))
    db.commit()
    cur.close()
    response = "Deleted character " + character.name
    return response

def delete_character(character: Character):
    db = sqlite3.connect(DB_PATH)
    cur = db.cursor()
    player_id = get_discord_id_by_character(character)
    cur.execute("UPDATE statistics SET delete_timestamp = ? WHERE character_id = ?", (int(time.time()), character.id_))
    cur.execute("INSERT INTO deleted_character(id_,name,level,current_xp,current_hp,class_id,gear_id,player_id) VALUES (?,?,?,?,?,?,?,?)", (character.id_, character.name, character.level, character.current_xp, "0", character.character_class.id_, character.gear.id_, player_id))
    cur.execute("DELETE FROM character WHERE id_ = ?",(character.id_,))
    cur.execute("DELETE FROM player WHERE discord_id = ?", (player_id,))
    db.commit()
    cur.close()

def reincarnate(character: Character):
    player_id = get_discord_id_by_character(character)
    delete_character(character)
    register_character(character.name, character.character_class.id_, player_id)

def register_player(player_id, character_id):
    db = sqlite3.connect(DB_PATH)
    cur = db.cursor()
    cur.execute("INSERT INTO player(discord_id,character_id)",(player_id, character_id))
    db.commit()
    cur.close()

def get_character_by_name(name) -> Character:
    db = sqlite3.connect(DB_PATH)
    cur = db.cursor()
    cur.execute("SELECT * FROM character WHERE lower(name) = ?", (name.lower(),))
    db_character = cur.fetchone()
    cur.close()
    if db_character is None:
        return None
    else:
        data_character = CharacterDB(db_character[0], db_character[1], db_character[2], db_character[3], db_character[4], db_character[5], db_character[6])
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
        data_character = CharacterDB(db_character[0], db_character[1], db_character[2], db_character[3], db_character[4], db_character[5], db_character[6])
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
        data_character = CharacterDB(db_character[0], db_character[1], db_character[2], db_character[3], db_character[4], db_character[5], db_character[6])
        character = db_character_to_character(data_character)
        return character
    else:
        return None

def get_character_ids() -> tuple:
    db = sqlite3.connect(DB_PATH)
    cur = db.cursor()
    cur.execute("SELECT id_ FROM character")
    characters = cur.fetchall()
    return characters

def get_all_characters() -> list[Character]:
    characters = []
    for id_ in get_character_ids():
        characters.append(get_character_by_id(id_[0]))
    return characters

def get_all_dead_characters() -> list[DeadCharacter]:
    dead_characters = []
    db = sqlite3.connect(DB_PATH)
    cur = db.cursor()
    cur.execute("SELECT * FROM deleted_character")
    db_results = cur.fetchall()
    for db_character in db_results:
        gearscore = get_gear(db_character[6]).gearscore
        stats = get_character_statistics_by_id(db_character[0])
        time_alive = stats.delete_timestamp - stats.create_timestamp
        dead_characters.append(DeadCharacter(db_character[0], db_character[1], db_character[2], db_character[5], gearscore, db_character[7], time_alive))

    dead_characters.sort(key=lambda dead_character: -dead_character.life_length)

    return dead_characters

def get_class(id) -> CharacterClass:
    db = sqlite3.connect(DB_PATH)
    cur = db.cursor()
    cur.execute("SELECT * FROM class WHERE id_ = ?", (id,))
    db_class = cur.fetchone()
    cur.close()
    character_class = CharacterClass(db_class[0], db_class[1], db_class[2], db_class[3], db_class[4], db_class[5], db_class[6], db_class[7])
    return character_class

def get_character_count() -> int:
    db = sqlite3.connect(DB_PATH)
    cur = db.cursor()
    cur.execute("SELECT count(id_) FROM character")
    count = cur.fetchone()
    return int(count[0])

def get_all_classes() -> list[CharacterClass]:
    classes = []
    db = sqlite3.connect(DB_PATH)
    cur = db.cursor()
    cur.execute("SELECT * FROM class")
    db_classes = cur.fetchall()
    for db_class in db_classes:
        classes.append(CharacterClass(db_class[0], db_class[1], db_class[2], db_class[3], db_class[4], db_class[5], db_class[6], db_class[7]))
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
    db_character = CharacterDB(character.id_, character.name, character.level, character.current_xp, character.current_hp, character.character_class.id_, character.gear.id_)
    return db_character

def db_character_to_character(character: CharacterDB) -> Character:
    game_class = get_class(character.class_id)
    game_gear = get_gear(character.gear_id)
    game_character = Character(character.id_, character.name, character.level, character.current_xp, character.current_hp, game_class, game_gear)
    return game_character

def is_name_valid(name) -> bool:
    db = sqlite3.connect(DB_PATH)
    cur = db.cursor()
    cur.execute("SELECT count(1) FROM character WHERE lower(name) = ?", (name.lower(),))
    count = int(cur.fetchone()[0])
    #sqlite doesn't support lower/upper for non-ascii characters, so we don't allow names with uppercase non-ascii characters to make sure case insensitive search works
    if count > 0 or len(name) > 12 or not name.isalpha() or [c for c in name if c.isupper() and not c.isascii()]:
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

def get_leaderboard(top_x, users_list, class_filter) -> str:
    characters = get_all_characters()
    if class_filter:
        characters = [character for character in characters if character.character_class.id_ == class_filter]

    top_characters = []
    characters.sort(key=lambda character: (-character.level, -character.gear.gearscore, -character.current_xp))
    for i, character in enumerate(characters):
        if i < top_x:
            top_characters.append(character)

    if len(top_characters) == 0:
        return ""
    else:
        leaderboard_lists = []
        leaderboard_lists.append(["Name"])
        leaderboard_lists.append(["L"])
        leaderboard_lists.append(["Class"])
        leaderboard_lists.append(["GS"])
        leaderboard_lists.append(["XP"])
        leaderboard_lists.append(["Age (h)"])
        leaderboard_lists.append(["Player"])
        for character in top_characters:
            character_statistics = get_character_statistics(character)
            time_alive = (int(time.time()) - character_statistics.create_timestamp)/60/60
            leaderboard_lists[0].append(character.name)
            leaderboard_lists[1].append(str(character.level))
            leaderboard_lists[2].append(character.character_class.name)
            leaderboard_lists[3].append(str(character.gear.gearscore))
            leaderboard_lists[4].append(str(character.current_xp) + "/" + str(character.character_class.xp_per_level))
            leaderboard_lists[5].append("%.2f" % time_alive + "h")
            player_name = [name["name"] for name in users_list if name["id"] == int(get_discord_id_by_character(character))]
            if player_name and player_name != "": leaderboard_lists[6].append(player_name[0])
            else: leaderboard_lists[6].append("Unknown")

        leaderboard = make_table(leaderboard_lists)

        return leaderboard

def get_graveyard(name, users_list, class_filter) -> str:
    dead_characters = get_all_dead_characters()
    top_characters = []

    if name:
        dead_characters = [character for character in dead_characters if character.name.lower() == name.lower()]

    if class_filter:
        dead_characters = [character for character in dead_characters if character.class_id == class_filter]

    for i, character in enumerate(dead_characters):
        if i < 10:
            top_characters.append(character)

    if len(top_characters) == 0:
        return ""
    else:
        leaderboard_lists = []
        leaderboard_lists.append(["Name"])
        leaderboard_lists.append(["L"])
        leaderboard_lists.append(["Class"])
        leaderboard_lists.append(["GS"])
        leaderboard_lists.append(["Quests"])
        leaderboard_lists.append(["PvP"])
        leaderboard_lists.append(["Kills"])
        leaderboard_lists.append(["Time alive"])
        leaderboard_lists.append(["Player"])
        for character in top_characters:
            stats = get_character_statistics_by_id(character.id_)
            time_alive = int(character.life_length)/3600
            leaderboard_lists[0].append(character.name)
            leaderboard_lists[1].append(str(character.level))
            leaderboard_lists[2].append(get_class(character.class_id).name)
            leaderboard_lists[3].append(str(character.gearscore))
            leaderboard_lists[4].append(str(stats.quests_won) + "/" + str(stats.quests_attempted))
            leaderboard_lists[5].append(str(stats.ganks_won+stats.defences_won) + "/" + str(stats.ganks_attempted+stats.defences_attempted))
            leaderboard_lists[6].append(str(stats.pks))
            leaderboard_lists[7].append("%.2f" % time_alive + "h")
            player_name = [name["name"] for name in users_list if name["id"] == character.player_id]
            if player_name and player_name != "": leaderboard_lists[8].append(player_name[0])
            else: leaderboard_lists[8].append("Unknown")

    graveyard = make_table(leaderboard_lists)

    return graveyard

def character_search(name, users_list) -> str:
    if name:
        character = get_character_by_name(name)
    else:
        player_id = int(users_list[0]["id"])
        character = get_character_by_player_id(player_id)

    if character is None:
        return "Character not found"

    hp_bar = make_hp_bar(character.current_hp, character.character_class.max_hp)

    results_lists = []
    results_lists.append(["Name"])
    results_lists.append(["L"])
    results_lists.append(["Class"])
    results_lists.append(["GS"])
    results_lists.append(["XP"])
    results_lists.append(["HP"])
    results_lists.append(["Player"])
    results_lists[0].append(character.name)
    results_lists[1].append(str(character.level))
    results_lists[2].append(character.character_class.name)
    results_lists[3].append(str(character.gear.gearscore))
    results_lists[4].append(str(character.current_xp) + "/" + str(character.character_class.xp_per_level))
    results_lists[5].append(hp_bar)
    player_name = [name["name"] for name in users_list if name["id"] == int(get_discord_id_by_character(character))]
    if player_name and player_name != "": results_lists[6].append(player_name[0])
    else: results_lists[6].append("Unknown")

    find_results = make_table(results_lists)

    stats = get_character_statistics(character)

    statistics_lists = []
    statistics_lists.append(["Quests"])
    statistics_lists.append(["Ganks"])
    statistics_lists.append(["Defences"])
    statistics_lists.append(["Kills"])
    statistics_lists.append(["PQ"])
    statistics_lists.append(["Created"])
    statistics_lists[0].append(str(stats.quests_won) + "/" + str(stats.quests_attempted))
    statistics_lists[1].append(str(stats.ganks_won) + "/" + str(stats.ganks_attempted))
    statistics_lists[2].append(str(stats.defences_won) + "/" + str(stats.defences_attempted))
    statistics_lists[3].append(str(stats.pks))
    statistics_lists[4].append(str(stats.personal_quests))
    statistics_lists[5].append(str(datetime.datetime.fromtimestamp(stats.create_timestamp)))

    stats_results = make_table(statistics_lists)

    results = find_results + stats_results

    return results