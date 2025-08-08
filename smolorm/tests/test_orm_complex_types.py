from datetime import datetime
import pytest
import json
from smolorm.expressions import col
from smolorm.sqlmodel import (
    DatetimeField,
    EnumField,
    IntField,
    ListField,
    RealField,
    SqlModel,
    TextField,
)
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
    SWITCH = "switch"


class GameMetadataModel(SqlModel):
    table_name: str = "test_game_metadatas"
    title = TextField(default_value="")
    description = TextField(default_value="")
    cover_url = TextField(default_value="")
    release_date = DatetimeField(default_value=datetime(1, 1, 1))
    developer = TextField(default_value="")
    publisher = TextField(default_value="")
    avg_completion_time = RealField(default_value=0.0)
    genres = ListField(default_value=[])
    platforms = ListField(default_value=[])


class GameBacklogEntryModel(SqlModel):
    table_name: str = "test_game_backlog_entries"
    meta_data = IntField(default_value=0)
    priority = EnumField(default_value=BacklogPriority.P3)
    status = EnumField(default_value=BacklogStatus.INBOX)

    # Relations
    backlog = IntField(default_value=0)


class GameBacklogModel(SqlModel):
    table_name: str = "test_game_backlogs"
    title = TextField(default_value="")

    # Relations
    entries = ListField(default_value=[])


class UserModel(SqlModel):
    table_name: str = "test_users"
    age = IntField(default_value=0)
    username = TextField(default_value="")
    password = TextField(default_value="password")


@pytest.fixture(autouse=True)
def setup_models():
    for model in [
        UserModel,
        GameMetadataModel,
        GameBacklogEntryModel,
        GameBacklogModel,
    ]:
        model.drop()
        model.__init_subclass__()
    yield
    for model in [
        UserModel,
        GameMetadataModel,
        GameBacklogEntryModel,
        GameBacklogModel,
    ]:
        model.drop()


def test_user_create_and_defaults():
    UserModel.create({"username": "alice"})
    result = UserModel.select().where(col("username") == "alice").run()
    assert result[0]["age"] == 0
    assert result[0]["username"] == "alice"
    assert result[0]["password"] == "password"


def test_game_metadata_serialized_lists_and_date():
    GameMetadataModel.create(
        {
            "title": "Test Game",
            "genres": json.dumps([Genre.RPG.value, Genre.ACTION.value]),
            "platforms": json.dumps([Platform.SWITCH.value, Platform.PC.value]),
        }
    )

    row = GameMetadataModel.select().where(col("title") == "Test Game").run()[0]
    assert json.loads(row["genres"]) == [Genre.RPG.value, Genre.ACTION.value]
    assert json.loads(row["platforms"]) == [Platform.SWITCH.value, Platform.PC.value]
    assert row["release_date"] == "0001-01-01T00:00:00"


def test_backlog_entry_enum_defaults():
    GameBacklogEntryModel.create({"meta_data": 0, "backlog": 0})
    row = GameBacklogEntryModel.select().run()[0]
    assert row["priority"] == str(BacklogPriority.P3.value)
    assert row["status"] == BacklogStatus.INBOX.value


def test_backlog_model_with_entries():
    GameBacklogModel.create({"title": "My backlog", "entries": json.dumps([1, 2, 3])})

    row = GameBacklogModel.select().where(col("title") == "My backlog").run()[0]
    assert json.loads(row["entries"]) == [1, 2, 3]


def test_chained_create_update_delete():
    GameBacklogModel.create({"title": "Temp Backlog", "entries": json.dumps([])})
    GameBacklogModel.update({"title": "Updated"}).where(
        col("title") == "Temp Backlog"
    ).run()
    row = GameBacklogModel.select().where(col("title") == "Updated").run()[0]
    assert row["entries"] == "[]"

    GameBacklogModel.delete().where(col("title") == "Updated").run()
    assert GameBacklogModel.select().where(col("title") == "Updated").run() == []


def test_select_no_matches_returns_empty():
    result = GameMetadataModel.select().where(col("title") == "Unknown Game").run()
    assert result == []
