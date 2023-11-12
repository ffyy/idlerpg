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

class EventOutcomes:
    def __init__(
            self,
            outcome_messages: list[str],
            deaths: list[str]
            ):
        self.outcome_messages = outcome_messages
        self.deaths = deaths

class DungeonMaster:
    def __init__(
            self):
        self.events_list = []
        self.initialize_events_list()

    def choose_and_run_event(self) -> EventOutcomes:
        """Randomly chooses an event type from the list of remaining event types before a long rest. Once triggered, the event type is removed from the list.\n
        If all event types have been removed from the list, a run_long_rest() is triggered and the remaining events list is reset to the list defined in DEFAULT_EVENTS_LIST.\n
        The PvP event is only run if there are more than 5 living characters in the world, otherwise another class quest is run.
        """
        if not self.events_list:
            print("out of events, running long rest")
            self.initialize_events_list()
            return self.run_long_rest()

        chosen_event = random.choice(self.events_list)
        self.events_list.remove(chosen_event)

        match chosen_event:
            case 0:
                print("chose personal quest")
                return self.run_class_quest()
            case 1:
                print("chose adventure")
                return self.run_adventure()
            case 2:
                if charutils.get_character_count() > 5: #in worlds with few characters, constant PvP is too volatile
                    print("chose pvp")
                    return self.run_pvp_encounter()
                else:
                    print("chose class quest because of lack of characters")
                    return self.run_class_quest()
            case _:
                return EventOutcomes([],[])

    def initialize_events_list(self):
        self.events_list = []
        for value in DEFAULT_EVENTS_LIST:
            self.events_list.append(value)

    def give_quest_rewards(self, quest: Quest, event_outcomes: EventOutcomes) -> EventOutcomes:
        """Adds rewards depending on Quest.quest_type values to the characters in Quest.party and saves the changes to database.
        Amount of XP depends on the difficulty of the quest.

        Arguments:
            quest: a Quest object which has been completed by complete_quest()
            event_outcomes: an existing EventOutcomes object is required as this should be called only as a result of a successful quest.
                If giving out rewards triggers an additional event, the outcome of the additional event will be appended to the provided EventOutcomes object.
        """
        if "experience" in quest.quest_type:
            for adventurer in quest.party:
                adventurer.current_xp += int(10000*(quest.quest_difficulty/(100*len(quest.party))))
                charutils.update_db_character(charutils.character_to_db_character(adventurer))
        if "loot" in quest.quest_type:
            if sum(character.character_class.id_ == 2 for character in quest.party) >= 2: #placeholder, replace fighter with hunter class once added
                fighters = random.sample(quest.party, 2)
                item_name = random.choice(ITEMS)
                description = "**Disputed item!**\n" + fighters[0].name + " and " + fighters[1].name + " both wanted the magic item and decided to fight over it."
                event_outcomes = self.run_pvp_encounter(event_outcomes, fighters, item_name, description)
            else:
                carry_index = quest.party_rolls.index(max(quest.party_rolls))
                quest.party[carry_index].gear.unattuned += 1
                charutils.update_db_gear(quest.party[carry_index].gear)

        return event_outcomes

    def complete_quest(self, dm_quest: Quest) -> Quest:
        """Completes the provided Quest object by having all Character objects in the Quest.party attribute roll dice.\n
        If the sum of the party rolls is at least as high as the quest difficulty, the quest is successful.\n
        Always awards XP on success, may award loot on success depending on the difficulty and sum of the party rolls.

        Arguments:
            dm_quest: a non-completed Quest, which has a Quest.party, Quest.difficulty, at least one Quest.type and a partially filled Quest.journal
        """
        QUEST_ITEM_THRESHOLD = 0.8 #if the quest is successful and the sum of party rolls is at least 80% of everyone rolling a 100, an item is guaranteed

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
            completed_quest.quest_journal = " ".join([completed_quest.quest_journal, "Luckily,"])
            completed_quest.quest_journal = " ".join([completed_quest.quest_journal, random.choice(SUCCESS_DESCRIPTIONS)])
            healer = next((hero for hero in completed_quest.party if hero.character_class.id_ == 6), None)
            if healer:
                hp_gain = random.randint(3,24) + 4
                for character in completed_quest.party:
                    character.current_hp = min(character.current_hp + hp_gain, character.character_class.max_hp)
                    charutils.update_db_character(charutils.character_to_db_character(character))
                completed_quest.quest_journal = " ".join([completed_quest.quest_journal, "Thanks to"])
                completed_quest.quest_journal = " ".join([completed_quest.quest_journal, healer.name])
                completed_quest.quest_journal = ", ".join([completed_quest.quest_journal, "everyone was healed for"])
                completed_quest.quest_journal = " ".join([completed_quest.quest_journal, str(hp_gain)])
                completed_quest.quest_journal = " ".join([completed_quest.quest_journal, "HP."])
            if "loot" in dm_quest.quest_type:
                if sum(character.character_class.id_ == 2 for character in dm_quest.party) >= 2:
                    completed_quest.quest_journal = " ".join([completed_quest.quest_journal, "A magic item was also found, but it was contested."])
                else:
                    carry_index = completed_quest.party_rolls.index(max(completed_quest.party_rolls))
                    item_name = random.choice(ITEMS)
                    completed_quest.quest_journal = " ".join([completed_quest.quest_journal, completed_quest.party[carry_index].name])
                    completed_quest.quest_journal = " ".join([completed_quest.quest_journal, "also found"])
                    if item_name[0] in "aeoiu":
                        completed_quest.quest_journal = " ".join([completed_quest.quest_journal, "an"])
                    else:
                        completed_quest.quest_journal = " ".join([completed_quest.quest_journal, "a"])
                    completed_quest.quest_journal = " ".join([completed_quest.quest_journal, item_name])
                    completed_quest.quest_journal = "".join([completed_quest.quest_journal, "!"])
            if "experience" in dm_quest.quest_type:
                completed_quest.quest_journal = "\n".join([completed_quest.quest_journal, "XP reward:"])
                completed_quest.quest_journal = " ".join([completed_quest.quest_journal, str(int(10000*(completed_quest.quest_difficulty/party_max_roll)))])
            completed_quest.quest_journal = "\n".join([completed_quest.quest_journal, str(sum(completed_quest.party_rolls))])
            completed_quest.quest_journal = "/".join([completed_quest.quest_journal, str(dm_quest.quest_difficulty)])
            completed_quest.quest_journal = " - ".join([completed_quest.quest_journal, "**Success!**"])
        else:
            hp_loss = int(100 - (sum(completed_quest.party_rolls) / dm_quest.quest_difficulty) * 100)
            completed_quest.outcome = 0
            completed_quest.quest_journal = " ".join([completed_quest.quest_journal, "Unfortunately,"])
            completed_quest.quest_journal = " ".join([completed_quest.quest_journal, random.choice(FAILURE_DESCRIPTIONS)])
            completed_quest.quest_journal = " ".join([completed_quest.quest_journal, "Everyone involved lost"])
            completed_quest.quest_journal = " ".join([completed_quest.quest_journal, str(hp_loss)])
            completed_quest.quest_journal = " ".join([completed_quest.quest_journal, "HP."])
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
                    completed_quest.quest_journal = " ".join([completed_quest.quest_journal, character.name])
                    completed_quest.quest_journal = " ".join([completed_quest.quest_journal, "died and was reincarnated at level 0!"])
            completed_quest.quest_journal = "\n".join([completed_quest.quest_journal, str(sum(completed_quest.party_rolls))])
            completed_quest.quest_journal = "/".join([completed_quest.quest_journal, str(dm_quest.quest_difficulty)])
            completed_quest.quest_journal = " - ".join([completed_quest.quest_journal, "**Failure!**"])

        return completed_quest

    def run_adventure(self, event_outcomes: EventOutcomes=None) -> EventOutcomes:
        """Creates a Quest object by selecting a quest hook, a difficulty, and randomly gathering a party from all characters. The quest is then resolved by the complete_quest() function.\n

        Arguments:
            event_outcomes: if provided, will append the outcome of this event to the provided EventOutcomes object.
        """
        character_ids = charutils.get_character_ids()

        #SUPPORTED_QUEST_TYPES = ["experience", "loot"]
        quest_type = ["experience"]

        quest_hook = " ".join(["**An epic adventure was had!**\nThe heroes were given an epic quest. They had to", random.choice(QUEST_HOOKS)])

        quest = Quest(quest_type, [], [], [], 0, quest_hook, 0)

        if not character_ids:
            return EventOutcomes(["I tried to run an adventure, but nobody showed up. 😢"], [])

        if(len(character_ids)) == 1:
            quest.party.append(charutils.get_character_by_id(character_ids[0][0]))
        else:
            party_size = random.randint(2,(max(2, (len(character_ids)//2))))
            for character_id in random.sample(character_ids, party_size):
                quest.party.append(charutils.get_character_by_id(character_id[0]))

        difficulty = random.randint(20,100)*len(quest.party)
        quest.quest_difficulty = difficulty

        completed_quest = self.complete_quest(quest)

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
        if event_outcomes:
            event_outcomes.outcome_messages.append(completed_quest.quest_journal)
            event_outcomes.deaths = completed_quest.death_notices
        else:
            event_outcomes = EventOutcomes([completed_quest.quest_journal], completed_quest.death_notices)

        if completed_quest.outcome == 1:
            event_outcomes = self.give_quest_rewards(completed_quest, event_outcomes)

        return event_outcomes

    def run_pvp_encounter(self, event_outcomes: EventOutcomes=None, fighters: list[Character]=None, item_reward: str=None, description: str=None) -> EventOutcomes:
        """ Runs a PvP encounter (roll-off) between two characters. The character with the lower roll loses current_hp and may die.\n

        Arguments:
            event_outcomes: If provided, appends the results to the provided EventOutcomes object.
            fighters: If provided, the first two characters in that list will fight.
            item_reward: If provided, the winner will be awarded +1 GS instead of XP and the journal will mention the item_reward by name.
            description: If provided, the provided description will be used in the Discord message instead of the default PvP description.
        """
        if fighters:
            pvp_characters = fighters
            pvp_journal = description
        else:
            all_characters = charutils.get_all_characters()
            all_characters.sort(key=lambda character:character.level)
            i_ganker = randint(0, len(all_characters)//2)
            pvp_characters = []
            pvp_characters.append(all_characters[i_ganker])
            del all_characters[0:i_ganker+1]
            pvp_characters.append(random.choice(all_characters))
            pvp_journal = "**Heroes fighting heroes!**\n" + pvp_characters[0].name + " waited for the right moment and attacked " + pvp_characters[1].name + "."

        ganker_statistics = charutils.get_character_statistics(pvp_characters[0])
        defender_statistics = charutils.get_character_statistics(pvp_characters[1])
        ganker_statistics.ganks_attempted += 1
        defender_statistics.defences_attempted += 1
        charutils.update_character_statistics(ganker_statistics)
        charutils.update_character_statistics(defender_statistics)
        deaths = []

        pvp_rolls = []
        for character in pvp_characters:
            character_roll = character.roll_dice() + character.gear.gearscore
            pvp_rolls.append(character_roll)
        xp_reward = min((max(1, pvp_characters[1].level - pvp_characters[0].level) * 1000), 10000)
        hp_loss = abs(pvp_rolls[0] - pvp_rolls[1])
        if pvp_rolls[0] >= pvp_rolls[1]:
            ganker_statistics.ganks_won += 1
            #fill outcome flavor text in journal
            pvp_journal = " ".join([pvp_journal, pvp_characters[0].name])
            pvp_journal = "".join([pvp_journal, random.choice([line for line in PVP_OUTCOMES if line[0] == "1"])[2:]])
            #start handling loser hp loss
            pvp_characters[1].current_hp -= hp_loss
            pvp_journal = ". ".join([pvp_journal, pvp_characters[1].name])
            pvp_journal = " ".join([pvp_journal, "lost"])
            pvp_journal = " ".join([pvp_journal, str(hp_loss)])
            pvp_journal = " ".join([pvp_journal, "HP."])
            #start handling loser death
            if pvp_characters[1].current_hp > 0:
                charutils.update_db_character(charutils.character_to_db_character(pvp_characters[1]))
            elif pvp_characters[1].current_hp <= 0:
                pvp_characters[1].current_hp = 0
                ganker_statistics.pks += 1
                deaths.append(charutils.get_discord_id_by_character(pvp_characters[1]))
                charutils.reincarnate(pvp_characters[1])
                pvp_journal = " ".join([pvp_journal, pvp_characters[1].name])
                pvp_journal = " ".join([pvp_journal, "died and was reincarnated at level 0!"])
                #start handling loot
                pvp_journal = " ".join([pvp_journal, pvp_characters[0].name])
                pvp_journal = " ".join([pvp_journal, "looted a few magic items."])
                items_found = randint(1, max(pvp_characters[1].gear.gearscore, 1))
                pvp_characters[0].gear.unattuned += items_found
                discord_id = charutils.get_discord_id_by_character(pvp_characters[1])
            #fill outcome statistics in journal
            if item_reward:
                pvp_journal = "\n".join([pvp_journal, pvp_characters[0].name])
                pvp_journal = " ".join([pvp_journal, "ended up getting the"])
                pvp_journal = " ".join([pvp_journal, item_reward])
                pvp_journal = "".join([pvp_journal, "!"])
                pvp_characters[0].gear.unattuned += 1
            else:
                pvp_journal = "\n".join([pvp_journal, "XP reward for"])
                pvp_journal = " ".join([pvp_journal, pvp_characters[0].name])
                pvp_journal = ": ".join([pvp_journal, str(xp_reward)])
                pvp_characters[0].current_xp += xp_reward
                pvp_journal = "\n".join([pvp_journal, str(pvp_rolls[0])])
                pvp_journal = "/".join([pvp_journal, str(pvp_rolls[1])])
                pvp_journal = " - ".join([pvp_journal, "**Success!**"])
            #handle rewards for ganker
            charutils.update_character_statistics(ganker_statistics)
            charutils.update_db_gear(pvp_characters[0].gear)
            charutils.update_db_character(charutils.character_to_db_character(pvp_characters[0]))
        elif pvp_rolls[0] < pvp_rolls[1]:
            defender_statistics.defences_won += 1
            #fill outcome flavor text in journal
            pvp_journal = " ".join([pvp_journal, "Unfortunately,"])
            pvp_journal = " ".join([pvp_journal, pvp_characters[0].name])
            pvp_journal = "".join([pvp_journal, random.choice([line for line in PVP_OUTCOMES if line[0] == "0"])[2:]])
            #start handling loser hp loss
            pvp_characters[0].current_hp -= hp_loss
            pvp_journal = ". ".join([pvp_journal, pvp_characters[0].name])
            pvp_journal = " ".join([pvp_journal, "lost"])
            pvp_journal = " ".join([pvp_journal, str(hp_loss)])
            pvp_journal = " ".join([pvp_journal, "HP."])
            #start handling loser death
            if pvp_characters[0].current_hp > 0:
                charutils.update_db_character(charutils.character_to_db_character(pvp_characters[0]))
            elif pvp_characters[0].current_hp <= 0:
                deaths.append(charutils.get_discord_id_by_character(pvp_characters[0]))
                pvp_characters[0].current_hp = 0
                defender_statistics.pks += 1
                charutils.reincarnate(pvp_characters[0])
                pvp_journal = " ".join([pvp_journal, pvp_characters[0].name])
                pvp_journal = " ".join([pvp_journal, "died and was reincarnated at level 0!"])
                #start handling loot
                pvp_journal = " ".join([pvp_journal, pvp_characters[1].name])
                pvp_journal = " ".join([pvp_journal, "looted a few magic items."])
                items_found = randint(1, max(pvp_characters[0].gear.gearscore, 1))
                pvp_characters[1].gear.unattuned += items_found
            #fill outcome statistics in journal
            if item_reward:
                pvp_journal = "\n".join([pvp_journal, pvp_characters[1].name])
                pvp_journal = " ".join([pvp_journal, "ended up getting the"])
                pvp_journal = " ".join([pvp_journal, item_reward])
                pvp_journal = "".join([pvp_journal, "!"])
                pvp_characters[1].gear.unattuned += 1
            else:
                pvp_journal = "\n".join([pvp_journal, str(pvp_rolls[0])])
                pvp_journal = "/".join([pvp_journal, str(pvp_rolls[1])])
                pvp_journal = " - ".join([pvp_journal, "**Failure!**"])
            charutils.update_db_gear(pvp_characters[1].gear)
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

        pvp_journal = "".join([pvp_journal, (make_table(pvp_report_lists))])

        if event_outcomes:
            event_outcomes.outcome_messages.append(pvp_journal)
            for discord_id in deaths:
                if discord_id not in event_outcomes.deaths:
                    event_outcomes.deaths.append(discord_id)
        else:
            event_outcomes = EventOutcomes([pvp_journal], deaths)

        return event_outcomes

    def run_class_quest(self, event_outcomes: EventOutcomes=None) -> EventOutcomes:
        """Chooses a class from among classes that have at least one registered character. Generates a party of 1-3 characters of this class and awards free XP to all characters.\n
        If 2 fighters are chosen, one of them will fight the other for experience and honor.

        Arguments:
            event_outcomes: if provided, appends the outcome of this event to the provided EventOutcomes
        """
        all_characters = charutils.get_all_characters()
        if not all_characters:
            return EventOutcomes(["Something super awful happened because this world has no heroes yet."], [])
        chosen_class = random.choice(all_characters).character_class
        potential_characters = [character for character in all_characters if character.character_class.id_ == chosen_class.id_]
        party_size = min(random.randint(1, len(potential_characters)), 3)
        chosen_party = random.sample(potential_characters, party_size)
        class_quest_hook = random.choice([line for line in PERSONAL_QUESTS if line[0] == str(chosen_class.id_)])[2:]
        xp_reward = randint(500, 2000)
        #class specific replacement events
        if party_size == 2 and chosen_class.id_ == 2: #fighters will duel if left together
            description = "**XP is not given, it is taken!**\n" + chosen_party[1].name + class_quest_hook + " and earned " + str(xp_reward) + " xp. " \
                + chosen_party[0].name + " decided to earn the xp in a duel instead and attacked " + chosen_party[1].name + "!"
            #defender still gets XP
            chosen_party[1].current_xp += xp_reward
            defender_statistics = charutils.get_character_statistics(chosen_party[1])
            defender_statistics.personal_quests += 1
            charutils.update_character_statistics(defender_statistics)
            charutils.update_db_character(charutils.character_to_db_character(chosen_party[1]))
            return self.run_pvp_encounter(event_outcomes, chosen_party, None, description)

        if party_size == 1:
            class_quest_journal = "**A hero did something!**\n"
            class_quest_journal = "".join([class_quest_journal, chosen_party[0].name])
            class_quest_journal = " ".join([class_quest_journal, "the"])
            class_quest_journal = " ".join([class_quest_journal, chosen_class.name])
        else:
            class_quest_journal = "**Heroes of a feather stick together!**\n"
            for hero in chosen_party:
                if hero != chosen_party[0] and hero != chosen_party[-1]:
                    class_quest_journal = "".join([class_quest_journal, ", "])
                elif hero == chosen_party[-1]:
                    class_quest_journal = " ".join([class_quest_journal, "and "])
                class_quest_journal = "".join([class_quest_journal, hero.name])
        class_quest_journal = "".join([class_quest_journal, class_quest_hook])
        class_quest_journal = ", ".join([class_quest_journal, "which earned them"])
        class_quest_journal = " ".join([class_quest_journal, str(xp_reward)])
        class_quest_journal = " ".join([class_quest_journal, "xp."])
        for hero in chosen_party:
            hero.current_xp += xp_reward
            statistics = charutils.get_character_statistics(hero)
            statistics.personal_quests += 1
            charutils.update_character_statistics(statistics)
            charutils.update_db_character(charutils.character_to_db_character(hero))

        if event_outcomes:
            event_outcomes.outcome_messages.append(class_quest_journal)
        else:
            event_outcomes = EventOutcomes([class_quest_journal], [])

        return event_outcomes

    def run_long_rest(self) -> EventOutcomes:
        """Runs the Character.take_long_rest() function for all living characters. If level or gearscore changes for at least one character as a result of this,
        returns an EventOutcomes object which includes a message with the results of the long rest.\n
        If there are no changes in level or gearscore and at least two living characters exist in the world, will trigger a PvP encounter between two random characters.\n
        Doesn't accept EventOutcomes as an argument because resting should not be triggered from some other event.
        """
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
            if charutils.get_character_count() >= 2:
                fighters = random.sample(charutils.get_all_characters(), 2)
                description = "**Violence in the night!**\nA tense situation developed, as the adventurers decided to take a rest, but weren't all that tired. " + fighters[0].name + " ended up attacking " + fighters[1].name + ", which surely livened up the evening."
                event_outcomes = self.run_pvp_encounter(None, fighters, None, description)
            else:
                event_outcomes = EventOutcomes([],[])
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

            rest_message = "**The adventurers sat down to take a long rest.**\nDuring the night, they thought about experiences they had had during the day and attuned new magic items. Character statistics in the morning:"
            string_day_report = make_table(table_lists)
            rest_message = "".join([rest_message, string_day_report])
            event_outcomes = EventOutcomes([rest_message], [])

        return event_outcomes