"""
In-memory log collector za spremljanje napak in dogodkov.

Hrani zadnjih N log vnosov v ring buffer-ju.
"""

import logging
import time
import threading
from collections import deque
from datetime import datetime


class LogEntry:
    __slots__ = ("timestamp", "level", "logger_name", "message", "module", "funcName", "lineno", "exc_text")

    def __init__(self, record: logging.LogRecord):
        self.timestamp = datetime.fromtimestamp(record.created).isoformat()
        self.level = record.levelname
        self.logger_name = record.name
        self.message = record.getMessage()
        self.module = record.module
        self.funcName = record.funcName
        self.lineno = record.lineno
        self.exc_text = record.exc_text or ""

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "level": self.level,
            "logger": self.logger_name,
            "message": self.message,
            "module": self.module,
            "function": self.funcName,
            "line": self.lineno,
            "exception": self.exc_text,
        }


class MemoryLogHandler(logging.Handler):
    """Handler ki shranjuje loge v ring buffer."""

    def __init__(self, max_entries: int = 500):
        super().__init__()
        self._buffer: deque[LogEntry] = deque(maxlen=max_entries)
        self._error_buffer: deque[LogEntry] = deque(maxlen=200)
        self._lock = threading.Lock()
        self._counts = {"DEBUG": 0, "INFO": 0, "WARNING": 0, "ERROR": 0, "CRITICAL": 0}

    def emit(self, record: logging.LogRecord):
        entry = LogEntry(record)
        with self._lock:
            self._buffer.append(entry)
            self._counts[record.levelname] = self._counts.get(record.levelname, 0) + 1
            if record.levelno >= logging.WARNING:
                self._error_buffer.append(entry)

    def get_logs(self, level: str = None, limit: int = 100, search: str = None) -> list[dict]:
        with self._lock:
            entries = list(self._buffer)
        if level:
            level_upper = level.upper()
            level_no = getattr(logging, level_upper, logging.DEBUG)
            entries = [e for e in entries if getattr(logging, e.level, 0) >= level_no]
        if search:
            search_lower = search.lower()
            entries = [e for e in entries if search_lower in e.message.lower() or search_lower in e.exc_text.lower()]
        return [e.to_dict() for e in entries[-limit:]]

    def get_errors(self, limit: int = 50) -> list[dict]:
        with self._lock:
            entries = list(self._error_buffer)
        return [e.to_dict() for e in entries[-limit:]]

    def get_counts(self) -> dict:
        with self._lock:
            return dict(self._counts)


# Singleton
_handler: MemoryLogHandler | None = None


def setup_log_collector() -> MemoryLogHandler:
    """Nastavi log collector na root logger."""
    global _handler
    if _handler is None:
        _handler = MemoryLogHandler(max_entries=500)
        _handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
        _handler.setFormatter(formatter)

        root = logging.getLogger()
        root.addHandler(_handler)

        # Ujemi tudi uvicorn in sqlalchemy
        for name in ("uvicorn", "uvicorn.error", "uvicorn.access", "sqlalchemy.engine", "app"):
            logger = logging.getLogger(name)
            logger.addHandler(_handler)

    return _handler


def get_log_collector() -> MemoryLogHandler:
    global _handler
    if _handler is None:
        return setup_log_collector()
    return _handler
