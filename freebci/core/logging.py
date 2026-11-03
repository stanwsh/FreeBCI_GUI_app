"""Thread-safe JSON-lines logging for a recording session.

The GUI already has a legacy text logger.  This module is the durable,
machine-readable log that belongs next to a recording, so support can inspect
one file instead of several dialog-specific logs.
"""

from __future__ import annotations

import json
import os
import threading
import time
from datetime import datetime, timezone
from typing import Optional


class StructuredLogger:
    def __init__(
        self,
        path: str,
        max_bytes: int = 8 * 1024 * 1024,
        backups: int = 2,
    ) -> None:
        self.path = path
        self.max_bytes = max(1024, int(max_bytes))
        self.backups = max(1, int(backups))
        self._lock = threading.Lock()
        self._handle = None
        self._closed = False
        directory = os.path.dirname(os.path.abspath(path))
        os.makedirs(directory, exist_ok=True)
        self._handle = open(path, "a", encoding="utf-8", newline="\n")

    def log(self, level: str, event: str, message: str = "", **fields) -> dict:
        if self._closed:
            raise RuntimeError("logger is closed")
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "time_ns": time.time_ns(),
            "level": str(level).lower(),
            "event": str(event),
            "message": str(message),
        }
        for key, value in fields.items():
            if key in record:
                continue
            record[key] = value
        line = json.dumps(record, sort_keys=True, default=str) + "\n"
        with self._lock:
            self._rotate_if_needed(len(line.encode("utf-8")))
            self._handle.write(line)
            self._handle.flush()
        return record

    def close(self) -> None:
        with self._lock:
            if self._closed:
                return
            self._closed = True
            try:
                self._handle.flush()
                os.fsync(self._handle.fileno())
            finally:
                self._handle.close()
                self._handle = None

    def _rotate_if_needed(self, incoming: int) -> None:
        if self._handle.tell() + incoming <= self.max_bytes:
            return
        self._handle.close()
        for index in range(self.backups, 0, -1):
            source = self.path if index == 1 else "%s.%d" % (self.path, index - 1)
            target = "%s.%d" % (self.path, index)
            if os.path.exists(source):
                os.replace(source, target)
        self._handle = open(self.path, "w", encoding="utf-8", newline="\n")
