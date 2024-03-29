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

class Grave:
    def __init__(
            self,
            character_id,
            gearscore
            ):
        self.character_id = character_id
        self.gearscore = gearscore

    def create_grave(self):
        from charutils import create_grave as db_create_grave
        db_create_grave(self.character_id, self.gearscore)

class CharacterClass:
    def __init__(
            self,
            id_,
            name,
            dice,
            die_size,
            bonus,
            xp_per_level,
            max_hp,
            description
    ):
        self.id_ = id_
        self.name = name
        self.dice = dice
        self.die_size = die_size
        self.bonus = bonus
        self.xp_per_level = xp_per_level
        self.max_hp = max_hp
        self.description = description

class CharacterDB:
    def __init__(
            self,
            id_,
            name,
            level,
            bonus,
            current_xp,
            current_hp,
            class_id,
            gear_id,
            aegis,
            parent_id
            ):
        self.id_ = id_
        self.name = name
        self.level = level
        self.bonus = bonus
        self.current_xp = current_xp
        self.current_hp = current_hp
        self.class_id = class_id
        self.gear_id = gear_id
        self.aegis = aegis
        self.parent_id = parent_id

class Character:
    def __init__(
            self,
            id_,
            name,
            level,
            bonus,
            current_xp,
            current_hp,
            character_class: CharacterClass,
            gear: Gear,
            aegis,
            parent_id
            ):
        self.id_ = id_
        self.name = name
        self.level = level
        self.bonus = bonus
        self.current_xp = current_xp
        self.current_hp = current_hp
        self.character_class = character_class
        self.gear = gear
        self.aegis = aegis
        self.parent_id = parent_id

    def bury(self):
        grave = Grave(self.id_, self.gear.gearscore)
        print("grave object created")
        grave.create_grave()

    def die(self, reason=-1) -> bool:
        if self.aegis == 1:
            from charutils import update_db_character
            self.aegis = 0
            self.current_hp = self.character_class.max_hp
            update_db_character(self)
            return False
        else:
            from charutils import reincarnate
            self.current_hp = 0
            if reason <= 0 and self.gear.gearscore > 0:
                self.bury()
            reincarnate(self, reason)
            return True

    def is_thief(self) -> bool:
        if self.character_class.id_ == 1:
            return True
        else:
            return False

    def is_fighter(self) -> bool:
        if self.character_class.id_ == 2:
            return True
        else:
            return False

    def is_hobbit(self) -> bool:
        if self.character_class.id_ == 3:
            return True
        else:
            return False

    def is_elf(self) -> bool:
        if self.character_class.id_ == 4:
            return True
        else:
            return False

    def is_magic_user(self) -> bool:
        if self.character_class.id_ == 5:
            return True
        else:
            return False

    def is_cleric(self) -> bool:
        if self.character_class.id_ == 6:
            return True
        else:
            return False

    def is_warlock(self) -> bool:
        if self.character_class.id_ == 7:
            return True
        else:
            return False

    def is_hunter(self) -> bool:
        if self.character_class.id_ == 8:
            return True
        else:
            return False

    def get_hp_bar(self) -> str:
        from charutils import make_hp_bar
        AEGIS_BOOKENDS = "{}"
        if self.aegis > 0:
            hp_bar = make_hp_bar(self.current_hp, self.character_class.max_hp, bookends=AEGIS_BOOKENDS)
        else:
            hp_bar = make_hp_bar(self.current_hp, self.character_class.max_hp)
        return hp_bar

    def roll_dice(self, temporary_bonus=0) -> int:
        """Roll dice based on the class and bonuses of the character. In case of Warlock, the bonus is reduced after the dice are rolled.
        Because of this, if it is necessary to know the bonus during the rolls (for outcome tables), the character's bonus should be checked BEFORE rolling.

        Arguments:
            temporary_bonus: integer which is added to this roll
        """
        if self.is_cleric(): return self.cleric_roll_dice(temporary_bonus)
        if self.is_warlock(): return self.warlock_roll_dice(temporary_bonus)
        result = self.bonus + temporary_bonus
        for die in range(self.character_class.dice):
            this_roll = randint(1, self.character_class.die_size)
            result += this_roll
        return result

    def cleric_roll_dice(self, temporary_bonus=0):
        from charutils import update_hp
        hp_gain = randint(1,8) + 4
        self.current_hp = min(self.current_hp+hp_gain, self.character_class.max_hp)
        update_hp(self)
        result = self.bonus + temporary_bonus
        for die in range(self.character_class.dice):
            this_roll = randint(1, self.character_class.die_size)
            result += this_roll
        return result

    def warlock_roll_dice(self, temporary_bonus=0) -> int:
        from charutils import update_bonus
        result = self.bonus + temporary_bonus
        for die in range(self.character_class.dice):
            this_roll = randint(1, self.character_class.die_size)
            result += this_roll
        self.bonus //= 2
        update_bonus(self)
        return result

    def warlock_recharge_bonus(self):
        from charutils import update_bonus
        self.bonus = self.character_class.bonus
        update_bonus(self)

    def roll_for_passive_xp(self) -> int:
        BASE_XP = 7200 #2 xp per second with default timescale 60
        xp_multiplier = self.roll_dice()
        xp = int(BASE_XP * xp_multiplier / 100)
        return xp

    def take_long_rest(self):
        rested_character = Character(self.id_, self.name, self.level, self.bonus, self.current_xp, self.current_hp, self.character_class, self.gear, self.aegis, self.parent_id)
        if self.is_warlock() and self.bonus < 10:
            self.warlock_recharge_bonus()
        while rested_character.current_xp >= self.character_class.xp_per_level:
            rested_character.level += 1
            rested_character.current_xp = max(rested_character.current_xp - self.character_class.xp_per_level, 0)
            rested_character.current_hp = rested_character.character_class.max_hp
        rested_character.gear = Gear(self.gear.id_, self.gear.gearscore, self.gear.unattuned)
        if rested_character.gear.gearscore <= 50:
            rested_character.gear.gearscore += self.gear.unattuned
            rested_character.gear.unattuned = 0
        else:
            rested_character.level += self.gear.unattuned
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

class DeadCharacter:
    def __init__(
            self,
            id_,
            name,
            level,
            class_id,
            gearscore,
            player_id,
            life_length,
            death_reason,
            parent_id
    ):
        self.id_ = id_
        self.name = name
        self.level = level
        self.class_id = class_id
        self.gearscore = gearscore
        self.player_id = player_id
        self.life_length = life_length
        self.death_reason = death_reason
        self.parent_id = parent_id

class Quest:
    def __init__(
            self,
            quest_type,
            party: list[Character],
            party_rolls: list[int],
            party_bonuses: list[int],
            death_notices: list[int],
            quest_difficulty,
            quest_journal,
            outcome):
        self.quest_type = quest_type
        self.party = party
        self.party_rolls = party_rolls
        self.party_bonuses = party_bonuses
        self.death_notices = death_notices
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

class RaidBoss:
    def __init__(
            self,
            id_,
            name,
            current_hp,
            max_hp,
            boss_type,
            target_level
    ):
        self.id_ = id_
        self.name = name
        self.current_hp = current_hp
        self.max_hp = max_hp
        self.boss_type = boss_type
        self.target_level = target_level

    def calculate_damage_ratio(self, hero: Character) -> int:
        """If the character's level matches the boss target level, they take 100% damage from the boss. If the level is less than half the target level, they take double damage.
        If the level is double the boss target level, they take half damage.
        """
        if hero.level == 0:
            return 2
        ratio = self.target_level / hero.level
        if ratio < 0.5:
            ratio = 0.5
        elif ratio > 2:
            ratio = 2
        return ratio

class CharacterStatistics:
    def __init__(
            self,
            character_id,
            quests_attempted,
            quests_won,
            ganks_attempted,
            ganks_won,
            defences_attempted,
            defences_won,
            pks,
            personal_quests,
            create_timestamp,
            delete_timestamp
    ):
        self.character_id = character_id
        self.quests_attempted = quests_attempted
        self.quests_won = quests_won
        self.ganks_attempted = ganks_attempted
        self.ganks_won = ganks_won
        self.defences_attempted = defences_attempted
        self.defences_won = defences_won
        self.pks = pks
        self.personal_quests = personal_quests
        self.create_timestamp = create_timestamp
        self.delete_timestamp = delete_timestamp