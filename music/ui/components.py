from __future__ import annotations

from PyQt6.QtCore import (
    QEasingCurve,
    QPoint,
    QPropertyAnimation,
    QSize,
    Qt,
    pyqtProperty,
    pyqtSignal,
)
from PyQt6.QtGui import QColor, QCursor, QFont, QIcon, QPainter, QPainterPath, QPen, QPixmap
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from ui.styles import Theme


class GlassPanel(QFrame):
    def __init__(self, theme: Theme, radius: int = 18, parent=None) -> None:
        super().__init__(parent)
        self._theme = theme
        self._radius = radius
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.apply_theme(theme)

    def apply_theme(self, theme: Theme) -> None:
        self._theme = theme
        self.setStyleSheet(
            f"""
            GlassPanel {{
                background-color: {theme.glass_css};
                border: 1px solid {theme.stroke};
                border-radius: {self._radius}px;
            }}
            """
        )


class IconPix:
    @staticmethod
    def draw(name: str, color: QColor, size: int = 22) -> QPixmap:
        pm = QPixmap(size, size)
        pm.fill(Qt.GlobalColor.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(color, max(1.4, size / 14), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        s = size
        m = s * 0.22
        if name == "play":
            path = QPainterPath()
            path.moveTo(s * 0.34, s * 0.22)
            path.lineTo(s * 0.78, s * 0.5)
            path.lineTo(s * 0.34, s * 0.78)
            path.closeSubpath()
            p.setBrush(color)
            p.setPen(Qt.PenStyle.NoPen)
            p.drawPath(path)
        elif name == "pause":
            p.setBrush(color)
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(int(s * 0.30), int(s * 0.24), int(s * 0.14), int(s * 0.52), 2, 2)
            p.drawRoundedRect(int(s * 0.56), int(s * 0.24), int(s * 0.14), int(s * 0.52), 2, 2)
        elif name == "next":
            p.drawLine(QPoint(int(s * 0.28), int(s * 0.28)), QPoint(int(s * 0.62), int(s * 0.5)))
            p.drawLine(QPoint(int(s * 0.62), int(s * 0.5)), QPoint(int(s * 0.28), int(s * 0.72)))
            p.drawLine(QPoint(int(s * 0.72), int(s * 0.26)), QPoint(int(s * 0.72), int(s * 0.74)))
        elif name == "prev":
            p.drawLine(QPoint(int(s * 0.72), int(s * 0.28)), QPoint(int(s * 0.38), int(s * 0.5)))
            p.drawLine(QPoint(int(s * 0.38), int(s * 0.5)), QPoint(int(s * 0.72), int(s * 0.72)))
            p.drawLine(QPoint(int(s * 0.28), int(s * 0.26)), QPoint(int(s * 0.28), int(s * 0.74)))
        elif name == "shuffle":
            p.drawLine(int(m), int(s * 0.34), int(s * 0.42), int(s * 0.34))
            p.drawLine(int(s * 0.58), int(s * 0.34), int(s * 0.78), int(s * 0.34))
            p.drawLine(int(s * 0.42), int(s * 0.34), int(s * 0.58), int(s * 0.66))
            p.drawLine(int(m), int(s * 0.66), int(s * 0.42), int(s * 0.66))
            p.drawLine(int(s * 0.58), int(s * 0.66), int(s * 0.78), int(s * 0.66))
        elif name == "repeat":
            p.drawArc(int(m), int(m), int(s - 2 * m), int(s - 2 * m), 40 * 16, 260 * 16)
            p.drawLine(int(s * 0.70), int(m + 1), int(s * 0.82), int(s * 0.30))
            p.drawLine(int(s * 0.70), int(m + 1), int(s * 0.58), int(s * 0.28))
        elif name == "heart":
            path = QPainterPath()
            path.moveTo(s * 0.5, s * 0.78)
            path.cubicTo(s * 0.18, s * 0.58, s * 0.14, s * 0.32, s * 0.32, s * 0.24)
            path.cubicTo(s * 0.42, s * 0.18, s * 0.50, s * 0.28, s * 0.50, s * 0.36)
            path.cubicTo(s * 0.50, s * 0.28, s * 0.58, s * 0.18, s * 0.68, s * 0.24)
            path.cubicTo(s * 0.86, s * 0.32, s * 0.82, s * 0.58, s * 0.5, s * 0.78)
            p.drawPath(path)
        elif name == "heart-fill":
            path = QPainterPath()
            path.moveTo(s * 0.5, s * 0.78)
            path.cubicTo(s * 0.18, s * 0.58, s * 0.14, s * 0.32, s * 0.32, s * 0.24)
            path.cubicTo(s * 0.42, s * 0.18, s * 0.50, s * 0.28, s * 0.50, s * 0.36)
            path.cubicTo(s * 0.50, s * 0.28, s * 0.58, s * 0.18, s * 0.68, s * 0.24)
            path.cubicTo(s * 0.86, s * 0.32, s * 0.82, s * 0.58, s * 0.5, s * 0.78)
            p.setBrush(color)
            p.drawPath(path)
        elif name == "search":
            p.drawEllipse(int(s * 0.22), int(s * 0.22), int(s * 0.42), int(s * 0.42))
            p.drawLine(int(s * 0.58), int(s * 0.58), int(s * 0.76), int(s * 0.76))
        elif name == "gear":
            p.drawEllipse(int(s * 0.36), int(s * 0.36), int(s * 0.28), int(s * 0.28))
            for i in range(6):
                p.save()
                p.translate(s / 2, s / 2)
                p.rotate(i * 60)
                p.drawLine(0, int(-s * 0.18), 0, int(-s * 0.36))
                p.restore()
        elif name == "home":
            path = QPainterPath()
            path.moveTo(s * 0.5, s * 0.22)
            path.lineTo(s * 0.82, s * 0.50)
            path.lineTo(s * 0.82, s * 0.78)
            path.lineTo(s * 0.18, s * 0.78)
            path.lineTo(s * 0.18, s * 0.50)
            path.closeSubpath()
            p.drawPath(path)
        elif name == "music":
            p.drawLine(int(s * 0.38), int(s * 0.22), int(s * 0.38), int(s * 0.70))
            p.drawLine(int(s * 0.38), int(s * 0.22), int(s * 0.74), int(s * 0.30))
            p.drawLine(int(s * 0.74), int(s * 0.30), int(s * 0.74), int(s * 0.62))
            p.setBrush(color)
            p.drawEllipse(int(s * 0.22), int(s * 0.62), int(s * 0.22), int(s * 0.16))
            p.drawEllipse(int(s * 0.58), int(s * 0.54), int(s * 0.22), int(s * 0.16))
        elif name == "album":
            p.drawEllipse(int(m), int(m), int(s - 2 * m), int(s - 2 * m))
            p.drawEllipse(int(s * 0.42), int(s * 0.42), int(s * 0.16), int(s * 0.16))
        elif name == "artist":
            p.drawEllipse(int(s * 0.36), int(s * 0.20), int(s * 0.28), int(s * 0.28))
            p.drawArc(int(s * 0.22), int(s * 0.48), int(s * 0.56), int(s * 0.42), 0, 180 * 16)
        elif name == "playlist":
            p.drawLine(int(s * 0.24), int(s * 0.32), int(s * 0.76), int(s * 0.32))
            p.drawLine(int(s * 0.24), int(s * 0.50), int(s * 0.76), int(s * 0.50))
            p.drawLine(int(s * 0.24), int(s * 0.68), int(s * 0.52), int(s * 0.68))
        elif name == "clock":
            p.drawEllipse(int(m), int(m), int(s - 2 * m), int(s - 2 * m))
            p.drawLine(int(s * 0.5), int(s * 0.5), int(s * 0.5), int(s * 0.32))
            p.drawLine(int(s * 0.5), int(s * 0.5), int(s * 0.66), int(s * 0.58))
        elif name == "plus":
            p.drawLine(int(s * 0.5), int(s * 0.26), int(s * 0.5), int(s * 0.74))
            p.drawLine(int(s * 0.26), int(s * 0.5), int(s * 0.74), int(s * 0.5))
        elif name == "queue":
            p.drawLine(int(s * 0.24), int(s * 0.30), int(s * 0.76), int(s * 0.30))
            p.drawLine(int(s * 0.24), int(s * 0.50), int(s * 0.76), int(s * 0.50))
            p.drawLine(int(s * 0.24), int(s * 0.70), int(s * 0.76), int(s * 0.70))
        elif name == "volume":
            path = QPainterPath()
            path.moveTo(s * 0.22, s * 0.42)
            path.lineTo(s * 0.38, s * 0.42)
            path.lineTo(s * 0.54, s * 0.28)
            path.lineTo(s * 0.54, s * 0.72)
            path.lineTo(s * 0.38, s * 0.58)
            path.lineTo(s * 0.22, s * 0.58)
            path.closeSubpath()
            p.drawPath(path)
            p.drawArc(int(s * 0.52), int(s * 0.32), int(s * 0.24), int(s * 0.36), -50 * 16, 100 * 16)
        elif name == "close":
            p.drawLine(int(s * 0.30), int(s * 0.30), int(s * 0.70), int(s * 0.70))
            p.drawLine(int(s * 0.70), int(s * 0.30), int(s * 0.30), int(s * 0.70))
        elif name == "min":
            p.drawLine(int(s * 0.28), int(s * 0.55), int(s * 0.72), int(s * 0.55))
        elif name == "max":
            p.drawRoundedRect(int(s * 0.28), int(s * 0.28), int(s * 0.44), int(s * 0.44), 2, 2)
        elif name == "restore":
            p.drawRect(int(s * 0.34), int(s * 0.26), int(s * 0.36), int(s * 0.36))
            p.drawRect(int(s * 0.26), int(s * 0.38), int(s * 0.36), int(s * 0.36))
        else:
            p.drawEllipse(int(m), int(m), int(s - 2 * m), int(s - 2 * m))
        p.end()
        return pm


class IconButton(QPushButton):
    def __init__(self, icon: str, theme: Theme, size: int = 36, parent=None, accent: bool = False) -> None:
        super().__init__(parent)
        self._icon_name = icon
        self._theme = theme
        self._accent = accent
        self._hover = 0.0
        self._size = size
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFixedSize(size, size)
        self.setFlat(True)
        self._anim = QPropertyAnimation(self, b"hover", self)
        self._anim.setDuration(160)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.toggled.connect(lambda _: self._refresh())
        self._refresh()

    def apply_theme(self, theme: Theme) -> None:
        self._theme = theme
        self._refresh()

    def set_icon_name(self, name: str) -> None:
        self._icon_name = name
        self._refresh()

    def get_hover(self) -> float:
        return self._hover

    def set_hover(self, value: float) -> None:
        self._hover = value
        self._refresh()

    hover = pyqtProperty(float, get_hover, set_hover)

    def enterEvent(self, event) -> None:
        self._anim.stop()
        self._anim.setStartValue(self._hover)
        self._anim.setEndValue(1.0)
        self._anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._anim.stop()
        self._anim.setStartValue(self._hover)
        self._anim.setEndValue(0.0)
        self._anim.start()
        super().leaveEvent(event)

    def _refresh(self) -> None:
        base = QColor(self._theme.text)
        acc = self._theme.accent_color
        if self._accent or self.isChecked():
            color = acc
        else:
            color = QColor(
                int(base.red() + (acc.red() - base.red()) * self._hover * 0.35),
                int(base.green() + (acc.green() - base.green()) * self._hover * 0.35),
                int(base.blue() + (acc.blue() - base.blue()) * self._hover * 0.35),
                int(170 + 85 * self._hover),
            )
        icon_size = int(self._size * 0.58)
        self.setIcon(QIcon(IconPix.draw(self._icon_name, color, icon_size)))
        self.setIconSize(QSize(icon_size, icon_size))
        bg_a = int(18 + 40 * self._hover)
        self.setStyleSheet(
            f"""
            QPushButton {{
                border: none;
                border-radius: {self._size // 2}px;
                background: rgba(255,255,255,{bg_a});
            }}
            """
        )


class WindowButton(QPushButton):
    def __init__(self, kind: str, theme: Theme, parent=None) -> None:
        super().__init__(parent)
        self.kind = kind
        self._theme = theme
        self.setFixedSize(14, 14)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._paint()

    def apply_theme(self, theme: Theme) -> None:
        self._theme = theme
        self._paint()

    def _paint(self) -> None:
        colors = {"close": "#e26d6d", "max": "#d4c07a", "min": "#7dcea0"}
        c = colors.get(self.kind, "#888")
        self.setStyleSheet(
            f"""
            QPushButton {{
                background: {c};
                border: none;
                border-radius: 7px;
            }}
            QPushButton:hover {{ background: {c}; }}
            """
        )


class CoverLabel(QLabel):
    """Album art with a subtle breathing scale while playing."""

    def __init__(self, size: int = 240, radius: int = 16, parent=None) -> None:
        super().__init__(parent)
        self._base = size
        self._radius = radius
        self._source: QPixmap | None = None
        self._scale = 1.0
        self._playing = False
        self.setFixedSize(size, size)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._anim = QPropertyAnimation(self, b"artScale", self)
        self._anim.setDuration(4200)
        self._anim.setLoopCount(-1)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutSine)
        self._anim.setStartValue(1.0)
        self._anim.setEndValue(1.045)
        self.set_placeholder()

    def get_scale(self) -> float:
        return self._scale

    def set_scale(self, value: float) -> None:
        self._scale = value
        self._render()

    artScale = pyqtProperty(float, get_scale, set_scale)

    def set_playing(self, playing: bool) -> None:
        self._playing = playing
        if playing:
            self._anim.start()
        else:
            self._anim.stop()
            self.set_scale(1.0)

    def set_placeholder(self, accent: str = "#c9a27a") -> None:
        pm = QPixmap(self._base, self._base)
        pm.fill(QColor("#16151a"))
        p = QPainter(pm)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(accent))
        p.setOpacity(0.22)
        p.drawEllipse(int(self._base * 0.18), int(self._base * 0.18), int(self._base * 0.64), int(self._base * 0.64))
        p.end()
        self.set_pixmap(pm)

    def set_pixmap(self, pixmap: QPixmap) -> None:
        self._source = pixmap
        self._render()

    def load_path(self, path: str | None, accent: str = "#c9a27a") -> None:
        if path and QPixmap(path).isNull() is False:
            self.set_pixmap(QPixmap(path))
        else:
            self.set_placeholder(accent)

    def _render(self) -> None:
        if self._source is None:
            return
        size = self._base
        canvas = QPixmap(size, size)
        canvas.fill(Qt.GlobalColor.transparent)
        scaled = self._source.scaled(
            int(size * self._scale),
            int(size * self._scale),
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )
        painter = QPainter(canvas)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(0, 0, size, size, self._radius, self._radius)
        painter.setClipPath(path)
        x = (size - scaled.width()) // 2
        y = (size - scaled.height()) // 2
        painter.drawPixmap(x, y, scaled)
        painter.end()
        super().setPixmap(canvas)


class SongRow(QWidget):
    clicked = pyqtSignal()
    favorite_toggled = pyqtSignal()
    add_to_playlist = pyqtSignal(object)

    def __init__(self, track: dict, theme: Theme, parent=None) -> None:
        super().__init__(parent)
        self.track = track
        self._theme = theme
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFixedHeight(int(58 * theme.scale))
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(12)

        self.cover = CoverLabel(44, 8)
        self.cover.load_path(track.get("artwork_path"), theme.accent)
        layout.addWidget(self.cover)

        text = QVBoxLayout()
        text.setSpacing(1)
        self.title = QLabel(track.get("title", "Unknown"))
        self.title.setObjectName("title")
        self.meta = QLabel(f"{track.get('artist', '')}  ·  {track.get('album', '')}")
        self.meta.setObjectName("muted")
        text.addWidget(self.title)
        text.addWidget(self.meta)
        layout.addLayout(text, 1)

        self.duration = QLabel(_fmt_ms(track.get("duration_ms", 0)))
        self.duration.setObjectName("muted")
        layout.addWidget(self.duration)

        self.heart = IconButton(
            "heart-fill" if track.get("is_favorite") else "heart",
            theme,
            32,
        )
        self.heart.clicked.connect(self.favorite_toggled.emit)
        layout.addWidget(self.heart)
        self._hover = False
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.apply_theme(theme)

    def apply_theme(self, theme: Theme) -> None:
        self._theme = theme
        self._restyle()

    def enterEvent(self, event) -> None:
        self._hover = True
        self._restyle()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._hover = False
        self._restyle()
        super().leaveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mouseReleaseEvent(event)

    def _restyle(self) -> None:
        bg = self._theme.glass_hover if self._hover else "transparent"
        self.setStyleSheet(
            f"""
            SongRow {{
                background: {bg};
                border-radius: 12px;
            }}
            """
        )


class MediaCard(QFrame):
    clicked = pyqtSignal()

    def __init__(self, title: str, subtitle: str, art: str | None, theme: Theme, parent=None) -> None:
        super().__init__(parent)
        self._theme = theme
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFixedWidth(int(168 * theme.scale))
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 12)
        layout.setSpacing(8)
        self.cover = CoverLabel(int(148 * theme.scale), 14)
        self.cover.load_path(art, theme.accent)
        title_l = QLabel(title)
        title_l.setObjectName("title")
        title_l.setWordWrap(True)
        sub = QLabel(subtitle)
        sub.setObjectName("muted")
        sub.setWordWrap(True)
        layout.addWidget(self.cover)
        layout.addWidget(title_l)
        layout.addWidget(sub)
        self.apply_theme(theme)

    def apply_theme(self, theme: Theme) -> None:
        self._theme = theme
        self.setStyleSheet(
            f"""
            MediaCard {{
                background: {theme.glass_css};
                border: 1px solid {theme.stroke};
                border-radius: 16px;
            }}
            MediaCard:hover {{
                background: {theme.glass_hover};
            }}
            """
        )

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mouseReleaseEvent(event)


class SeekSlider(QSlider):
    seek_requested = pyqtSignal(float)

    def __init__(self, parent=None) -> None:
        super().__init__(Qt.Orientation.Horizontal, parent)
        self.setRange(0, 1000)
        self._pressed = False
        self.sliderPressed.connect(lambda: setattr(self, "_pressed", True))
        self.sliderReleased.connect(self._release)

    def _release(self) -> None:
        self._pressed = False
        self.seek_requested.emit(self.value() / 1000.0)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            ratio = event.position().x() / max(1, self.width())
            self.setValue(int(ratio * 1000))
            self.seek_requested.emit(max(0.0, min(1.0, ratio)))
        super().mousePressEvent(event)


def _fmt_ms(ms: int) -> str:
    ms = max(0, int(ms or 0))
    s = ms // 1000
    return f"{s // 60}:{s % 60:02d}"


def format_ms(ms: int) -> str:
    return _fmt_ms(ms)


class SectionTitle(QLabel):
    def __init__(self, text: str, theme: Theme, parent=None) -> None:
        super().__init__(text, parent)
        font = QFont()
        font.setPointSize(theme.fs(16))
        font.setWeight(QFont.Weight.DemiBold)
        self.setFont(font)
