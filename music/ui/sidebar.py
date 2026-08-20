from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

from ui.components import GlassPanel, IconPix
from ui.styles import Theme


NAV_ITEMS = [
    ("home", "home", "Home"),
    ("songs", "music", "Songs"),
    ("albums", "album", "Albums"),
    ("artists", "artist", "Artists"),
    ("playlists", "playlist", "Playlists"),
    ("favorites", "heart", "Favorites"),
    ("recent", "clock", "Recently Played"),
]


class NavButton(QPushButton):
    def __init__(self, key: str, icon: str, label: str, theme: Theme, parent=None) -> None:
        super().__init__(label, parent)
        self.key = key
        self.icon_name = icon
        self._theme = theme
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setCheckable(True)
        self.apply_theme(theme)

    def apply_theme(self, theme: Theme) -> None:
        self._theme = theme
        self.setIcon(QIcon(IconPix.draw(self.icon_name, theme.accent_color, 18)))
        self.setStyleSheet(
            f"""
            QPushButton {{
                text-align: left;
                padding: 10px 14px;
                border: none;
                border-radius: 12px;
                color: {theme.text};
                background: transparent;
                font-size: {theme.fs(13)}px;
            }}
            QPushButton:hover {{
                background: {theme.glass_hover};
            }}
            QPushButton:checked {{
                background: {theme.glass_hover};
                color: {theme.accent};
                font-weight: 600;
            }}
            """
        )


class Sidebar(GlassPanel):
    navigate = pyqtSignal(str)
    add_music = pyqtSignal()

    def __init__(self, theme: Theme, parent=None) -> None:
        super().__init__(theme, 20, parent)
        self.buttons: list[NavButton] = []
        self.setFixedWidth(int(228 * theme.scale))
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 18, 14, 16)
        layout.setSpacing(4)

        brand = QLabel("ARIA")
        brand.setStyleSheet(
            f"color: {theme.accent}; letter-spacing: 4px; font-size: {theme.fs(15)}px; font-weight: 700;"
        )
        sub = QLabel("Music")
        sub.setObjectName("muted")
        layout.addWidget(brand)
        layout.addWidget(sub)
        layout.addSpacing(18)

        self.buttons: list[NavButton] = []
        for key, icon, label in NAV_ITEMS:
            btn = NavButton(key, icon, label, theme)
            btn.clicked.connect(lambda _=False, k=key: self._select(k))
            layout.addWidget(btn)
            self.buttons.append(btn)

        layout.addStretch(1)

        add = QPushButton("  Add Music")
        add.setCursor(Qt.CursorShape.PointingHandCursor)
        add.setIcon(QIcon(IconPix.draw("plus", theme.accent_color, 16)))
        add.clicked.connect(self.add_music.emit)
        add.setStyleSheet(
            f"""
            QPushButton {{
                background: {theme.glass_hover};
                border: 1px solid {theme.stroke};
                border-radius: 14px;
                padding: 12px 14px;
                color: {theme.text};
                font-weight: 600;
            }}
            QPushButton:hover {{ background: {theme.accent}; color: #111; }}
            """
        )
        layout.addWidget(add)
        self._add_btn = add
        self._select("home")

    def _select(self, key: str) -> None:
        for btn in self.buttons:
            btn.setChecked(btn.key == key)
            btn.apply_theme(self._theme)
        self.navigate.emit(key)

    def apply_theme(self, theme: Theme) -> None:
        super().apply_theme(theme)
        if not getattr(self, "buttons", None):
            return
        for btn in self.buttons:
            btn.apply_theme(theme)
        if not getattr(self, "_add_btn", None):
            return
        self._add_btn.setStyleSheet(
            f"""
            QPushButton {{
                background: {theme.glass_hover};
                border: 1px solid {theme.stroke};
                border-radius: 14px;
                padding: 12px 14px;
                color: {theme.text};
                font-weight: 600;
            }}
            QPushButton:hover {{ background: {theme.accent}; color: #111; }}
            """
        )
