from enum import Enum


class BacklogPriority(Enum):
    P0 = 0
    P1 = 1
    P2 = 2
    P3 = 3


class BacklogStatus(Enum):
    INBOX = "inbox"
    CONSIDERING = "considering"
    TO_BE_PLAYED = "to_be_played"
    PLAYING = "playing"
    ABANDONED = "abandoned"
    FINISHED = "finished"
    PAUSED = "paused"

    @staticmethod
    def from_string(status: str):
        return BacklogStatus[status.upper()]


class Genre(Enum):
    ACTION = "action"
    ADVENTURE = "adventure"
    RPG = "rpg"
    STRATEGY = "strategy"
    PUZZLE = "puzzle"
    SIMULATION = "simulation"
    SPORTS = "sports"
    RACING = "racing"
    FIGHTING = "fighting"
    SHOOTER = "shooter"
    MMO = "mmo"
    MMORPG = "mmorpg"
    INDIE = "indie"
    HORROR = "horror"
    PLATFORMER = "platformer"


class Platform(Enum):
    PC = "pc"
    PLAYSTATION = "playstation"
    XBOX = "xbox"
    NINTENDO = "nintendo"
    MOBILE = "mobile"
    CONSOLE = "console"
    PLAYSTATION_5 = "playstation_5"
