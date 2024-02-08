import random
import charutils
from rpgobjects import *
from helpers import *

QUEST_HOOKS = open("content/quests.txt").read().splitlines()
PERSONAL_QUESTS = open("content/personalquests.txt").read().splitlines()
SUCCESS_DESCRIPTIONS = open("content/successes.txt").read().splitlines()
FAILURE_DESCRIPTIONS = open("content/failures.txt").read().splitlines()
PVP_OUTCOMES = open("content/pvpoutcomes.txt").read().splitlines()
RAID_OUTCOMES = open("content/raidoutcomes.txt").read().splitlines()
ITEMS = open("content/items.txt").read().splitlines()
DEFAULT_DAILY_EVENTS_LIST = [0, 1, 2]
DEFAULT_MONTHLY_EVENTS_LIST = [2, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
CLERIC_MAX_BUFF = 6
QUEST_MINIMUM_DIFFICULTY = 20

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
        self.daily_events_list = []
        self.monthly_events_list = []
        self.active_boss = None
        self.load_state()
        self.summon_new_boss()

    def load_state(self):
        daily_state_string = charutils.get_daily_state()
        loaded_daily_events_list = []
        if daily_state_string:
            for char in daily_state_string:
                loaded_daily_events_list.append(int(char))
        print("events loaded from db: " + str(loaded_daily_events_list))
        self.daily_events_list = loaded_daily_events_list

        monthly_state_string = charutils.get_monthly_state()
        loaded_monthly_events_list = []
        if monthly_state_string:
            split_monthly_state = monthly_state_string.split(".")
            for char in split_monthly_state[0]:
                loaded_monthly_events_list.append(int(char))
            for i in range(int(split_monthly_state[1])):
                loaded_monthly_events_list.append(0)
        print("events loaded from db: " + str(loaded_monthly_events_list))
        self.monthly_events_list = loaded_monthly_events_list

    def generate_daily_state(self) -> str:
        daily_state_string = ""
        if 0 in self.daily_events_list:
            daily_state_string = "".join([daily_state_string, "0"])
        if 1 in self.daily_events_list:
            daily_state_string = "".join([daily_state_string, "1"])
        if 2 in self.daily_events_list:
            daily_state_string = "".join([daily_state_string, "2"])
        return daily_state_string

    def generate_monthly_state(self) -> str:
        monthly_state_string = ""
        if 2 in self.monthly_events_list:
            monthly_state_string = "".join([monthly_state_string, "2"])
        if 1 in self.monthly_events_list:
            monthly_state_string = "".join([monthly_state_string, "1"])
        EVENT_TYPE_SEPARATOR = "."
        num_zeroes = sum(number == 0 for number in self.monthly_events_list)
        monthly_state_string = EVENT_TYPE_SEPARATOR.join([monthly_state_string, str(num_zeroes)])
        return monthly_state_string

    def update_states(self):
        daily_state = self.generate_daily_state()
        monthly_state = self.generate_monthly_state()
        charutils.update_state(daily_state, monthly_state)

    def shutdown(self) -> bool:
        #would be nice if in case of problems saving state it was caught and a warning was returned instead
        daily_state = self.generate_daily_state()
        monthly_state = self.generate_monthly_state()
        charutils.update_state(daily_state, monthly_state)
        print("saved daily state: " + charutils.get_daily_state())
        print("saved monthly state: " + charutils.get_monthly_state())
        return True

    def is_pvp_allowed(self) -> bool:
        """Checks if there are enough characters in the world for random PvP events to trigger. Returns true in case there are at least 6 living characters.
        """
        if charutils.get_character_count() > 5:
            return True
        else:
            return False

    def choose_and_run_daily_event(self) -> EventOutcomes:
        """Randomly chooses an event type from the list of remaining daily event types before a long rest. Once triggered, the event type is removed from the list.\n
        If all event types have been removed from the list, a run_long_rest() is triggered and the remaining events list is reset to the list defined in DEFAULT_EVENTS_LIST.\n
        The PvP event is only run if there are more than 5 living characters in the world, otherwise another class quest is run.
        """
        if not self.daily_events_list:
            print("out of events, running long rest")
            self.initialize_daily_events_list()
            self.update_states()
            return self.run_long_rest()

        chosen_event = random.choice(self.daily_events_list)
        self.daily_events_list.remove(chosen_event)
        self.update_states()

        match chosen_event:
            case 0:
                print("chose personal quest")
                return self.run_class_quest()
            case 1:
                print("chose adventure")
                return self.run_adventure()
            case 2:
                if self.is_pvp_allowed():
                    print("chose pvp")
                    return self.run_pvp_encounter()
                else:
                    print("chose class quest because of lack of characters")
                    return self.run_class_quest()
            case _:
                return EventOutcomes([],[])

    def choose_and_run_monthly_event(self) -> EventOutcomes:
        """A month in the game world is equal to timescale * 30.\n
        Randomly chooses an event type from the list of remaining monthly events. The list of monthly events is only reset when the month is over, meaning only if this
        function has been called 30 times. If event type 0 is chosen, nothing happens this game day.
        """
        if not self.monthly_events_list:
            self.initialize_monthly_events_list()

        chosen_event = random.choice(self.monthly_events_list)
        self.monthly_events_list.remove(chosen_event)
        self.update_states()

        match chosen_event:
            case 0:
                print("nothing happened")
                return EventOutcomes([],[])
            case 1:
                print("running gangbang")
                return self.run_group_pvp()
            case 2:
                print("running raid boss")
                return self.run_raidboss_encounter()

    def initialize_daily_events_list(self):
        self.daily_events_list = []
        for value in DEFAULT_DAILY_EVENTS_LIST:
            self.daily_events_list.append(value)

    def initialize_monthly_events_list(self):
        self.monthly_events_list = []
        for value in DEFAULT_MONTHLY_EVENTS_LIST:
            self.monthly_events_list.append(value)

    def summon_new_boss(self):
        bosses = charutils.get_all_bosses()
        bosses.sort(key=lambda boss: (boss.target_level, boss.current_hp-boss.max_hp))
        self.active_boss = bosses[0]

    def update_current_boss(self):
        if self.active_boss.current_hp > 0:
            charutils.update_boss(self.active_boss)
        else:
            self.active_boss.current_hp = self.active_boss.max_hp
            self.active_boss.target_level = self.active_boss.target_level * 2
            charutils.update_boss(self.active_boss)
            self.summon_new_boss()

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
            hunter = next((character for character in quest.party if character.is_hunter()), None)
            if hunter: #hunters will always need-roll everything
                if sum(character.is_hunter() for character in quest.party) >= 2: #if there are two or more hunters, two of them will fight over the item
                    potential_fighters = list(character for character in quest.party if character.character_class.id_ == 8)
                    fighters = random.sample(potential_fighters, 2)
                    item_name = random.choice(ITEMS)
                    description = "**Disputed item!**\n" + fighters[0].name + " and " + fighters[1].name + " both wanted the magic item and decided to fight over it."
                    event_outcomes = self.run_pvp_encounter(event_outcomes, fighters, item_name, description)
                else:
                    hunter.gear.unattuned += 1
                    charutils.update_db_gear(hunter.gear)
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
        buff = 0
        buffer = next((hero for hero in completed_quest.party if hero.is_cleric()), None)
        if buffer:
            buff = randint(1,CLERIC_MAX_BUFF)
            completed_quest.quest_journal = " ".join([completed_quest.quest_journal, buffer.name])
            completed_quest.quest_journal = " ".join([completed_quest.quest_journal, "gave everyone a buff, which gave them a bonus of"])
            completed_quest.quest_journal = " ".join([completed_quest.quest_journal, str(buff)])
            completed_quest.quest_journal = " ".join([completed_quest.quest_journal, "to their rolls."])
        for adventurer in dm_quest.party:
            completed_quest.party_bonuses.append(adventurer.bonus + adventurer.gear.gearscore + buff)
            adventurer_roll = adventurer.roll_dice(adventurer.gear.gearscore + buff)
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
            if buffer:
                hp_gain = random.randint(1,8) + 4
                for character in completed_quest.party:
                    character.current_hp = min(character.current_hp + hp_gain, character.character_class.max_hp)
                    charutils.update_db_character(charutils.character_to_db_character(character))
                completed_quest.quest_journal = " ".join([completed_quest.quest_journal, "Thanks to"])
                completed_quest.quest_journal = " ".join([completed_quest.quest_journal, buffer.name])
                completed_quest.quest_journal = ", ".join([completed_quest.quest_journal, "everyone was healed for"])
                completed_quest.quest_journal = " ".join([completed_quest.quest_journal, str(hp_gain)])
                completed_quest.quest_journal = " ".join([completed_quest.quest_journal, "HP."])
            if "loot" in dm_quest.quest_type:
                if sum(character.character_class.id_ == 8 for character in dm_quest.party) >= 2:
                    completed_quest.quest_journal = " ".join([completed_quest.quest_journal, "A magic item was also found, but it was contested."])
                else:
                    carry_index = completed_quest.party_rolls.index(max(completed_quest.party_rolls))
                    item_name = random.choice(ITEMS)
                    hunter = next((hero for hero in completed_quest.party if hero.character_class.id_ == 8), None)
                    if hunter:
                        completed_quest.quest_journal = " ".join([completed_quest.quest_journal, hunter.name])
                    else:
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
                    discord_id = charutils.get_discord_id_by_character(character)
                    permanent_death = character.die(-1)
                    if permanent_death:
                        completed_quest.death_notices.append(discord_id)
                        completed_quest.quest_journal = " ".join([completed_quest.quest_journal, character.name])
                        completed_quest.quest_journal = " ".join([completed_quest.quest_journal, "died and was reincarnated at level 0!"])
                    else:
                        completed_quest.quest_journal = " ".join([completed_quest.quest_journal, character.name])
                        completed_quest.quest_journal = " ".join([completed_quest.quest_journal, "would have died but was saved by the Aegis of Immortality!"])
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

        quest = Quest(quest_type, [], [], [], [], 0, quest_hook, 0)

        if not character_ids:
            return EventOutcomes(["I tried to run an adventure, but nobody showed up. 😢"], [])

        if(len(character_ids)) == 1:
            quest.party.append(charutils.get_character_by_id(character_ids[0][0]))
        else:
            party_size = random.randint(2,(max(2, (len(character_ids)//2))))
            for character_id in random.sample(character_ids, party_size):
                quest.party.append(charutils.get_character_by_id(character_id[0]))

        difficulty = random.randint(QUEST_MINIMUM_DIFFICULTY,100)*len(quest.party)
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
            raw_roll = completed_quest.party_rolls[i] - completed_quest.party_bonuses[i]
            completed_quest_lists[0].append(hero.name)
            completed_quest_lists[1].append(hero.character_class.name)
            completed_quest_lists[2].append(str(hero.level))
            completed_quest_lists[3].append(str(hero.gear.gearscore))
            completed_quest_lists[4].append(hero.get_hp_bar())
            completed_quest_lists[5].append(str(completed_quest.party_rolls[i]) + " (" + str(raw_roll) + "+" + str(completed_quest.party_bonuses[i]) + ")")

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

    def run_raidboss_encounter(self) -> EventOutcomes:
        """Runs a fight where all living characters battle against one of the raid bosses in the world. Each character will take damage from the boss depending on the level
        of the character and the difficulty modifier of the boss.
        """

        event_outcomes = EventOutcomes([],[])
        party = charutils.get_all_characters()
        party_max_level = max(party, key=lambda character: character.level).level
        random.shuffle(party)
        boss_difficulty = random.randint(QUEST_MINIMUM_DIFFICULTY,100)
        xp_reward = 10000

        boss_journal = "**AN EPIC RAID!**\n"
        boss_journal = "".join([boss_journal, "All the heroes in the world got together in an attempt to take down"])
        boss_journal = " ".join([boss_journal, self.active_boss.name])
        boss_journal = "".join([boss_journal, "!"])
        boss_journal = " ".join([boss_journal, "This is a level"])
        boss_journal = " ".join([boss_journal, str(self.active_boss.target_level)])
        boss_journal = " ".join([boss_journal, "encounter."])
        if self.active_boss.target_level > party_max_level + 15:
            boss_journal = "\n".join([boss_journal, "Upon seeing this target level, they decided that the boss is too difficult for them."])
            boss_journal = " ".join([boss_journal, "They instead took the opportunity to do some additional quests to weaken the boss, reducing the target level to"])
            boss_journal = " ".join([boss_journal, str(party_max_level + 15)])
            boss_journal = "".join([boss_journal, "."])
            self.active_boss.target_level = party_max_level + 15
            self.update_current_boss()
            event_outcomes.outcome_messages.append(boss_journal)
            return event_outcomes
        boss_journal = " ".join([boss_journal, "This time the target number to hold your own in the fight was"])
        boss_journal = " ".join([boss_journal, str(boss_difficulty)])
        boss_journal = "".join([boss_journal, "."])

        buff = 0
        buffer = next((hero for hero in party if hero.is_cleric()), None)
        if buffer:
            buff = randint(1,CLERIC_MAX_BUFF)
            boss_journal = "\n".join([boss_journal, buffer.name])
            boss_journal = " ".join([boss_journal, "gave everyone a buff, which gave them a bonus of"])
            boss_journal = " ".join([boss_journal, str(buff)])
            boss_journal = " ".join([boss_journal, "to their rolls."])

        boss_starting_hp = self.active_boss.current_hp
        party_rolls = []
        party_bonuses = []
        hp_changes = []
        deaths = []
        aegises_lost = []
        killer = None
        for adventurer in party:
            personal_buff = buff + max((adventurer.level - self.active_boss.target_level), 0)
            party_bonuses.append(adventurer.gear.gearscore + adventurer.bonus + personal_buff)
            adventurer_roll = max(adventurer.roll_dice(adventurer.gear.gearscore + personal_buff), 1)
            party_rolls.append(adventurer_roll)
            damage = adventurer_roll-boss_difficulty
            if damage >= 0:
                hp_changes.append(damage)
                if self.active_boss.current_hp > 0:
                    self.active_boss.current_hp -= damage
                    if self.active_boss.current_hp <= 0:
                        killer = adventurer
                        killer.gear.unattuned += 1
                        killer.aegis = 1
                        charutils.update_db_character(killer)
                        charutils.update_db_gear(killer.gear)
                        self.active_boss.current_hp = 0
                        break
            else:
                ratio = self.active_boss.calculate_damage_ratio(adventurer)
                damage_to_hero = int(damage * ratio)
                hp_changes.append(damage_to_hero)
                if self.active_boss.boss_type == 1: #type 1 bosses just deal damage
                    adventurer.current_hp -= abs(damage_to_hero)
                    if adventurer.current_hp > 0:
                        charutils.update_db_character(charutils.character_to_db_character(adventurer))
                    elif adventurer.current_hp <= 0:
                        discord_id = charutils.get_discord_id_by_character(adventurer)
                        permanent_death = adventurer.die(-3)
                        if permanent_death:
                            deaths.append(adventurer)
                            event_outcomes.deaths.append(discord_id)
                        else:
                            aegises_lost.append(adventurer)
                elif self.active_boss.boss_type == 2: #type 2 bosses eat items
                    surviving_gear_modifier = (100 - abs(damage_to_hero))/100
                    adventurer.gear.gearscore = int(adventurer.gear.gearscore * surviving_gear_modifier)
                    charutils.update_db_gear(adventurer.gear)
                    deaths.append(adventurer) #they dont actually die, but this makes it easy to check if anyone lost gearscore

        boss_journal = " ".join([boss_journal, "During the battle,"])
        boss_journal = " ".join([boss_journal, self.active_boss.name])
        boss_journal = " ".join([boss_journal, "took a total of"])
        boss_journal = " ".join([boss_journal, str(boss_starting_hp - self.active_boss.current_hp)])
        boss_journal = " ".join([boss_journal, "damage."])
        if self.active_boss.boss_type == 1:
            if deaths:
                boss_journal = " ".join([boss_journal, "Unfortunately, that came at the cost of heroic sacrifice. "])
                for hero in deaths:
                    if hero != deaths[0] and hero != deaths[-1]:
                        boss_journal = "".join([boss_journal, ", "])
                    elif hero != deaths[0] and hero == deaths[-1]:
                        boss_journal = " ".join([boss_journal, "and "])
                    boss_journal = "".join([boss_journal, hero.name])
                boss_journal = " ".join([boss_journal, "fell in the battle and had to be reincarnated."])
            if aegises_lost:
                boss_journal = "".join([boss_journal, " "])
                for hero in aegises_lost:
                    if hero != aegises_lost[0] and hero != aegises_lost[-1]:
                        boss_journal = "".join([boss_journal, ", "])
                    elif hero != aegises_lost[0] and hero == aegises_lost[-1]:
                        boss_journal = " ".join([boss_journal, "and "])
                    boss_journal = "".join([boss_journal, hero.name])
                boss_journal = " ".join([boss_journal, "would have died, but survived thanks to the Aegis of Immortality."])
        elif self.active_boss.boss_type == 2 and deaths:
            boss_journal = " ".join([boss_journal, "Unfortunately, that came at the cost of material sacrifice."])
            boss_journal = " ".join([boss_journal, "All heroes who failed to hold their own lost a percentage of their gearscore equal to the scale of their failure."])
        if killer:
            boss_journal = "\n".join([boss_journal, killer.name])
            boss_journal = " ".join([boss_journal, random.choice(RAID_OUTCOMES)])
            boss_journal = " ".join([boss_journal, "and struck the killing blow!"])
            boss_journal = "\n".join([boss_journal, "Everyone who survived received"])
            boss_journal = " ".join([boss_journal, str(xp_reward)])
            boss_journal = " ".join([boss_journal, "xp, while"])
            boss_journal = " ".join([boss_journal, killer.name])
            boss_journal = " ".join([boss_journal, "also found a magic item and an Aegis of Immortality!"])
            for adventurer in party:
                if adventurer not in deaths:
                    adventurer.current_xp += xp_reward
                    charutils.update_db_character(charutils.character_to_db_character(adventurer))
            boss_journal = "\n".join([boss_journal, self.active_boss.name])
            boss_journal = " ".join([boss_journal, "was slain, but will eventually come back, stronger than ever!"])
            boss_journal = "\n".join([boss_journal, "**Success!**"])
        else:
            boss_journal = "\n".join([boss_journal, self.active_boss.name])
            boss_journal = " ".join([boss_journal, "survived the epic raid and will continue terrorizing the world!"])
            boss_journal = "\n".join([boss_journal, "**Failure!**"])

        boss_table = make_boss_hp_bar(self.active_boss.name, self.active_boss.current_hp, self.active_boss.max_hp, target_number=boss_difficulty)

        hero_strings = []
        hero_strings.append(["Hero"])
        hero_strings.append(["L"])
        hero_strings.append(["HP"])
        hero_strings.append(["DMG"])
        hero_strings.append(["Roll"])

        for i,hero in enumerate(party):
            if i < len(party_rolls):
                raw_roll = party_rolls[i] - party_bonuses[i]
                hero_strings[0].append(hero.name)
                hero_strings[1].append(str(hero.level))
                hero_strings[2].append(hero.get_hp_bar())
                hero_strings[3].append(str(hp_changes[i]))
                hero_strings[4].append(str(party_rolls[i]) + " (" + str(raw_roll) + "+" + str(party_bonuses[i]) + ")")

        hero_table = make_table(hero_strings)

        boss_journal = "".join([boss_journal, boss_table])
        boss_journal = "".join([boss_journal, "VS"])
        boss_journal = "".join([boss_journal, hero_table])

        event_outcomes.outcome_messages.append(boss_journal)

        self.update_current_boss()
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
        pvp_bonuses = []
        for character in pvp_characters:
            temporary_bonus = 0
            if character.character_class.id_ == 6: #clerics will buff themselves before fighting
                temporary_bonus = randint(1,CLERIC_MAX_BUFF)
            pvp_bonuses.append(character.bonus + character.gear.gearscore + temporary_bonus)
            character_roll = character.roll_dice(character.gear.gearscore + temporary_bonus)
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
                discord_id = charutils.get_discord_id_by_character(pvp_characters[1])
                permanent_death = pvp_characters[1].die(pvp_characters[0].id_)
                if permanent_death:
                    ganker_statistics.pks += 1
                    deaths.append(discord_id)
                    pvp_journal = " ".join([pvp_journal, pvp_characters[1].name])
                    pvp_journal = " ".join([pvp_journal, "died and was reincarnated at level 0!"])
                    #start handling loot
                    pvp_journal = " ".join([pvp_journal, pvp_characters[0].name])
                    pvp_journal = " ".join([pvp_journal, "looted a few magic items."])
                    items_found = randint(1, max(pvp_characters[1].gear.gearscore, 1))
                    pvp_characters[0].gear.unattuned += items_found
                else:
                    pvp_journal = " ".join([pvp_journal, pvp_characters[1].name])
                    pvp_journal = " ".join([pvp_journal, "would have died but was saved by the Aegis of Immortality!"])
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
                discord_id = charutils.get_discord_id_by_character(pvp_characters[0])
                permanent_death = pvp_characters[0].die(pvp_characters[1].id_)
                if permanent_death:
                    deaths.append(discord_id)
                    defender_statistics.pks += 1
                    pvp_journal = " ".join([pvp_journal, pvp_characters[0].name])
                    pvp_journal = " ".join([pvp_journal, "died and was reincarnated at level 0!"])
                    #start handling loot
                    pvp_journal = " ".join([pvp_journal, pvp_characters[1].name])
                    pvp_journal = " ".join([pvp_journal, "looted a few magic items."])
                    items_found = randint(1, max(pvp_characters[0].gear.gearscore, 1))
                    pvp_characters[1].gear.unattuned += items_found
                else:
                    pvp_journal = " ".join([pvp_journal, pvp_characters[0].name])
                    pvp_journal = " ".join([pvp_journal, "would have died but was saved by the Aegis of Immortality!"])
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
            raw_roll = pvp_rolls[i] - pvp_bonuses[i]
            pvp_report_lists[0].append(fighter.name)
            pvp_report_lists[1].append(fighter.character_class.name)
            pvp_report_lists[2].append(str(fighter.level))
            pvp_report_lists[3].append(str(fighter.gear.gearscore))
            pvp_report_lists[4].append(fighter.get_hp_bar())
            pvp_report_lists[5].append(str(pvp_rolls[i]) + " (" + str(raw_roll) + "+" + str(pvp_bonuses[i]) + ")")

        pvp_journal = "".join([pvp_journal, (make_table(pvp_report_lists))])

        if event_outcomes:
            event_outcomes.outcome_messages.append(pvp_journal)
            for discord_id in deaths:
                if discord_id not in event_outcomes.deaths:
                    event_outcomes.deaths.append(discord_id)
        else:
            event_outcomes = EventOutcomes([pvp_journal], deaths)

        return event_outcomes

    def run_group_pvp(self, fighters: list[Character]=None, description: str=None) -> EventOutcomes:
        """Runs a group fight in which the highest level character defends against 3 lower level characters. If the defender wins, they gain XP.
        If the defender loses, they lose XP. The fight is handled like several duels against the defender ongoing at once.
        In these fights, Characters may lose hp and die as in regular PvP.

        Arguments:
            fighters: if provided, the first character is the defender and other characters in the list are attackers
            description: if provided, overrides the journal entry for the fight in the Discord message. Expected to be passed only together with fighters.
        """
        event_outcomes = EventOutcomes([], [])
        if not self.is_pvp_allowed():
            return event_outcomes

        if fighters and description:
            defender = fighters[0]
            attackers = fighters.remove(defender)
            pvp_journal = description
        else:
            all_characters = charutils.get_all_characters()
            defender = max(all_characters, key=lambda character: character.level)
            all_characters.remove(defender)
            attackers_count = 3
            attackers = random.sample(all_characters, attackers_count)

            pvp_journal = "**One against many!**\n" + defender.name + " was attacked by "
            for attacker in attackers:
                if attacker != attackers[0] and attacker != attackers[-1]:
                    pvp_journal = "".join([pvp_journal, ", "])
                elif attacker == attackers[-1]:
                    pvp_journal = " ".join([pvp_journal, "and "])
                pvp_journal = "".join([pvp_journal, attacker.name])
            pvp_journal = " ".join([pvp_journal, "because of jealousy and had to put up a desparate defence!\n"])

        defender_rolls = []
        defender_bonuses = []
        attacker_rolls = []
        attacker_bonuses = []
        defender_statistics = charutils.get_character_statistics(defender)
        defender_statistics.defences_attempted += 1
        attacker_wins = 0
        for i,attacker in enumerate(attackers):
            defender_temp_bonus = 0
            attacker_temp_bonus = 0
            if defender.character_class.id_ == 6: #clerics will buff themselves before fighting
                defender_temp_bonus = randint(1,CLERIC_MAX_BUFF)
            defender_bonuses.append(defender.bonus + defender.gear.gearscore + defender_temp_bonus)
            defender_rolls.append(defender.roll_dice(defender.gear.gearscore + defender_temp_bonus))
            if attacker.character_class.id_ == 6: #clerics will buff themselves before fighting
                attacker_temp_bonus = randint(1,CLERIC_MAX_BUFF)
            attacker_bonuses.append(attacker.bonus + attacker.gear.gearscore + attacker_temp_bonus)
            attacker_rolls.append(attacker.roll_dice(attacker.gear.gearscore + attacker_temp_bonus))
            current_attacker_statistics = charutils.get_character_statistics(attacker)
            current_attacker_statistics.ganks_attempted += 1
            charutils.update_character_statistics(current_attacker_statistics)
            if attacker_rolls[i] >= defender_rolls[i]:
                attacker_wins += 1
            if attacker_rolls[i]-defender_rolls[i] > attacker_rolls[0]-defender_rolls[0]:
                carry_index = i

        xp_reward = int(5000*(sum(defender_rolls)/(sum(attacker_rolls))))
        carry_index = 0

        #handle hp losses during the fights
        defender_hp_loss = 0
        for i, attacker in enumerate(attackers): #each attacker has a separate duel with the defender
            hp_loss = abs(defender_rolls[i] - attacker_rolls[i])
            if defender_rolls[i] > attacker_rolls[i]:
                attacker.current_hp -= hp_loss
                pvp_journal = "".join([pvp_journal, attacker.name])
                pvp_journal = " ".join([pvp_journal, "lost"])
                pvp_journal = " ".join([pvp_journal, str(hp_loss)])
                pvp_journal = " ".join([pvp_journal, "HP. "])
                #handle possible death
                if attacker.current_hp > 0:
                    charutils.update_db_character(charutils.character_to_db_character(attacker))
                elif attacker.current_hp <= 0:
                    discord_id = charutils.get_discord_id_by_character(attacker)
                    permanent_death = attacker.die(defender.id_)
                    if permanent_death:
                        pvp_journal = "".join([pvp_journal, attacker.name])
                        pvp_journal = " ".join([pvp_journal, "died and was reincarnated at level 0! "])
                        event_outcomes.deaths.append(discord_id)
                        defender_statistics.pks += 1
                    else:
                        pvp_journal = "".join([pvp_journal, attacker.name])
                        pvp_journal = " ".join([pvp_journal, "would have died but was saved by the Aegis of Immortality! "])
            else:
                defender_hp_loss += hp_loss
        if defender_hp_loss > 0:
            #defender_hp_loss = defender_hp_loss//len(attackers) #defender toughness scales with number of attackers
            defender.current_hp -= defender_hp_loss
            pvp_journal = " ".join([pvp_journal, defender.name])
            pvp_journal = " ".join([pvp_journal, "was hit for a total of"])
            pvp_journal = " ".join([pvp_journal, str(defender_hp_loss)])
            pvp_journal = " ".join([pvp_journal, "HP in the battle."])
            #handle possible death
            if defender.current_hp > 0:
                charutils.update_db_character(charutils.character_to_db_character(defender))
            elif defender.current_hp <= 0:
                discord_id = charutils.get_discord_id_by_character(defender)
                permanent_death = defender.die(attackers[carry_index].id_)
                if permanent_death:
                    pvp_journal = " ".join([pvp_journal, defender.name])
                    pvp_journal = " ".join([pvp_journal, "died and was reincarnated at level 0!"])
                    event_outcomes.deaths.append(discord_id)
                else:
                    pvp_journal = " ".join([pvp_journal, defender.name])
                    pvp_journal = " ".join([pvp_journal, "would have died but was saved by the Aegis of Immortality!"])

        if not attacker_wins > len(attackers)/2 and defender.current_hp > 0:
            defender_statistics.defences_won += 1
            pvp_journal = "\n".join([pvp_journal, defender.name])
            pvp_journal = " ".join([pvp_journal, "managed to fight off the attackers and gained some experience."])
            defender.current_xp += xp_reward
            charutils.update_db_character(charutils.character_to_db_character(defender))
            pvp_journal = "\n".join([pvp_journal, "XP reward for"])
            pvp_journal = " ".join([pvp_journal, defender.name])
            pvp_journal = ": ".join([pvp_journal, str(xp_reward)])
            pvp_journal = "\n".join([pvp_journal, "**Success!**"])
        else:
            pvp_journal = "\n".join([pvp_journal, "The attackers managed to overwhelm"])
            pvp_journal = " ".join([pvp_journal, defender.name])
            pvp_journal = ",".join([pvp_journal, " which slowed down their progression a bit."])
            for i,attacker in enumerate(attackers):
                current_attacker_statistics = charutils.get_character_statistics(attacker)
                current_attacker_statistics.ganks_won += 1
                charutils.update_character_statistics(current_attacker_statistics)
            if xp_reward >= defender.current_xp:
                xp_reward = defender.current_xp
            defender.current_xp = max(defender.current_xp-xp_reward, 0)
            charutils.update_db_character(charutils.character_to_db_character(defender))
            pvp_journal = "\n".join([pvp_journal, "XP loss for"])
            pvp_journal = " ".join([pvp_journal, defender.name])
            pvp_journal = ": ".join([pvp_journal, str(xp_reward)])
            pvp_journal = "\n".join([pvp_journal, "**Failure!**"])

        charutils.update_character_statistics(defender_statistics)

        defender_table = make_boss_hp_bar(defender.name, defender.current_hp, defender.character_class.max_hp)

        attackers_table_strings = []
        attackers_table_strings.append(["Name"])
        attackers_table_strings.append(["Class"])
        attackers_table_strings.append(["Level"])
        attackers_table_strings.append(["GS"])
        attackers_table_strings.append(["A.Roll"])
        attackers_table_strings.append(["D.Roll"])
        attackers_table_strings.append(["HP"])
        for i,attacker in enumerate(attackers):
            hp_bar = attacker.get_hp_bar()
            defender_raw_roll = defender_rolls[i] - defender_bonuses[i]
            attacker_raw_roll = attacker_rolls[i] - attacker_bonuses[i]
            attackers_table_strings[0].append(attacker.name)
            attackers_table_strings[1].append(attacker.character_class.name)
            attackers_table_strings[2].append(str(attacker.level))
            attackers_table_strings[3].append(str(attacker.gear.gearscore))
            attackers_table_strings[4].append(str(attacker_rolls[i]) + " (" + str(attacker_raw_roll) + "+" + str(attacker_bonuses[i]) + ")")
            attackers_table_strings[5].append(str(defender_rolls[i]) + " (" + str(defender_raw_roll) + "+" + str(defender_bonuses[i]) + ")")
            attackers_table_strings[6].append(hp_bar)

        attackers_table = make_table(attackers_table_strings)
        pvp_journal = "".join([pvp_journal, defender_table])
        pvp_journal = "".join([pvp_journal, "VS"])
        pvp_journal = "".join([pvp_journal, attackers_table])

        event_outcomes.outcome_messages.append(pvp_journal)

        return event_outcomes

    def raid_tomb(self, party, grave, event_outcomes: EventOutcomes=None) -> EventOutcomes:
        gs_reward = max(random.randint(1, grave.gearscore)//len(party), 1)

        gravestone_name = charutils.generate_name_with_generation(charutils.get_character_by_id(grave.character_id))
        if grave.gearscore - gs_reward*len(party) < 0:
            grave.gearscore = 0
        else:
            grave.gearscore -= gs_reward*len(party)
        charutils.update_grave(grave)

        for hero in party:
            hero.gear.unattuned += gs_reward
            charutils.update_db_gear(hero.gear)

        if len(party) == 1:
            class_quest_journal = "**It's free gear estate!**\n"
            class_quest_journal = "".join([class_quest_journal, party[0].name])
            class_quest_journal = " ".join([class_quest_journal, "the"])
            class_quest_journal = " ".join([class_quest_journal, party[0].character_class.name])
        else:
            class_quest_journal = "**Raiders of the lost parts!**\n"
            for hero in party:
                if hero != party[0] and hero != party[-1]:
                    class_quest_journal = "".join([class_quest_journal, ", "])
                elif hero == party[-1]:
                    class_quest_journal = " ".join([class_quest_journal, "and "])
                class_quest_journal = "".join([class_quest_journal, hero.name])
        class_quest_journal = " ".join([class_quest_journal, "decided to visit the grave of"])
        class_quest_journal = " ".join([class_quest_journal, gravestone_name])
        class_quest_journal = ", ".join([class_quest_journal, "which earned them"])
        if len(party) != 1:
            class_quest_journal = " ".join([class_quest_journal, "each"])
        class_quest_journal = " ".join([class_quest_journal, str(gs_reward)])
        class_quest_journal = " ".join([class_quest_journal, "extra gearscore."])

        if event_outcomes:
            event_outcomes.outcome_messages.append(class_quest_journal)
        else:
            event_outcomes = EventOutcomes([class_quest_journal], [])

        return event_outcomes

    def run_class_quest(self, event_outcomes: EventOutcomes=None) -> EventOutcomes:
        """Chooses a class from among classes that have at least one registered character. Generates a party of 1-3 characters of this class and awards free XP to all characters.\n
        If 2 fighters are chosen, one of them will fight the other for experience and honor.\nOne third of the time, if lootable graves (dead characters who had gear) exist, the
        chosen characters will go grave robbing and earn gearscore instead of xp instead.

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

        lootable_graveyard = charutils.get_lootable_graves()
        if lootable_graveyard:
            if randint(1,3) == 3:
                grave = random.choice(lootable_graveyard)
                return self.raid_tomb(chosen_party, grave, event_outcomes)

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
        elif chosen_class.id_ == 7: #warlocks don't get free xp, they recharge their class bonus
            class_quest_journal = "**A profane ritual!**\n"
            if party_size == 1:
                class_quest_journal = "".join([class_quest_journal, chosen_party[0].name])
                class_quest_journal = " ".join([class_quest_journal, "the"])
                class_quest_journal = " ".join([class_quest_journal, chosen_class.name])
            else:
                for hero in chosen_party:
                    if hero != chosen_party[0] and hero != chosen_party[-1]:
                        class_quest_journal = "".join([class_quest_journal, ", "])
                    elif hero == chosen_party[-1]:
                        class_quest_journal = " ".join([class_quest_journal, "and "])
                    class_quest_journal = "".join([class_quest_journal, hero.name])
            class_quest_journal = "".join([class_quest_journal, class_quest_hook])
            class_quest_journal = ", ".join([class_quest_journal, "which recharged their evil magic!"])
            for hero in chosen_party:
                hero.warlock_recharge_bonus()
                statistics = charutils.get_character_statistics(hero)
                statistics.personal_quests += 1
                charutils.update_character_statistics(statistics)
                charutils.update_db_character(charutils.character_to_db_character(hero))
            if event_outcomes:
                event_outcomes.outcome_messages.append(class_quest_journal)
            else:
                event_outcomes = EventOutcomes([class_quest_journal], [])
            return event_outcomes

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
        if party_size == 1 and chosen_party[0].is_thief() and randint(1,2) == 2:
            class_quest_journal = " ".join([class_quest_journal, "By working alone,"])
            class_quest_journal = " ".join([class_quest_journal, chosen_party[0].name])
            class_quest_journal = " ".join([class_quest_journal, "also found"])
            item_name = random.choice(ITEMS)
            if item_name[0] in "aeoiu":
                class_quest_journal = " ".join([class_quest_journal, "an"])
            else:
                class_quest_journal = " ".join([class_quest_journal, "a"])
            class_quest_journal = " ".join([class_quest_journal, item_name])
            class_quest_journal = "".join([class_quest_journal, "!"])
            chosen_party[0].gear.unattuned += 1
            charutils.update_db_gear(chosen_party[0].gear)
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
            resting_character = Character(old_character.id_, old_character.name, old_character.level, old_character.bonus, old_character.current_xp, old_character.current_hp, old_character.character_class, old_character.gear, old_character.aegis, old_character.parent_id)
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