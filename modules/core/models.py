from dataclasses import dataclass
from enum import Enum
from datetime import datetime

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

@dataclass
class Platform:
    id: int
    title: str

@dataclass
class Game:
    id: int
    title: str
    description: str
    cover_url: str
    genres: list[Genre] | None
    release_date: datetime
    platforms: list[Platform] | None
    developer: str
    publisher: str
    rating: float
    price: float
    
    # Timestamps
    created_at: datetime
    updated_at: datetime