from libs.log.base_logger import AbstractLogger, LogLevel
from datetime import datetime


class FileLogger(AbstractLogger):
    def __init__(self, name: str = "FileLogger", filepath: str = "log.txt"):
        super().__init__(name)
        self.filepath = filepath
        self._create_file()

    def _create_file(self):
        with open(self.filepath, "w") as file:
            file.write("")

    def _get_timestamp(self) -> str:
        return datetime.now().isoformat(timespec="seconds")

    def _log(self, level: LogLevel, message: str) -> None:
        timestamp = self._get_timestamp()
        log_str = f"[{timestamp}] [{self.name}] [{level.value}] {message}"

        with open(self.filepath, "a") as file:
            file.write(log_str + "\n")
