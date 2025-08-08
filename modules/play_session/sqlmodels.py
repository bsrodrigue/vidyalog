from datetime import datetime

from smolorm.sqlmodel import DatetimeField, IntField, SqlModel


class PlaySessionModel(SqlModel):
    table_name: str = "play_sessions"
    session_start = DatetimeField(default_value=datetime.now())
    session_end = DatetimeField(required=False)
    backlog_entry = IntField(default_value=0)
