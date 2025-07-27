from datetime import datetime


class DateTimeFormatter:
    FMT_STR = "%d/%m/%Y %H:%M:%S"
    PLAY_TIME_STR = "%H:%M:%S"

    @staticmethod
    def fmt(date_time: datetime, formatter_str: str = FMT_STR) -> str:
        return date_time.strftime(formatter_str)

    @staticmethod
    def from_seconds(time: float) -> datetime:
        return datetime.fromtimestamp(time)

    @staticmethod
    def fmt_playtime(time: float) -> str:
        return DateTimeFormatter.fmt(
            DateTimeFormatter.from_seconds(time), DateTimeFormatter.PLAY_TIME_STR
        )
