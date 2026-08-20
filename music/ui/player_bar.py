from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QSlider, QVBoxLayout, QWidget

from core.playlist import RepeatMode
from ui.components import CoverLabel, GlassPanel, IconButton, SeekSlider, format_ms
from ui.styles import Theme


class PlayerBar(GlassPanel):
    play_toggled = pyqtSignal()
    next_clicked = pyqtSignal()
    prev_clicked = pyqtSignal()
    shuffle_toggled = pyqtSignal(bool)
    repeat_cycled = pyqtSignal()
    seek_ratio = pyqtSignal(float)
    volume_changed = pyqtSignal(float)
    queue_clicked = pyqtSignal()
    favorite_clicked = pyqtSignal()

    def __init__(self, theme: Theme, parent=None) -> None:
        super().__init__(theme, 20, parent)
        self.setFixedHeight(int(92 * theme.scale))
        root = QHBoxLayout(self)
        root.setContentsMargins(16, 10, 16, 10)
        root.setSpacing(16)

        self.cover = CoverLabel(64, 10)
        info = QVBoxLayout()
        info.setSpacing(2)
        self.title = QLabel("Not playing")
        self.title.setObjectName("title")
        self.artist = QLabel("Select a song to begin")
        self.artist.setObjectName("muted")
        info.addWidget(self.title)
        info.addWidget(self.artist)
        left = QHBoxLayout()
        left.addWidget(self.cover)
        left.addLayout(info)
        self.fav = IconButton("heart", theme, 34)
        self.fav.clicked.connect(self.favorite_clicked.emit)
        left.addWidget(self.fav)
        wrap_left = QWidget()
        wrap_left.setLayout(left)
        wrap_left.setFixedWidth(int(320 * theme.scale))
        root.addWidget(wrap_left)

        center = QVBoxLayout()
        center.setSpacing(6)
        controls = QHBoxLayout()
        controls.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.shuffle = IconButton("shuffle", theme, 34)
        self.shuffle.setCheckable(True)
        self.prev = IconButton("prev", theme, 36)
        self.play = IconButton("play", theme, 46, accent=True)
        self.next = IconButton("next", theme, 36)
        self.repeat = IconButton("repeat", theme, 34)
        self.shuffle.clicked.connect(lambda: self.shuffle_toggled.emit(self.shuffle.isChecked()))
        self.prev.clicked.connect(self.prev_clicked.emit)
        self.play.clicked.connect(self.play_toggled.emit)
        self.next.clicked.connect(self.next_clicked.emit)
        self.repeat.clicked.connect(self.repeat_cycled.emit)
        for w in (self.shuffle, self.prev, self.play, self.next, self.repeat):
            controls.addWidget(w)
        times = QHBoxLayout()
        self.elapsed = QLabel("0:00")
        self.elapsed.setObjectName("muted")
        self.slider = SeekSlider()
        self.slider.seek_requested.connect(self.seek_ratio.emit)
        self.total = QLabel("0:00")
        self.total.setObjectName("muted")
        times.addWidget(self.elapsed)
        times.addWidget(self.slider, 1)
        times.addWidget(self.total)
        center.addLayout(controls)
        center.addLayout(times)
        root.addLayout(center, 1)

        right = QHBoxLayout()
        self.vol_icon = IconButton("volume", theme, 32)
        self.volume = QSlider(Qt.Orientation.Horizontal)
        self.volume.setRange(0, 100)
        self.volume.setFixedWidth(110)
        self.volume.valueChanged.connect(lambda v: self.volume_changed.emit(v / 100.0))
        self.queue_btn = IconButton("queue", theme, 34)
        self.queue_btn.clicked.connect(self.queue_clicked.emit)
        right.addWidget(self.vol_icon)
        right.addWidget(self.volume)
        right.addWidget(self.queue_btn)
        wrap_right = QWidget()
        wrap_right.setLayout(right)
        wrap_right.setFixedWidth(200)
        root.addWidget(wrap_right)

        self._duration = 0

    def set_track(self, track: dict | None, theme: Theme) -> None:
        if not track:
            self.title.setText("Not playing")
            self.artist.setText("Select a song to begin")
            self.cover.set_placeholder(theme.accent)
            self.fav.set_icon_name("heart")
            return
        self.title.setText(track.get("title", "Unknown"))
        self.artist.setText(track.get("artist", "Unknown Artist"))
        self.cover.load_path(track.get("artwork_path"), theme.accent)
        self.fav.set_icon_name("heart-fill" if track.get("is_favorite") else "heart")

    def set_playing(self, playing: bool) -> None:
        self.play.set_icon_name("pause" if playing else "play")
        self.cover.set_playing(playing)

    def set_duration(self, ms: int) -> None:
        self._duration = ms
        self.total.setText(format_ms(ms))

    def set_position(self, ms: int) -> None:
        if self.slider._pressed:
            return
        self.elapsed.setText(format_ms(ms))
        if self._duration > 0:
            self.slider.setValue(int(ms / self._duration * 1000))

    def set_shuffle(self, on: bool) -> None:
        self.shuffle.setChecked(on)

    def set_repeat(self, mode: RepeatMode) -> None:
        self.repeat.set_icon_name("repeat")
        self.repeat.setProperty("mode", mode.value)
        self.repeat.setToolTip(f"Repeat: {mode.value}")

    def apply_theme(self, theme: Theme) -> None:
        super().apply_theme(theme)
        controls = (
            getattr(self, "shuffle", None),
            getattr(self, "prev", None),
            getattr(self, "play", None),
            getattr(self, "next", None),
            getattr(self, "repeat", None),
            getattr(self, "fav", None),
            getattr(self, "vol_icon", None),
            getattr(self, "queue_btn", None),
        )
        for btn in controls:
            if btn is not None:
                btn.apply_theme(theme)
