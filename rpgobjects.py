from random import randint

class Gear:
    def __init__(
            self,
            id_,
            gearscore,
            unattuned
            ):
        self.id_ = id_
        self.gearscore = gearscore
        self.unattuned = unattuned

class CharacterClass:
    def __init__(
            self,
            id_,
            name,
            dice,
            die_size,
            bonus,
            xp_per_level,
            description
    ):
        self.id_ = id_
        self.name = name
        self.dice = dice
        self.die_size = die_size
        self.bonus = bonus
        self.xp_per_level = xp_per_level
        self.description = description

class CharacterDB:
    def __init__(
            self,
            id_,
            name,
            level,
            current_xp,
            class_id,
            gear_id
            ):
        self.id_ = id_
        self.name = name
        self.level = level
        self.current_xp = current_xp
        self.class_id = class_id
        self.gear_id = gear_id

class Character:
    def __init__(
            self,
            id_,
            name,
            level,
            current_xp,
            character_class: CharacterClass,
            gear: Gear,
            ):
        self.id_ = id_
        self.name = name
        self.level = level
        self.current_xp = current_xp
        self.character_class = character_class
        self.gear = gear

    def roll_dice(self):
        result = self.character_class.bonus
        for die in range(self.character_class.dice):
            this_roll = randint(1, self.character_class.die_size)
            result += this_roll
        return result

    def roll_for_passive_xp(self) -> int:
        BASE_XP = 3600 #1 xp per second with default timescale 60
        xp_multiplier = self.roll_dice()
        xp = int(BASE_XP * xp_multiplier / 100)
        return xp

    def take_long_rest(self):
        rested_character = Character(self.id_, self.name, self.level, self.current_xp, self.character_class, self.gear)
        while rested_character.current_xp >= self.character_class.xp_per_level:
            rested_character.level += 1
            rested_character.current_xp = max(rested_character.current_xp - self.character_class.xp_per_level, 0)
        rested_character.gear = Gear(self.gear.id_, self.gear.gearscore, self.gear.unattuned)
        rested_character.gear.gearscore += self.gear.unattuned
        rested_character.gear.unattuned = 0
        return rested_character

class Player:
    def __init__(
            self,
            id_,
            discord_id,
            character_id
    ):
        self.id_ = id_
        self.discord_id = discord_id
        self.character.id = character_id

class Quest:
    def __init__(
            self,
            quest_type,
            party: list[Character],
            party_rolls: list[int],
            quest_difficulty,
            quest_journal,
            outcome):
        self.quest_type = quest_type
        self.party = party
        self.party_rolls = party_rolls
        self.quest_difficulty = quest_difficulty
        self.quest_journal = quest_journal
        self.outcome = outcome

class DayReport:
    def __init__(
            self,
            character_name,
            level_result,
            gearscore_result,
            xp_result
    ):
        self.character_name = character_name
        self.level_result = level_result
        self.gearscore_result = gearscore_result
        self.xp_result = xp_result

class LeaderboardEntry:
    def __init__(
            self,
            character_name,
            level,
            gearscore,
            player_id
    ):
        self.character_name = character_name
        self.level = level
        self.gearscore = gearscore
        self.player_id = player_id

class CharacterStatistics:
    def __init__(
            self,
            character_id,
            quests_attempted,
            quests_won,
            ganks_attempted,
            ganks_won,
            defences_attempted,
            defences_won
    ):
        self.character_id = character_id
        self.quests_attempted = quests_attempted
        self.quests_won = quests_won
        self.ganks_attempted = ganks_attempted
        self.ganks_won = ganks_won
        self.defences_attempted = defences_attempted
        self.defences_won = defences_won