from __future__ import annotations

import random
from enum import Enum

from PyQt6.QtCore import QObject, pyqtSignal


class RepeatMode(str, Enum):
    OFF = "off"
    ALL = "all"
    ONE = "one"


class PlayQueue(QObject):
    changed = pyqtSignal()
    index_changed = pyqtSignal(int)

    def __init__(self) -> None:
        super().__init__()
        self._tracks: list[dict] = []
        self._order: list[int] = []
        self._cursor = -1
        self.shuffle = False
        self.repeat = RepeatMode.OFF

    @property
    def tracks(self) -> list[dict]:
        return list(self._tracks)

    @property
    def current(self) -> dict | None:
        if 0 <= self._cursor < len(self._order) and self._order:
            return self._tracks[self._order[self._cursor]]
        return None

    @property
    def current_index(self) -> int:
        return self._cursor

    def __len__(self) -> int:
        return len(self._tracks)

    def set_tracks(self, tracks: list[dict], start_id: int | None = None) -> None:
        self._tracks = list(tracks)
        self._rebuild_order(keep_id=start_id)
        if start_id is not None:
            for i, idx in enumerate(self._order):
                if self._tracks[idx].get("id") == start_id:
                    self._cursor = i
                    break
            else:
                self._cursor = 0 if self._order else -1
        else:
            self._cursor = 0 if self._order else -1
        self.changed.emit()
        self.index_changed.emit(self._cursor)

    def replace_queue(self, tracks: list[dict]) -> None:
        self.set_tracks(tracks, start_id=tracks[0]["id"] if tracks else None)

    def enqueue(self, track: dict) -> None:
        self._tracks.append(track)
        self._order.append(len(self._tracks) - 1)
        if self._cursor < 0:
            self._cursor = 0
        self.changed.emit()

    def enqueue_next(self, track: dict) -> None:
        self._tracks.append(track)
        insert_at = self._cursor + 1
        self._order.insert(insert_at, len(self._tracks) - 1)
        if self._cursor < 0:
            self._cursor = 0
        self.changed.emit()

    def remove_at(self, queue_index: int) -> None:
        if not (0 <= queue_index < len(self._order)):
            return
        track_index = self._order.pop(queue_index)
        self._tracks.pop(track_index)
        self._order = [i if i < track_index else i - 1 for i in self._order]
        if queue_index < self._cursor:
            self._cursor -= 1
        elif queue_index == self._cursor:
            if self._cursor >= len(self._order):
                self._cursor = len(self._order) - 1
        self.changed.emit()
        self.index_changed.emit(self._cursor)

    def jump(self, queue_index: int) -> dict | None:
        if not (0 <= queue_index < len(self._order)):
            return None
        self._cursor = queue_index
        self.index_changed.emit(self._cursor)
        return self.current

    def next_track(self, user_initiated: bool = False) -> dict | None:
        if not self._order:
            return None
        if self.repeat == RepeatMode.ONE and not user_initiated:
            return self.current
        nxt = self._cursor + 1
        if nxt >= len(self._order):
            if self.repeat == RepeatMode.ALL or user_initiated:
                self._cursor = 0
                self.index_changed.emit(self._cursor)
                return self.current
            return None
        self._cursor = nxt
        self.index_changed.emit(self._cursor)
        return self.current

    def previous_track(self) -> dict | None:
        if not self._order:
            return None
        prev = self._cursor - 1
        if prev < 0:
            if self.repeat == RepeatMode.ALL:
                self._cursor = len(self._order) - 1
            else:
                self._cursor = 0
        else:
            self._cursor = prev
        self.index_changed.emit(self._cursor)
        return self.current

    def set_shuffle(self, enabled: bool) -> None:
        current_id = self.current.get("id") if self.current else None
        self.shuffle = enabled
        self._rebuild_order(keep_id=current_id)
        self.changed.emit()
        self.index_changed.emit(self._cursor)

    def cycle_repeat(self) -> RepeatMode:
        order = [RepeatMode.OFF, RepeatMode.ALL, RepeatMode.ONE]
        self.repeat = order[(order.index(self.repeat) + 1) % 3]
        return self.repeat

    def _rebuild_order(self, keep_id: int | None) -> None:
        n = len(self._tracks)
        order = list(range(n))
        if self.shuffle and n > 1:
            random.shuffle(order)
            if keep_id is not None:
                for i, idx in enumerate(order):
                    if self._tracks[idx].get("id") == keep_id:
                        order[0], order[i] = order[i], order[0]
                        break
        self._order = order
        self._cursor = 0 if order else -1
        if keep_id is not None:
            for i, idx in enumerate(self._order):
                if self._tracks[idx].get("id") == keep_id:
                    self._cursor = i
                    break

    def ordered_tracks(self) -> list[dict]:
        return [self._tracks[i] for i in self._order]
