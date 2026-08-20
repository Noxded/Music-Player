from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QPoint, QRectF, Qt, QTimer, QUrl, pyqtSignal
from PyQt6.QtGui import QColor, QKeyEvent, QMouseEvent, QPainter, QPainterPath, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMenu,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from core.database import Database
from core.library import LibraryController
from core.player import PlayerEngine
from core.playlist import RepeatMode
from core.settings import Settings
from ui.background import BackgroundRenderer
from ui.components import GlassPanel, IconButton, SongRow, WindowButton
from ui.music_library import MusicLibrary
from ui.player_bar import PlayerBar
from ui.settings_panel import SettingsPanel
from ui.sidebar import Sidebar
from ui.styles import Theme, app_stylesheet


class TitleBar(QWidget):
    def __init__(self, theme: Theme, window: "MainWindow") -> None:
        super().__init__()
        self._window = window
        self.setFixedHeight(int(52 * theme.scale))
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 12, 0)
        layout.setSpacing(8)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search songs, artists, albums")
        self.search.setFixedWidth(int(280 * theme.scale))
        self.search_btn = IconButton("search", theme, 34)
        self.settings_btn = IconButton("gear", theme, 34)
        layout.addStretch()
        layout.addWidget(self.search_btn)
        layout.addWidget(self.search)
        layout.addStretch()
        layout.addWidget(self.settings_btn)

        traffic = QHBoxLayout()
        traffic.setSpacing(8)
        self.min_btn = WindowButton("min", theme)
        self.max_btn = WindowButton("max", theme)
        self.close_btn = WindowButton("close", theme)
        traffic.addWidget(self.min_btn)
        traffic.addWidget(self.max_btn)
        traffic.addWidget(self.close_btn)
        wrap = QWidget()
        wrap.setLayout(traffic)
        layout.addWidget(wrap)

        self.min_btn.clicked.connect(window.showMinimized)
        self.max_btn.clicked.connect(window.toggle_max)
        self.close_btn.clicked.connect(window.close)
        self.search_btn.clicked.connect(lambda: self.search.setFocus())

        self._drag = QPoint()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag = event.globalPosition().toPoint() - self._window.frameGeometry().topLeft()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if event.buttons() & Qt.MouseButton.LeftButton and not self._window.isMaximized():
            self._window.move(event.globalPosition().toPoint() - self._drag)
        super().mouseMoveEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        self._window.toggle_max()
        super().mouseDoubleClickEvent(event)


class QueuePanel(GlassPanel):
    jump = pyqtSignal(int)

    def __init__(self, theme: Theme, parent=None) -> None:
        super().__init__(theme, 18, parent)
        self.setFixedWidth(320)
        self.layout_ = QVBoxLayout(self)
        self.layout_.setContentsMargins(12, 14, 12, 12)
        title = QLabel("Queue")
        title.setStyleSheet("font-weight: 600; font-size: 16px;")
        self.layout_.addWidget(title)
        self.list_host = QVBoxLayout()
        self.layout_.addLayout(self.list_host)
        self.layout_.addStretch()

    def populate(self, tracks: list[dict], theme: Theme) -> None:
        while self.list_host.count():
            item = self.list_host.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for i, track in enumerate(tracks):
            row = SongRow(track, theme)
            row.clicked.connect(lambda idx=i: self.jump.emit(idx))
            self.list_host.addWidget(row)


class MainWindow(QWidget):
    def __init__(self, settings: Settings, db: Database) -> None:
        super().__init__()
        self.settings = settings
        self.db = db
        self.player = PlayerEngine()
        self.library = LibraryController(db)
        self.theme = self._theme()
        self._bg = QPixmap()
        self._renderer = BackgroundRenderer(settings)
        self._resize_edge = None
        self._drag_origin = QPoint()
        self._maximized = False
        self._normal_geom = None

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setMinimumSize(980, 640)
        self.resize(
            int(settings.get("window", "width") or 1280),
            int(settings.get("window", "height") or 800),
        )
        x, y = settings.get("window", "x"), settings.get("window", "y")
        if settings.get("window", "remember_geometry") and x is not None and y is not None:
            self.move(int(x), int(y))

        self.player.set_volume(float(settings.get("audio", "volume") or 0.8))
        self.player.set_shuffle(bool(settings.get("audio", "shuffle")))
        try:
            self.player.queue.repeat = RepeatMode(settings.get("audio", "repeat") or "off")
        except ValueError:
            self.player.queue.repeat = RepeatMode.OFF

        self._build()
        self._connect()
        self.apply_theme()
        QTimer.singleShot(80, self._refresh_background)
        QTimer.singleShot(200, self._autoload)
        if settings.get("window", "maximized"):
            QTimer.singleShot(0, self.toggle_max)

    def _theme(self) -> Theme:
        a = self.settings.data["appearance"]
        return Theme(
            mode=a.get("mode", "dark"),
            accent=a.get("accent", "#c9a27a"),
            scale=float(a.get("ui_scale") or 1.0),
            glass_opacity=float(a.get("glass_opacity") or 0.42),
        )

    def _build(self) -> None:
        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(14, 12, 14, 12)
        self.root.setSpacing(10)

        self.titlebar = TitleBar(self.theme, self)
        body = QHBoxLayout()
        body.setSpacing(10)
        self.sidebar = Sidebar(self.theme)
        self.content_stack = QStackedWidget()
        self.library_view = MusicLibrary(self.db, self.theme)
        self.content_stack.addWidget(self.library_view)

        self.queue_panel = QueuePanel(self.theme)
        self.queue_panel.hide()

        body.addWidget(self.sidebar)
        body.addWidget(self.content_stack, 1)
        body.addWidget(self.queue_panel)

        self.player_bar = PlayerBar(self.theme)
        self.player_bar.volume.setValue(int(self.player.volume() * 100))
        self.player_bar.set_shuffle(self.player.queue.shuffle)
        self.player_bar.set_repeat(self.player.queue.repeat)

        self.status = QLabel("")
        self.status.setObjectName("muted")
        self.status.hide()

        self.settings_panel = SettingsPanel(self.settings, self.theme, self)
        self.settings_panel.hide()

        self.root.addWidget(self.titlebar)
        self.root.addLayout(body, 1)
        self.root.addWidget(self.status)
        self.root.addWidget(self.player_bar)

    def _connect(self) -> None:
        self.sidebar.navigate.connect(self.library_view.show_page)
        self.sidebar.add_music.connect(self._add_music)
        self.titlebar.settings_btn.clicked.connect(self.toggle_settings)
        self.titlebar.search.textChanged.connect(self.library_view.set_query)
        self.settings_panel.closed.connect(lambda: self.settings_panel.hide())
        self.settings_panel.changed.connect(self.apply_theme)
        self.settings_panel.pick_folder.connect(self._import_default_folder)

        self.library_view.play_tracks.connect(self._play_tracks)
        self.library_view.toggle_favorite.connect(self._toggle_fav)
        self._start_geom = self.geometry()

        self.player_bar.play_toggled.connect(self.player.toggle)
        self.player_bar.next_clicked.connect(self.player.next)
        self.player_bar.prev_clicked.connect(self.player.previous)
        self.player_bar.shuffle_toggled.connect(self._shuffle)
        self.player_bar.repeat_cycled.connect(self._repeat)
        self.player_bar.seek_ratio.connect(self._seek)
        self.player_bar.volume_changed.connect(self._volume)
        self.player_bar.queue_clicked.connect(self.toggle_queue)
        self.player_bar.favorite_clicked.connect(self._fav_current)
        self.queue_panel.jump.connect(self._jump_queue)

        self.player.position_changed.connect(self.player_bar.set_position)
        self.player.duration_changed.connect(self.player_bar.set_duration)
        self.player.state_changed.connect(self._on_state)
        self.player.track_changed.connect(self._on_track)
        self.player.error_occurred.connect(self._toast)

        self.library.scan_progress.connect(self._scan_progress)
        self.library.scan_finished.connect(self._scan_done)
        self.library.scan_failed.connect(self._toast)
        self.library.changed.connect(self.library_view.refresh)
        self._renderer.updated.connect(self._set_bg)

    def _play_tracks(self, tracks: list, start: object) -> None:
        self.player.play_list(tracks, start if isinstance(start, dict) else None)
        self.queue_panel.populate(self.player.queue.ordered_tracks(), self.theme)

    def _jump_queue(self, index: int) -> None:
        track = self.player.queue.jump(index)
        if track:
            self.player.play_track(track)

    def _on_track(self, track: object) -> None:
        if not isinstance(track, dict):
            return
        fresh = self.db.get_track(track["id"]) or track
        self.player_bar.set_track(fresh, self.theme)
        self.db.mark_played(fresh["id"])
        if self.settings.get("library", "remember_last_song"):
            self.settings.set("library", "last_track_id", fresh["id"], persist=False)
        self.queue_panel.populate(self.player.queue.ordered_tracks(), self.theme)

    def _on_state(self, state: str) -> None:
        self.player_bar.set_playing(state == "playing")

    def _seek(self, ratio: float) -> None:
        duration = self.player.duration
        if duration:
            self.player.seek(int(duration * ratio))

    def _volume(self, value: float) -> None:
        self.player.set_volume(value)
        self.settings.set("audio", "volume", value, persist=False)

    def _shuffle(self, on: bool) -> None:
        self.player.set_shuffle(on)
        self.settings.set("audio", "shuffle", on, persist=False)
        self.queue_panel.populate(self.player.queue.ordered_tracks(), self.theme)

    def _repeat(self) -> None:
        mode = self.player.cycle_repeat()
        self.player_bar.set_repeat(mode)
        self.settings.set("audio", "repeat", mode.value, persist=False)

    def _toggle_fav(self, track_id: int) -> None:
        self.db.toggle_favorite(track_id)
        current = self.player.queue.current
        if current and current.get("id") == track_id:
            current["is_favorite"] = 1 - int(bool(current.get("is_favorite")))
            self.player_bar.set_track(self.db.get_track(track_id), self.theme)
        self.library_view.refresh()

    def _fav_current(self) -> None:
        current = self.player.queue.current
        if current:
            self._toggle_fav(current["id"])

    def toggle_queue(self) -> None:
        self.queue_panel.setVisible(not self.queue_panel.isVisible())
        if self.queue_panel.isVisible():
            self.queue_panel.populate(self.player.queue.ordered_tracks(), self.theme)

    def toggle_settings(self) -> None:
        if self.settings_panel.isVisible():
            self.settings_panel.hide()
            return
        self.settings_panel.adjustSize()
        geo = self.rect()
        panel = self.settings_panel.sizeHint()
        self.settings_panel.setGeometry(
            geo.center().x() - panel.width() // 2,
            geo.center().y() - panel.height() // 2,
            panel.width(),
            min(panel.height() + 20, geo.height() - 80),
        )
        self.settings_panel.show()
        self.settings_panel.raise_()

    def _add_music(self) -> None:
        menu = QMenu(self)
        files = menu.addAction("Add files")
        folder = menu.addAction("Add folder")
        playlist = menu.addAction("New playlist")
        chosen = menu.exec(self.sidebar.mapToGlobal(self.sidebar.rect().bottomLeft()))
        if chosen is files:
            paths, _ = QFileDialog.getOpenFileNames(
                self,
                "Add music",
                self.settings.get("library", "music_folder") or "",
                "Audio (*.mp3 *.wav *.flac *.ogg *.m4a *.aac *.wma *.mp4 *.opus *.oga *.aiff)",
            )
            if paths:
                self.library.import_paths(paths)
        elif chosen is folder:
            path = QFileDialog.getExistingDirectory(self, "Add folder")
            if path:
                self.library.import_paths([path])
        elif chosen is playlist:
            name, ok = QInputDialog.getText(self, "Playlist", "Name")
            if ok and name.strip():
                self.db.create_playlist(name.strip())
                self.library_view.refresh()

    def _import_default_folder(self) -> None:
        folder = self.settings.get("library", "music_folder")
        if folder:
            self.library.import_paths([folder])

    def _autoload(self) -> None:
        folder = self.settings.get("library", "music_folder")
        if folder and Path(folder).exists() and not self.db.all_tracks():
            self.library.import_paths([folder])
        last_id = self.settings.get("library", "last_track_id")
        if self.settings.get("library", "remember_last_song") and last_id:
            track = self.db.get_track(int(last_id))
            tracks = self.db.all_tracks()
            if track and tracks:
                self.player.queue.set_tracks(tracks, start_id=track["id"])
                self.player.player.setSource(QUrl.fromLocalFile(track["path"]))
                pos = int(self.settings.get("library", "last_position_ms") or 0)
                if pos:
                    QTimer.singleShot(250, lambda: self.player.seek(pos))
                self.player_bar.set_track(track, self.theme)

    def _scan_progress(self, current: int, total: int, name: str) -> None:
        self.status.show()
        self.status.setText(f"Indexing {current}/{total}  ·  {name}")

    def _scan_done(self, count: int) -> None:
        self.status.setText(f"Added {count} tracks")
        QTimer.singleShot(2200, self.status.hide)
        self.library_view.refresh()

    def _toast(self, message: str) -> None:
        self.status.show()
        self.status.setText(message)
        QTimer.singleShot(3200, self.status.hide)

    def apply_theme(self) -> None:
        self.theme = self._theme()
        self.setStyleSheet(app_stylesheet(self.theme))
        self.sidebar.apply_theme(self.theme)
        self.player_bar.apply_theme(self.theme)
        self.library_view.apply_theme(self.theme)
        self.queue_panel.apply_theme(self.theme)
        self.settings_panel.apply_theme(self.theme)
        self._refresh_background()
        self.update()

    def _refresh_background(self) -> None:
        self._renderer.request(self.size())

    def _set_bg(self, pixmap: QPixmap) -> None:
        self._bg = pixmap
        self.update()

    def toggle_max(self) -> None:
        if self._maximized:
            self._maximized = False
            if self._normal_geom:
                self.setGeometry(self._normal_geom)
        else:
            self._normal_geom = self.geometry()
            screen = QApplication.primaryScreen().availableGeometry()
            self.setGeometry(screen)
            self._maximized = True
        self._refresh_background()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        radius = 0 if self._maximized else 18
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), radius, radius)
        painter.setClipPath(path)
        if not self._bg.isNull():
            painter.drawPixmap(self.rect(), self._bg)
        else:
            painter.fillRect(self.rect(), QColor("#0b0b0e"))
        painter.setClipping(False)
        painter.setPen(QColor(255, 255, 255, 28))
        painter.drawRoundedRect(self.rect().adjusted(0, 0, -1, -1), radius, radius)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if self.settings_panel.isVisible():
            self.toggle_settings()
            self.toggle_settings()
        QTimer.singleShot(40, self._refresh_background)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton and not self._maximized:
            self._resize_edge = self._hit_edge(event.position().toPoint())
            self._drag_origin = event.globalPosition().toPoint()
            self._start_geom = self.geometry()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        pos = event.position().toPoint()
        if self._resize_edge and event.buttons() & Qt.MouseButton.LeftButton:
            self._perform_resize(event.globalPosition().toPoint())
        else:
            edge = self._hit_edge(pos)
            cursors = {
                "left": Qt.CursorShape.SizeHorCursor,
                "right": Qt.CursorShape.SizeHorCursor,
                "top": Qt.CursorShape.SizeVerCursor,
                "bottom": Qt.CursorShape.SizeVerCursor,
                "topleft": Qt.CursorShape.SizeFDiagCursor,
                "bottomright": Qt.CursorShape.SizeFDiagCursor,
                "topright": Qt.CursorShape.SizeBDiagCursor,
                "bottomleft": Qt.CursorShape.SizeBDiagCursor,
            }
            self.setCursor(cursors.get(edge, Qt.CursorShape.ArrowCursor))
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._resize_edge = None
        super().mouseReleaseEvent(event)

    def _hit_edge(self, pos) -> str | None:
        m = 6
        r = self.rect()
        left, right = pos.x() <= m, pos.x() >= r.width() - m
        top, bottom = pos.y() <= m, pos.y() >= r.height() - m
        if top and left:
            return "topleft"
        if top and right:
            return "topright"
        if bottom and left:
            return "bottomleft"
        if bottom and right:
            return "bottomright"
        if left:
            return "left"
        if right:
            return "right"
        if top:
            return "top"
        if bottom:
            return "bottom"
        return None

    def _perform_resize(self, global_pos) -> None:
        delta = global_pos - self._drag_origin
        g = self._start_geom
        geo = g
        edge = self._resize_edge
        if "left" in (edge or ""):
            geo.setLeft(g.left() + delta.x())
        if "right" in (edge or ""):
            geo.setRight(g.right() + delta.x())
        if "top" in (edge or ""):
            geo.setTop(g.top() + delta.y())
        if "bottom" in (edge or ""):
            geo.setBottom(g.bottom() + delta.y())
        if geo.width() >= self.minimumWidth() and geo.height() >= self.minimumHeight():
            self.setGeometry(geo)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        key = event.key()
        if key == Qt.Key.Key_Space:
            self.player.toggle()
        elif key == Qt.Key.Key_Right:
            self.player.seek_relative(5000)
        elif key == Qt.Key.Key_Left:
            self.player.seek_relative(-5000)
        elif key == Qt.Key.Key_Up:
            self.player_bar.volume.setValue(min(100, self.player_bar.volume.value() + 5))
        elif key == Qt.Key.Key_Down:
            self.player_bar.volume.setValue(max(0, self.player_bar.volume.value() - 5))
        elif key == Qt.Key.Key_Escape:
            self.settings_panel.hide()
            self.queue_panel.hide()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event) -> None:
        if self.settings.get("window", "remember_geometry"):
            if not self._maximized:
                g = self.geometry()
                self.settings.set("window", "x", g.x(), persist=False)
                self.settings.set("window", "y", g.y(), persist=False)
                self.settings.set("window", "width", g.width(), persist=False)
                self.settings.set("window", "height", g.height(), persist=False)
            self.settings.set("window", "maximized", self._maximized, persist=False)
        if self.settings.get("library", "remember_last_song"):
            self.settings.set("library", "last_position_ms", int(self.player.player.position()), persist=False)
        self.settings.save()
        self.db.close()
        super().closeEvent(event)
