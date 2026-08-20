from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QObject, QUrl, pyqtSignal
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer

from core.playlist import PlayQueue, RepeatMode


class PlayerEngine(QObject):
    position_changed = pyqtSignal(int)
    duration_changed = pyqtSignal(int)
    state_changed = pyqtSignal(str)
    track_changed = pyqtSignal(object)
    error_occurred = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self.audio = QAudioOutput()
        self.player = QMediaPlayer()
        self.player.setAudioOutput(self.audio)
        self.queue = PlayQueue()
        self._duration = 0
        self._seeking = False

        self.player.positionChanged.connect(self._on_position)
        self.player.durationChanged.connect(self._on_duration)
        self.player.playbackStateChanged.connect(self._on_state)
        self.player.mediaStatusChanged.connect(self._on_status)
        self.player.errorOccurred.connect(self._on_error)

    @property
    def is_playing(self) -> bool:
        return self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState

    @property
    def duration(self) -> int:
        return self._duration

    def set_volume(self, value: float) -> None:
        self.audio.setVolume(max(0.0, min(1.0, value)))

    def volume(self) -> float:
        return float(self.audio.volume())

    def set_muted(self, muted: bool) -> None:
        self.audio.setMuted(muted)

    def play_track(self, track: dict) -> None:
        path = Path(track["path"])
        if not path.exists():
            self.error_occurred.emit(f"Missing file: {path.name}")
            return
        self.player.setSource(QUrl.fromLocalFile(str(path)))
        self.player.play()
        self.track_changed.emit(track)

    def play_list(self, tracks: list[dict], start: dict | None = None) -> None:
        if not tracks:
            return
        start_id = start["id"] if start else tracks[0]["id"]
        self.queue.set_tracks(tracks, start_id=start_id)
        current = self.queue.current
        if current:
            self.play_track(current)

    def toggle(self) -> None:
        if self.is_playing:
            self.player.pause()
        elif self.queue.current:
            if self.player.source().isEmpty():
                self.play_track(self.queue.current)
            else:
                self.player.play()

    def pause(self) -> None:
        self.player.pause()

    def stop(self) -> None:
        self.player.stop()

    def next(self, user: bool = True) -> None:
        track = self.queue.next_track(user_initiated=user)
        if track:
            self.play_track(track)

    def previous(self) -> None:
        if self.player.position() > 3500:
            self.seek(0)
            return
        track = self.queue.previous_track()
        if track:
            self.play_track(track)

    def seek(self, ms: int) -> None:
        self.player.setPosition(max(0, ms))

    def seek_relative(self, delta_ms: int) -> None:
        self.seek(self.player.position() + delta_ms)

    def set_shuffle(self, enabled: bool) -> None:
        self.queue.set_shuffle(enabled)

    def cycle_repeat(self) -> RepeatMode:
        return self.queue.cycle_repeat()

    def _on_position(self, pos: int) -> None:
        if not self._seeking:
            self.position_changed.emit(int(pos))

    def _on_duration(self, duration: int) -> None:
        self._duration = int(duration)
        self.duration_changed.emit(self._duration)

    def _on_state(self, state: QMediaPlayer.PlaybackState) -> None:
        mapping = {
            QMediaPlayer.PlaybackState.PlayingState: "playing",
            QMediaPlayer.PlaybackState.PausedState: "paused",
            QMediaPlayer.PlaybackState.StoppedState: "stopped",
        }
        self.state_changed.emit(mapping.get(state, "stopped"))

    def _on_status(self, status: QMediaPlayer.MediaStatus) -> None:
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.finished.emit()
            self.next(user=False)

    def _on_error(self, *_args) -> None:
        err = self.player.errorString() or "Playback error"
        self.error_occurred.emit(err)
