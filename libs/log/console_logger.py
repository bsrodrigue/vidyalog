from libs.log.base_logger import AbstractLogger, LogLevel
from datetime import datetime


class ConsoleLogger(AbstractLogger):
    def log(self, level: LogLevel, message: str) -> None:
        timestamp = datetime.now().isoformat(timespec="seconds")
        print(f"[{timestamp}] [{self.name}] [{level.value}] {message}")
