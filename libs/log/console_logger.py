from libs.log.base_logger import AbstractLogger, LogLevel
from datetime import datetime


class ConsoleLogger(AbstractLogger):
    def _get_timestamp(self) -> str:
        return datetime.now().isoformat(timespec="seconds")

    def _log(self, level: LogLevel, message: str) -> None:
        timestamp = self._get_timestamp()
        print(f"[{timestamp}] [{self.name}] [{level.value}] {message}")
