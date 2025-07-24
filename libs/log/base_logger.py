from abc import ABC, abstractmethod
import enum


class LogLevel(enum.Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class AbstractLogger(ABC):
    def __init__(self, name: str = "Logger"):
        self.name = name

    @abstractmethod
    def _get_timestamp(self) -> str:
        raise NotImplementedError("")

    @abstractmethod
    def _log(self, level: LogLevel, message: str) -> None:
        """Log a message with the given level."""
        raise NotImplementedError("")

    def debug(self, message: str) -> None:
        self._log(LogLevel.DEBUG, message)

    def info(self, message: str) -> None:
        self._log(LogLevel.INFO, message)

    def warning(self, message: str) -> None:
        self._log(LogLevel.WARNING, message)

    def error(self, message: str) -> None:
        self._log(LogLevel.ERROR, message)

    def critical(self, message: str) -> None:
        self._log(LogLevel.CRITICAL, message)
