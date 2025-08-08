from smolorm.sqlmodel import (
    DatetimeField,
    EnumField,
    IntField,
    ListField,
    RealField,
    SqlModel,
    TextField,
)
from datetime import datetime

from modules.enums.enums import BacklogPriority, BacklogStatus, Genre


class GameMetadataModel(SqlModel):
    table_name: str = "game_metadatas"
    title = TextField(default_value="")
    description = TextField(default_value="")
    cover_url = TextField(default_value="")
    release_date = DatetimeField(default_value=datetime(1, 1, 1))
    developer = TextField(default_value="")
    publisher = TextField(default_value="")
    avg_completion_time = RealField(default_value=0.0)
    genres = EnumField(default_value=Genre.ADVENTURE)
    platforms = ListField(default_value=[])


class GameBacklogEntryModel(SqlModel):
    table_name: str = "game_backlog_entries"
    meta_data = IntField(default_value=0)
    priority = EnumField(default_value=BacklogPriority.P0)
    status = EnumField(default_value=BacklogStatus.INBOX)

    # Relations
    backlog = IntField(default_value=0)  # GameBacklog


class GameBacklogModel(SqlModel):
    table_name: str = "game_backlogs"
    title = TextField(default_value="")

    # Relations
    entries = ListField(default_value=[])
