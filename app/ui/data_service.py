from dataclasses import dataclass
from app.service import backlog_service, play_session_service
from libs.fmt.datetime_formatter import DateTimeFormatter


@dataclass()
class PlaySessionData:
    id = "0"
    title = ""
    start = ""
    end = ""
    playtime = ""


@dataclass()
class PlayStatisticsData:
    id = "0"
    title = ""
    playtime = ""


class DataService:
    @staticmethod
    def get_play_sessions_data() -> list[PlaySessionData]:
        sessions = []
        result = play_session_service.get_all_sessions()

        for s in result:
            data = PlaySessionData()
            data.id = str(s.id)
            data.start = DateTimeFormatter.fmt(s.session_start)
            data.end = DateTimeFormatter.fmt(s.session_end) if s.session_end else ""
            data.playtime = DateTimeFormatter.fmt_playtime(s.time_played)

            entry = backlog_service.get_entry(s.backlog_entry)

            if not entry:
                raise ValueError(f"Entry {s.backlog_entry} not found")

            meta_data = backlog_service.get_game_metadata(entry.meta_data)

            if not meta_data:
                raise ValueError(f"Metadata {entry.meta_data} not found")

            data.title = meta_data.title
            sessions.append(data)

        return sessions

    @staticmethod
    def get_play_statitics() -> list[PlaySessionData]:
        stats = []

        entries = play_session_service.get_entries_with_playtime()

        for id, time_played in entries.items():
            data = PlayStatisticsData()
            data.id = str(id)
            data.playtime = DateTimeFormatter.fmt_playtime(time_played)

            entry = backlog_service.get_entry(id)

            if not entry:
                raise ValueError(f"Entry {id} not found")

            meta_data = backlog_service.get_game_metadata(entry.meta_data)

            if not meta_data:
                raise ValueError(f"Metadata {entry.meta_data} not found")

            data.title = meta_data.title
            stats.append(data)

        return stats
