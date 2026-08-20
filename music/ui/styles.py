from __future__ import annotations

from dataclasses import dataclass

from PyQt6.QtGui import QColor


def _hex(color: str) -> QColor:
    c = QColor(color)
    return c if c.isValid() else QColor("#c9a27a")


@dataclass
class Theme:
    mode: str
    accent: str
    scale: float
    glass_opacity: float

    @property
    def dark(self) -> bool:
        return self.mode != "light"

    @property
    def text(self) -> str:
        return "#f4f1ea" if self.dark else "#1b1a18"

    @property
    def muted(self) -> str:
        return "rgba(244, 241, 234, 0.58)" if self.dark else "rgba(27, 26, 24, 0.55)"

    @property
    def faint(self) -> str:
        return "rgba(244, 241, 234, 0.28)" if self.dark else "rgba(27, 26, 24, 0.28)"

    @property
    def glass_rgb(self) -> tuple[int, int, int]:
        return (14, 14, 18) if self.dark else (248, 246, 241)

    @property
    def glass_css(self) -> str:
        r, g, b = self.glass_rgb
        a = int(max(0.18, min(0.78, self.glass_opacity)) * 255)
        return f"rgba({r}, {g}, {b}, {a})"

    @property
    def glass_hover(self) -> str:
        r, g, b = self.glass_rgb
        a = int(max(0.22, min(0.88, self.glass_opacity + 0.12)) * 255)
        return f"rgba({r}, {g}, {b}, {a})"

    @property
    def stroke(self) -> str:
        return "rgba(255, 255, 255, 28)" if self.dark else "rgba(20, 18, 16, 28)"

    @property
    def accent_color(self) -> QColor:
        return _hex(self.accent)

    def fs(self, size: int) -> int:
        return max(10, int(size * self.scale))


def app_stylesheet(theme: Theme) -> str:
    acc = theme.accent
    text = theme.text
    muted = theme.muted
    return f"""
    QWidget {{
        color: {text};
        font-family: 'Segoe UI Variable', 'Segoe UI', 'SF Pro Display', 'Inter', sans-serif;
        font-size: {theme.fs(13)}px;
        background: transparent;
    }}
    QToolTip {{
        color: {text};
        background: {theme.glass_hover};
        border: 1px solid {theme.stroke};
        padding: 6px 10px;
        border-radius: 8px;
    }}
    QScrollArea {{ border: none; background: transparent; }}
    QScrollBar:vertical {{
        background: transparent;
        width: 10px;
        margin: 4px;
    }}
    QScrollBar::handle:vertical {{
        background: {theme.faint};
        border-radius: 5px;
        min-height: 32px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
    QScrollBar:horizontal {{ height: 0; }}
    QLineEdit {{
        background: {theme.glass_css};
        border: 1px solid {theme.stroke};
        border-radius: 12px;
        padding: 8px 12px;
        selection-background-color: {acc};
        color: {text};
    }}
    QLineEdit:focus {{ border: 1px solid {acc}; }}
    QComboBox {{
        background: {theme.glass_css};
        border: 1px solid {theme.stroke};
        border-radius: 10px;
        padding: 6px 10px;
        color: {text};
    }}
    QComboBox QAbstractItemView {{
        background: {theme.glass_hover};
        color: {text};
        selection-background-color: {acc};
        border: 1px solid {theme.stroke};
    }}
    QSlider::groove:horizontal {{
        height: 4px;
        background: {theme.faint};
        border-radius: 2px;
    }}
    QSlider::handle:horizontal {{
        width: 12px;
        height: 12px;
        margin: -4px 0;
        background: {text};
        border-radius: 6px;
    }}
    QSlider::sub-page:horizontal {{
        background: {acc};
        border-radius: 2px;
    }}
    QLabel#muted {{ color: {muted}; }}
    QLabel#title {{ font-weight: 600; }}
    """
