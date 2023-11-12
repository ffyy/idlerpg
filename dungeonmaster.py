import random
import charutils
from rpgobjects import *
from helpers import *

QUEST_HOOKS = open("content/quests.txt").read().splitlines()
PERSONAL_QUESTS = open("content/personalquests.txt").read().splitlines()
SUCCESS_DESCRIPTIONS = open("content/successes.txt").read().splitlines()
FAILURE_DESCRIPTIONS = open("content/failures.txt").read().splitlines()
PVP_OUTCOMES = open("content/pvpoutcomes.txt").read().splitlines()
ITEMS = open("content/items.txt").read().splitlines()
DEFAULT_EVENTS_LIST = [0, 1, 2]

class DungeonMaster:
    def __init__(
            self):
        self.events_list = []
        self.initialize_list()

    def choose_event(self):
        if not self.events_list:
            self.initialize_list()
            return self.run_long_rest()

        chosen_event = random.choice(self.events_list)
        self.events_list.remove(chosen_event)

        match chosen_event:
            case 0:
                return self.run_personal_quest()
            case 1:
                return self.run_adventure()
            case 2:
                return self.run_pvp_encounter()
            case _:
                return "Something super fucky happened"

    def initialize_list(self):
        for value in DEFAULT_EVENTS_LIST:
            self.events_list.append(value)

    def give_quest_rewards(self, quest: Quest):
        if "experience" in quest.quest_type:
            for adventurer in quest.party:
                adventurer.current_xp += int(10000*(quest.quest_difficulty/(100*len(quest.party))))
                charutils.update_db_character(charutils.character_to_db_character(adventurer))
        if "loot" in quest.quest_type:
            carry_index = quest.party_rolls.index(max(quest.party_rolls))
            quest.party[carry_index].gear.unattuned += 1
            charutils.update_db_gear(quest.party[carry_index].gear)

    def run_quest(self, dm_quest: Quest) -> Quest:
        QUEST_ITEM_THRESHOLD = 0.8

        completed_quest = dm_quest
        for adventurer in dm_quest.party:
            adventurer_roll = adventurer.roll_dice() + adventurer.gear.gearscore
            completed_quest.party_rolls.append(adventurer_roll)

        party_max_roll = 100*len(dm_quest.party)
        if (random.randint(1,100) <= 100*(sum(completed_quest.party_rolls) - dm_quest.quest_difficulty)/dm_quest.quest_difficulty) or (party_max_roll * QUEST_ITEM_THRESHOLD <= sum(completed_quest.party_rolls)):
            completed_quest.quest_type.append("loot")

        if sum(completed_quest.party_rolls) > dm_quest.quest_difficulty:
            for character in completed_quest.party:
                character_statistics = charutils.get_character_statistics(character)
                character_statistics.quests_attempted += 1
                character_statistics.quests_won += 1
                charutils.update_character_statistics(character_statistics)
            completed_quest.outcome = 1
            completed_quest.quest_journal = ' '.join([completed_quest.quest_journal, "Luckily,"])
            completed_quest.quest_journal = ' '.join([completed_quest.quest_journal, random.choice(SUCCESS_DESCRIPTIONS)])
            healer = next((hero for hero in completed_quest.party if hero.character_class.id_ == 6), None)
            if healer:
                hp_gain = random.randint(3,24) + 4
                for character in completed_quest.party:
                    character.current_hp = min(character.current_hp + hp_gain, character.character_class.max_hp)
                    charutils.update_db_character(charutils.character_to_db_character(character))
                completed_quest.quest_journal = ' '.join([completed_quest.quest_journal, "Thanks to"])
                completed_quest.quest_journal = ' '.join([completed_quest.quest_journal, healer.name])
                completed_quest.quest_journal = ', '.join([completed_quest.quest_journal, "everyone was healed for"])
                completed_quest.quest_journal = ' '.join([completed_quest.quest_journal, str(hp_gain)])
                completed_quest.quest_journal = ' '.join([completed_quest.quest_journal, "HP."])
            if "loot" in dm_quest.quest_type:
                carry_index = completed_quest.party_rolls.index(max(completed_quest.party_rolls))
                item_name = random.choice(ITEMS)
                completed_quest.quest_journal = ' '.join([completed_quest.quest_journal, completed_quest.party[carry_index].name])
                completed_quest.quest_journal = ' '.join([completed_quest.quest_journal, "also found"])
                if item_name[0] in "aeoiu":
                    completed_quest.quest_journal = ' '.join([completed_quest.quest_journal, "an"])
                else:
                    completed_quest.quest_journal = ' '.join([completed_quest.quest_journal, "a"])
                completed_quest.quest_journal = ' '.join([completed_quest.quest_journal, item_name])
                completed_quest.quest_journal = ''.join([completed_quest.quest_journal, "!"])
            if "experience" in dm_quest.quest_type:
                completed_quest.quest_journal = '\n'.join([completed_quest.quest_journal, "XP reward:"])
                completed_quest.quest_journal = ' '.join([completed_quest.quest_journal, str(int(10000*(completed_quest.quest_difficulty/party_max_roll)))])
            completed_quest.quest_journal = '\n'.join([completed_quest.quest_journal, str(sum(completed_quest.party_rolls))])
            completed_quest.quest_journal = '/'.join([completed_quest.quest_journal, str(dm_quest.quest_difficulty)])
            completed_quest.quest_journal = ' - '.join([completed_quest.quest_journal, "**Success!**"])
            self.give_quest_rewards(completed_quest)
        else:
            hp_loss = int(100 - (sum(completed_quest.party_rolls) / dm_quest.quest_difficulty) * 100)
            completed_quest.outcome = 0
            completed_quest.quest_journal = ' '.join([completed_quest.quest_journal, "Unfortunately,"])
            completed_quest.quest_journal = ' '.join([completed_quest.quest_journal, random.choice(FAILURE_DESCRIPTIONS)])
            completed_quest.quest_journal = ' '.join([completed_quest.quest_journal, "Everyone involved lost"])
            completed_quest.quest_journal = ' '.join([completed_quest.quest_journal, str(hp_loss)])
            completed_quest.quest_journal = ' '.join([completed_quest.quest_journal, "HP."])
            for character in completed_quest.party:
                character_statistics = charutils.get_character_statistics(character)
                character_statistics.quests_attempted += 1
                charutils.update_character_statistics(character_statistics)
                character.current_hp -= hp_loss
                if character.current_hp > 0:
                    charutils.update_db_character(charutils.character_to_db_character(character))
                elif character.current_hp <= 0:
                    character.current_hp = 0
                    completed_quest.death_notices.append(charutils.get_discord_id_by_character(character))
                    charutils.reincarnate(character)
                    completed_quest.quest_journal = ' '.join([completed_quest.quest_journal, character.name])
                    completed_quest.quest_journal = ' '.join([completed_quest.quest_journal, "died and was reincarnated at level 0!"])
            completed_quest.quest_journal = '\n'.join([completed_quest.quest_journal, str(sum(completed_quest.party_rolls))])
            completed_quest.quest_journal = '/'.join([completed_quest.quest_journal, str(dm_quest.quest_difficulty)])
            completed_quest.quest_journal = ' - '.join([completed_quest.quest_journal, "**Failure!**"])

        return completed_quest

    def run_adventure(self) -> str:
        character_ids = charutils.get_character_ids()

        QUEST_TYPES = ["experience", "loot"]
        quest_type = ["experience"]

        quest_hook = ' '.join(["The heroes were given an epic quest. They had to", random.choice(QUEST_HOOKS)])

        quest = Quest(quest_type, [], [], [], 0, quest_hook, 0)

        if not character_ids:
            return "I tried to run an adventure, but nobody showed up. 😢"

        if(len(character_ids)) == 1:
            quest.party.append(charutils.get_character_by_id(character_ids[0][0]))
        else:
            party_size = random.randint(2,(max(2, (len(character_ids)//2))))
            for character_id in random.sample(character_ids, party_size):
                quest.party.append(charutils.get_character_by_id(character_id[0]))

        difficulty = random.randint(20,100)*len(quest.party)
        quest.quest_difficulty = difficulty

        completed_quest = self.run_quest(quest)

        completed_quest_lists = []
        completed_quest_lists.append(["Hero"])
        completed_quest_lists.append(["Class"])
        completed_quest_lists.append(["Level"])
        completed_quest_lists.append(["GS"])
        completed_quest_lists.append(["HP"])
        completed_quest_lists.append(["Roll"])

        for i,hero in enumerate(completed_quest.party):
            completed_quest_lists[0].append(hero.name)
            completed_quest_lists[1].append(hero.character_class.name)
            completed_quest_lists[2].append(str(hero.level))
            completed_quest_lists[3].append(str(hero.gear.gearscore))
            completed_quest_lists[4].append(make_hp_bar(hero.current_hp, hero.character_class.max_hp))
            completed_quest_lists[5].append(str(completed_quest.party_rolls[i]))

        quest_table = make_table(completed_quest_lists)

        completed_quest.quest_journal = "".join([completed_quest.quest_journal, quest_table])

        return [completed_quest.quest_journal, completed_quest.death_notices]

    def run_pvp_encounter(self) -> str:
        all_characters = charutils.get_all_characters()
        #if there are too few characters, DM should actually run a personal quest instead of the volatile pvp
        if len(all_characters) < 6:
            return ["I tried to incite violence, but there weren't enough characters around for PvP.",""]

        all_characters.sort(key=lambda character:character.level)
        i_ganker = randint(0, len(all_characters)//2)
        pvp_characters = []
        pvp_characters.append(all_characters[i_ganker])
        del all_characters[0:i_ganker+1]
        pvp_characters.append(random.choice(all_characters))

        ganker_statistics = charutils.get_character_statistics(pvp_characters[0])
        defender_statistics = charutils.get_character_statistics(pvp_characters[1])
        ganker_statistics.ganks_attempted += 1
        defender_statistics.defences_attempted += 1
        charutils.update_character_statistics(ganker_statistics)
        charutils.update_character_statistics(defender_statistics)

        pvp_rolls = []
        for character in pvp_characters:
            character_roll = character.roll_dice() + character.gear.gearscore
            pvp_rolls.append(character_roll)
        pvp_journal = [pvp_characters[0].name + " waited for the right moment and attacked " + pvp_characters[1].name + ".", []]
        xp_reward = min((max(1, pvp_characters[1].level - pvp_characters[0].level) * 1000), 10000)
        hp_loss = abs(pvp_rolls[0] - pvp_rolls[1])
        if pvp_rolls[0] >= pvp_rolls[1]:
            ganker_statistics.ganks_won += 1
            #fill outcome flavor text in journal
            pvp_journal[0] = " ".join([pvp_journal[0], "This time,"])
            pvp_journal[0] = " ".join([pvp_journal[0], pvp_characters[0].name])
            pvp_journal[0] = "".join([pvp_journal[0], random.choice([line for line in PVP_OUTCOMES if line[0] == "1"])[2:]])
            #start handling loser hp loss
            pvp_characters[1].current_hp -= hp_loss
            pvp_journal[0] = ". ".join([pvp_journal[0], pvp_characters[1].name])
            pvp_journal[0] = " ".join([pvp_journal[0], "lost"])
            pvp_journal[0] = " ".join([pvp_journal[0], str(hp_loss)])
            pvp_journal[0] = " ".join([pvp_journal[0], "HP."])
            #start handling loser death
            if pvp_characters[1].current_hp > 0:
                charutils.update_db_character(charutils.character_to_db_character(pvp_characters[1]))
            elif pvp_characters[1].current_hp <= 0:
                pvp_characters[1].current_hp = 0
                ganker_statistics.pks += 1
                pvp_journal[1].append(charutils.get_discord_id_by_character(pvp_characters[1]))
                charutils.reincarnate(pvp_characters[1])
                pvp_journal[0] = " ".join([pvp_journal[0], pvp_characters[1].name])
                pvp_journal[0] = " ".join([pvp_journal[0], "died and was reincarnated at level 0!"])
                #start handling loot
                pvp_journal[0] = " ".join([pvp_journal[0], pvp_characters[0].name])
                pvp_journal[0] = " ".join([pvp_journal[0], "looted a few magic items."])
                items_found = randint(1, max(pvp_characters[1].gear.gearscore, 1))
                pvp_characters[0].gear.unattuned += items_found
                charutils.update_db_gear(pvp_characters[0].gear)
                discord_id = charutils.get_discord_id_by_character(pvp_characters[1])
            #fill outcome statistics in journal
            pvp_journal[0] = "\n".join([pvp_journal[0], "XP reward for"])
            pvp_journal[0] = " ".join([pvp_journal[0], pvp_characters[0].name])
            pvp_journal[0] = ": ".join([pvp_journal[0], str(xp_reward)])
            pvp_characters[0].current_xp += xp_reward
            pvp_journal[0] = "\n".join([pvp_journal[0], str(pvp_rolls[0])])
            pvp_journal[0] = "/".join([pvp_journal[0], str(pvp_rolls[1])])
            pvp_journal[0] = " - ".join([pvp_journal[0], "**Success!**"])
            #handle xp gain for ganker
            charutils.update_character_statistics(ganker_statistics)
            charutils.update_db_character(charutils.character_to_db_character(pvp_characters[0]))
        elif pvp_rolls[0] < pvp_rolls[1]:
            defender_statistics.defences_won += 1
            #fill outcome flavor text in journal
            pvp_journal[0] = " ".join([pvp_journal[0], "Unfortunately,"])
            pvp_journal[0] = " ".join([pvp_journal[0], pvp_characters[0].name])
            pvp_journal[0] = "".join([pvp_journal[0], random.choice([line for line in PVP_OUTCOMES if line[0] == "0"])[2:]])
            #start handling loser hp loss
            pvp_characters[0].current_hp -= hp_loss
            pvp_journal[0] = ". ".join([pvp_journal[0], pvp_characters[0].name])
            pvp_journal[0] = " ".join([pvp_journal[0], "lost"])
            pvp_journal[0] = " ".join([pvp_journal[0], str(hp_loss)])
            pvp_journal[0] = " ".join([pvp_journal[0], "HP."])
            #start handling loser death
            if pvp_characters[0].current_hp > 0:
                charutils.update_db_character(charutils.character_to_db_character(pvp_characters[0]))
            elif pvp_characters[0].current_hp <= 0:
                pvp_journal[1].append(charutils.get_discord_id_by_character(pvp_characters[0]))
                pvp_characters[0].current_hp = 0
                defender_statistics.pks += 1
                charutils.reincarnate(pvp_characters[0])
                pvp_journal[0] = " ".join([pvp_journal[0], pvp_characters[0].name])
                pvp_journal[0] = " ".join([pvp_journal[0], "died and was reincarnated at level 0!"])
                #start handling loot
                pvp_journal[0] = " ".join([pvp_journal[0], pvp_characters[1].name])
                pvp_journal[0] = " ".join([pvp_journal[0], "looted a few magic items."])
                items_found = randint(1, max(pvp_characters[0].gear.gearscore, 1))
                pvp_characters[1].gear.unattuned += items_found
                charutils.update_db_gear(pvp_characters[1].gear)
            #fill outcome statistics in journal
            pvp_journal[0] = "\n".join([pvp_journal[0], str(pvp_rolls[0])])
            pvp_journal[0] = "/".join([pvp_journal[0], str(pvp_rolls[1])])
            pvp_journal[0] = " - ".join([pvp_journal[0], "**Failure!**"])
            charutils.update_character_statistics(defender_statistics)

        pvp_report_lists = []
        pvp_report_lists.append(["Fighter"])
        pvp_report_lists.append(["Class"])
        pvp_report_lists.append(["Level"])
        pvp_report_lists.append(["GS"])
        pvp_report_lists.append(["HP"])
        pvp_report_lists.append(["Roll"])

        for i,fighter in enumerate(pvp_characters):
            pvp_report_lists[0].append(fighter.name)
            pvp_report_lists[1].append(fighter.character_class.name)
            pvp_report_lists[2].append(str(fighter.level))
            pvp_report_lists[3].append(str(fighter.gear.gearscore))
            pvp_report_lists[4].append(make_hp_bar(fighter.current_hp, fighter.character_class.max_hp))
            pvp_report_lists[5].append(str(pvp_rolls[i]))

        pvp_journal[0] = "".join([pvp_journal[0], (make_table(pvp_report_lists))])
        return pvp_journal

    def run_personal_quest(self) -> str:
        hero = random.choice(charutils.get_all_characters())
        personal_quest_hook = random.choice([line for line in PERSONAL_QUESTS if line[0] == str(hero.character_class.id_)])[2:]
        xp_reward = randint(500, 2000)
        personal_quest_journal = ""
        personal_quest_journal = "".join([personal_quest_journal, hero.name])
        personal_quest_journal = " ".join([personal_quest_journal, "the"])
        personal_quest_journal = " ".join([personal_quest_journal, hero.character_class.name])
        personal_quest_journal = "".join([personal_quest_journal, personal_quest_hook])
        personal_quest_journal = ", ".join([personal_quest_journal, "which earned"])
        personal_quest_journal = " ".join([personal_quest_journal, hero.name])
        personal_quest_journal = " ".join([personal_quest_journal, str(xp_reward)])
        personal_quest_journal = " ".join([personal_quest_journal, "xp."])
        hero.current_xp += xp_reward
        statistics = charutils.get_character_statistics(hero)
        statistics.personal_quests += 1
        charutils.update_character_statistics(statistics)
        charutils.update_db_character(charutils.character_to_db_character(hero))

        return personal_quest_journal

    def run_long_rest(self) -> str:
        old_characters = charutils.get_all_characters()
        rested_characters = []
        day_report = []

        old_characters.sort(key=lambda character: (-character.level, -character.gear.gearscore, -character.current_xp))
        for old_character in old_characters:
            resting_character = Character(old_character.id_, old_character.name, old_character.level, old_character.current_xp, old_character.current_hp, old_character.character_class, old_character.gear)
            resting_character.current_xp += resting_character.roll_for_passive_xp()
            rested_characters.append(resting_character.take_long_rest())

        for i, rested_character in enumerate(rested_characters):
            charutils.update_db_character(charutils.character_to_db_character(rested_character))
            charutils.update_db_gear(rested_character.gear)
            if rested_character.level != old_characters[i].level or rested_character.gear.gearscore != old_characters[i].gear.gearscore:
                personal_report = DayReport(rested_character.name, rested_character.level, rested_character.gear.gearscore, str(rested_character.current_xp) + "/" + str(rested_character.character_class.xp_per_level))
                if rested_character.level != old_characters[i].level:
                    personal_report.level_result = str(old_characters[i].level) + "->" + str(rested_character.level)
                if rested_character.gear.gearscore != old_characters[i].gear.gearscore:
                    personal_report.gearscore_result = str(old_characters[i].gear.gearscore) + "->" + str(rested_character.gear.gearscore)
                if rested_character.current_xp != old_characters[i].current_xp:
                    personal_report.xp_result = str(rested_character.current_xp) + "/" + str(rested_character.character_class.xp_per_level)
                day_report.append(personal_report)

        if len(day_report) == 0:
            return ""
        else:
            table_lists = []
            table_lists.append(["Character"])
            table_lists.append(["Level"])
            table_lists.append(["GS"])
            table_lists.append(["XP"])

            for character in day_report:
                table_lists[0].append(character.character_name)
                table_lists[1].append(str(character.level_result))
                table_lists[2].append(str(character.gearscore_result))
                table_lists[3].append(str(character.xp_result))

            string_day_report = make_table(table_lists)

            return string_day_report