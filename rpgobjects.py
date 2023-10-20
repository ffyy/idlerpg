from random import randint

class Gear:
    def __init__(
            self,
            id_,
            gearscore
            ):
        self.id_ = id_
        self.gearscore = gearscore

class CharacterClass:
    def __init__(
            self,
            id_,
            name,
            dice,
            die_size,
            bonus
    ):
        self.id_ = id_
        self.name = name
        self.dice = dice
        self.die_size = die_size
        self.bonus = bonus

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
        