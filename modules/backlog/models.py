from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from typing import Optional
from modules.base.models import BaseModel


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


@dataclass
class GameMetadata(BaseModel):
    """
    The Game Information can be provided manually or by scraping the web.
    """

    title: str
    description: str = ""
    cover_url: str = ""
    release_date: Optional[datetime] = None
    developer: str = ""
    publisher: str = ""
    avg_completion_time: Optional[float] = None
    genres: list[Genre] = field(default_factory=list)
    platforms: list[Platform] = field(default_factory=list)


@dataclass
class GameBacklogEntry(BaseModel):
    """
    Main class for the game entry.
    """

    meta_data: int
    priority: BacklogPriority
    status: BacklogStatus

    # Relations
    backlog: int  # GameBacklog
    sessions: list[int] = field(default_factory=list)


@dataclass
class GameBacklog(BaseModel):
    """
    Main class for the backlog.
    """

    title: str

    # Relations
    entries: list[int] = field(default_factory=list)  # GameBacklogEntry
