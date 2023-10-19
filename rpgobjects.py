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
            tactic
    ):
        self.id_ = id_
        self.name = name
        self.tactic = tactic

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