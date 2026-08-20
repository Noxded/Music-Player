from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QColorDialog,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from core.settings import Settings
from ui.components import GlassPanel
from ui.styles import Theme


class SettingsPanel(GlassPanel):
    changed = pyqtSignal()
    closed = pyqtSignal()
    pick_folder = pyqtSignal()

    def __init__(self, settings: Settings, theme: Theme, parent=None) -> None:
        super().__init__(theme, 22, parent)
        self.settings = settings
        self.setFixedWidth(440)
        self.setMaximumHeight(720)
        shell = QVBoxLayout(self)
        shell.setContentsMargins(8, 8, 8, 8)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        inner = QWidget()
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(16, 12, 16, 16)
        layout.setSpacing(12)
        scroll.setWidget(inner)
        shell.addWidget(scroll)

        header = QHBoxLayout()
        title = QLabel("Settings")
        title.setStyleSheet(f"font-size: {theme.fs(20)}px; font-weight: 600;")
        close = QPushButton("Close")
        close.setCursor(Qt.CursorShape.PointingHandCursor)
        close.clicked.connect(self.closed.emit)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(close)
        layout.addLayout(header)

        layout.addWidget(self._label("Background"))
        row = QHBoxLayout()
        self.bg_type = QComboBox()
        self.bg_type.addItems(["Image", "Solid color"])
        self.bg_type.setCurrentIndex(0 if settings.get("appearance", "background_type") == "image" else 1)
        img_btn = QPushButton("Choose image")
        color_btn = QPushButton("Color")
        img_btn.clicked.connect(self._pick_image)
        color_btn.clicked.connect(self._pick_color)
        row.addWidget(self.bg_type, 1)
        row.addWidget(img_btn)
        row.addWidget(color_btn)
        layout.addLayout(row)
        self.bg_type.currentIndexChanged.connect(self._on_bg_type)

        self.opacity = self._slider("Background opacity", 5, 100, int(settings.get("appearance", "background_opacity") * 100))
        self.blur = self._slider("Background blur", 0, 50, int(settings.get("appearance", "background_blur")))
        self.overlay = self._slider("Dark overlay", 0, 80, int(settings.get("appearance", "dark_overlay") * 100))
        self.glass = self._slider("Glass transparency", 18, 75, int(settings.get("appearance", "glass_opacity") * 100))
        self.scale = self._slider("UI scale", 80, 140, int(settings.get("appearance", "ui_scale") * 100))
        layout.addWidget(self.opacity[0])
        layout.addWidget(self.blur[0])
        layout.addWidget(self.overlay[0])
        layout.addWidget(self.glass[0])
        layout.addWidget(self.scale[0])

        mode_row = QHBoxLayout()
        mode_row.addWidget(self._label("Appearance"))
        self.mode = QComboBox()
        self.mode.addItems(["Dark", "Light"])
        self.mode.setCurrentIndex(0 if settings.get("appearance", "mode") == "dark" else 1)
        accent_btn = QPushButton("Accent color")
        accent_btn.clicked.connect(self._pick_accent)
        mode_row.addWidget(self.mode, 1)
        mode_row.addWidget(accent_btn)
        layout.addLayout(mode_row)
        self.mode.currentIndexChanged.connect(self._persist)

        layout.addWidget(self._label("Library"))
        folder_row = QHBoxLayout()
        self.folder = QLineEdit(settings.get("library", "music_folder") or "")
        self.folder.setPlaceholderText("Default music folder")
        browse = QPushButton("Browse")
        browse.clicked.connect(self._pick_folder)
        folder_row.addWidget(self.folder, 1)
        folder_row.addWidget(browse)
        layout.addLayout(folder_row)

        self.remember_song = QComboBox()
        self.remember_song.addItems(["Remember last song", "Do not remember last song"])
        self.remember_song.setCurrentIndex(0 if settings.get("library", "remember_last_song") else 1)
        self.remember_geom = QComboBox()
        self.remember_geom.addItems(["Remember window size & position", "Do not remember window"])
        self.remember_geom.setCurrentIndex(0 if settings.get("window", "remember_geometry") else 1)
        layout.addWidget(self.remember_song)
        layout.addWidget(self.remember_geom)
        self.remember_song.currentIndexChanged.connect(self._persist)
        self.remember_geom.currentIndexChanged.connect(self._persist)

        layout.addWidget(self._label("Audio"))
        self.volume = self._slider("Default volume", 0, 100, int(settings.get("audio", "volume") * 100))
        layout.addWidget(self.volume[0])
        layout.addStretch()

        for slider in (self.opacity[1], self.blur[1], self.overlay[1], self.glass[1], self.scale[1], self.volume[1]):
            slider.valueChanged.connect(self._persist)

        close.setStyleSheet(
            f"""
            QPushButton {{
                background: transparent;
                border: 1px solid {theme.stroke};
                border-radius: 10px;
                padding: 6px 12px;
                color: {theme.text};
            }}
            """
        )

    def _label(self, text: str) -> QLabel:
        lab = QLabel(text)
        lab.setStyleSheet("font-weight: 600; padding-top: 8px;")
        return lab

    def _slider(self, caption: str, lo: int, hi: int, value: int) -> tuple[QWidget, QSlider]:
        box = QWidget()
        layout = QVBoxLayout(box)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        row = QHBoxLayout()
        lab = QLabel(caption)
        lab.setObjectName("muted")
        val = QLabel(str(value))
        val.setObjectName("muted")
        row.addWidget(lab)
        row.addStretch()
        row.addWidget(val)
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(lo, hi)
        slider.setValue(value)
        slider.valueChanged.connect(lambda v: val.setText(str(v)))
        layout.addLayout(row)
        layout.addWidget(slider)
        return box, slider

    def _pick_image(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Background image",
            "",
            "Images (*.png *.jpg *.jpeg *.webp *.bmp)",
        )
        if path:
            self.settings.set("appearance", "background_image", path, persist=False)
            self.settings.set("appearance", "background_type", "image", persist=False)
            self.bg_type.setCurrentIndex(0)
            self._persist()

    def _pick_color(self) -> None:
        color = QColorDialog.getColor(QColor(self.settings.get("appearance", "background_color")), self)
        if color.isValid():
            self.settings.set("appearance", "background_color", color.name(), persist=False)
            self.settings.set("appearance", "background_type", "color", persist=False)
            self.bg_type.setCurrentIndex(1)
            self._persist()

    def _pick_accent(self) -> None:
        color = QColorDialog.getColor(QColor(self.settings.get("appearance", "accent")), self)
        if color.isValid():
            self.settings.set("appearance", "accent", color.name(), persist=False)
            self._persist()

    def _pick_folder(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Default music folder")
        if path:
            self.folder.setText(path)
            self._persist()
            self.pick_folder.emit()

    def _on_bg_type(self) -> None:
        self.settings.set(
            "appearance",
            "background_type",
            "image" if self.bg_type.currentIndex() == 0 else "color",
            persist=False,
        )
        self._persist()

    def _persist(self) -> None:
        s = self.settings
        s.set("appearance", "background_opacity", self.opacity[1].value() / 100.0, persist=False)
        s.set("appearance", "background_blur", self.blur[1].value(), persist=False)
        s.set("appearance", "dark_overlay", self.overlay[1].value() / 100.0, persist=False)
        s.set("appearance", "glass_opacity", self.glass[1].value() / 100.0, persist=False)
        s.set("appearance", "ui_scale", self.scale[1].value() / 100.0, persist=False)
        s.set("appearance", "mode", "dark" if self.mode.currentIndex() == 0 else "light", persist=False)
        s.set("library", "music_folder", self.folder.text(), persist=False)
        s.set("library", "remember_last_song", self.remember_song.currentIndex() == 0, persist=False)
        s.set("window", "remember_geometry", self.remember_geom.currentIndex() == 0, persist=False)
        s.set("audio", "volume", self.volume[1].value() / 100.0, persist=False)
        s.save()
        self.changed.emit()
