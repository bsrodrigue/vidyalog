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
    def log(self, level: LogLevel, message: str) -> None:
        """Log a message with the given level."""
        pass

    def debug(self, message: str) -> None:
        self.log(LogLevel.DEBUG, message)

    def info(self, message: str) -> None:
        self.log(LogLevel.INFO, message)

    def warning(self, message: str) -> None:
        self.log(LogLevel.WARNING, message)

    def error(self, message: str) -> None:
        self.log(LogLevel.ERROR, message)

    def critical(self, message: str) -> None:
        self.log(LogLevel.CRITICAL, message)
