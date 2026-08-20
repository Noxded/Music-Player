from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from core.database import Database
from ui.components import CoverLabel, MediaCard, SectionTitle, SongRow
from ui.styles import Theme


class _Scroll(QScrollArea):
    def __init__(self, child: QWidget) -> None:
        super().__init__()
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setWidget(child)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)


class MusicLibrary(QStackedWidget):
    play_tracks = pyqtSignal(list, object)
    toggle_favorite = pyqtSignal(int)
    open_album = pyqtSignal(str, str)
    open_artist = pyqtSignal(str)
    open_playlist = pyqtSignal(int)

    def __init__(self, db: Database, theme: Theme, parent=None) -> None:
        super().__init__(parent)
        self.db = db
        self.theme = theme
        self._query = ""
        self._pages = {}
        for name in ("home", "songs", "albums", "artists", "playlists", "favorites", "recent", "detail"):
            page = QWidget()
            layout = QVBoxLayout(page)
            layout.setContentsMargins(4, 0, 4, 0)
            inner = QWidget()
            inner_layout = QVBoxLayout(inner)
            inner_layout.setContentsMargins(8, 8, 8, 20)
            inner_layout.setSpacing(16)
            layout.addWidget(_Scroll(inner))
            self._pages[name] = inner_layout
            self.addWidget(page)
        self.refresh()

    def set_query(self, query: str) -> None:
        self._query = query.strip()
        if self._query:
            self.show_page("songs")
        else:
            self.refresh()

    def show_page(self, name: str) -> None:
        keys = ["home", "songs", "albums", "artists", "playlists", "favorites", "recent", "detail"]
        if name in keys:
            self.setCurrentIndex(keys.index(name))
            self._rebuild(name)

    def refresh(self) -> None:
        current = ["home", "songs", "albums", "artists", "playlists", "favorites", "recent", "detail"]
        name = current[self.currentIndex()]
        self._rebuild(name)

    def apply_theme(self, theme: Theme) -> None:
        self.theme = theme
        self.refresh()

    def _clear(self, layout: QVBoxLayout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._wipe_layout(item.layout())

    def _wipe_layout(self, layout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._wipe_layout(item.layout())

    def _rebuild(self, name: str) -> None:
        layout = self._pages[name]
        self._clear(layout)
        if name == "home":
            self._home(layout)
        elif name == "songs":
            self._songs(layout, self.db.all_tracks(self._query))
        elif name == "albums":
            self._albums(layout)
        elif name == "artists":
            self._artists(layout)
        elif name == "playlists":
            self._playlists(layout)
        elif name == "favorites":
            self._songs(layout, self.db.favorites(), heading="Favorites")
        elif name == "recent":
            self._songs(layout, self.db.recently_played(), heading="Recently Played")

    def show_album(self, album: str, artist: str) -> None:
        tracks = self.db.album_tracks(album, artist)
        self._detail(album, artist, tracks)

    def show_artist(self, artist: str) -> None:
        tracks = self.db.artist_tracks(artist)
        self._detail(artist, "Artist", tracks)

    def show_playlist(self, playlist_id: int, name: str) -> None:
        tracks = self.db.playlist_tracks(playlist_id)
        self._detail(name, "Playlist", tracks)

    def _detail(self, title: str, subtitle: str, tracks: list[dict]) -> None:
        layout = self._pages["detail"]
        self._clear(layout)
        header = QHBoxLayout()
        art = CoverLabel(160, 18)
        if tracks:
            art.load_path(tracks[0].get("artwork_path"), self.theme.accent)
        else:
            art.set_placeholder(self.theme.accent)
        texts = QVBoxLayout()
        texts.addStretch()
        t = QLabel(title)
        t.setStyleSheet(f"font-size: {self.theme.fs(28)}px; font-weight: 600;")
        s = QLabel(f"{subtitle}  ·  {len(tracks)} tracks")
        s.setObjectName("muted")
        texts.addWidget(t)
        texts.addWidget(s)
        texts.addStretch()
        header.addWidget(art)
        header.addLayout(texts, 1)
        wrap = QWidget()
        wrap.setLayout(header)
        layout.addWidget(wrap)
        self._song_list(layout, tracks)
        self.setCurrentIndex(7)

    def _home(self, layout: QVBoxLayout) -> None:
        hero_track = None
        recent = self.db.recently_played(1)
        added = self.db.recently_added(1)
        if recent:
            hero_track = recent[0]
        elif added:
            hero_track = added[0]
        if hero_track:
            hero = QHBoxLayout()
            art = CoverLabel(int(260 * self.theme.scale), 22)
            art.load_path(hero_track.get("artwork_path"), self.theme.accent)
            art.set_playing(True)
            col = QVBoxLayout()
            kicker = QLabel("NOW SELECTED")
            kicker.setStyleSheet(
                f"color: {self.theme.accent}; letter-spacing: 3px; font-size: {self.theme.fs(11)}px;"
            )
            title = QLabel(hero_track.get("title", ""))
            title.setStyleSheet(f"font-size: {self.theme.fs(32)}px; font-weight: 600;")
            title.setWordWrap(True)
            artist = QLabel(hero_track.get("artist", ""))
            artist.setObjectName("muted")
            album = QLabel(hero_track.get("album", ""))
            album.setObjectName("muted")
            col.addStretch()
            col.addWidget(kicker)
            col.addWidget(title)
            col.addWidget(artist)
            col.addWidget(album)
            col.addStretch()
            hero.addWidget(art)
            hero.addSpacing(24)
            hero.addLayout(col, 1)
            box = QWidget()
            box.setLayout(hero)
            box.setCursor(Qt.CursorShape.PointingHandCursor)
            box.mouseReleaseEvent = lambda e, t=hero_track: self.play_tracks.emit(self.db.all_tracks(), t)
            layout.addWidget(box)

        layout.addWidget(SectionTitle("Recently added", self.theme))
        self._card_row(layout, self.db.recently_added(10), kind="track")
        layout.addWidget(SectionTitle("Playlists", self.theme))
        self._playlists(layout, compact=True)
        layout.addStretch()

    def _songs(self, layout: QVBoxLayout, tracks: list[dict], heading: str = "Songs") -> None:
        layout.addWidget(SectionTitle(heading if not self._query else f"Search  ·  {self._query}", self.theme))
        if not tracks:
            empty = QLabel("Nothing here yet. Add a folder of music to begin.")
            empty.setObjectName("muted")
            layout.addWidget(empty)
            layout.addStretch()
            return
        self._song_list(layout, tracks)
        layout.addStretch()

    def _song_list(self, layout: QVBoxLayout, tracks: list[dict]) -> None:
        for track in tracks:
            row = SongRow(track, self.theme)
            row.clicked.connect(lambda t=track, bundle=tracks: self.play_tracks.emit(bundle, t))
            row.favorite_toggled.connect(lambda t=track: self.toggle_favorite.emit(t["id"]))
            row.customContextMenuRequested.connect(lambda pos, t=track, w=row: self._track_menu(w, pos, t))
            layout.addWidget(row)

    def _track_menu(self, widget, pos, track: dict) -> None:
        from PyQt6.QtWidgets import QMenu

        menu = QMenu(widget)
        play = menu.addAction("Play")
        fav = menu.addAction("Remove favorite" if track.get("is_favorite") else "Add to favorites")
        playlists = self.db.playlists()
        add_menu = menu.addMenu("Add to playlist")
        actions = []
        if not playlists:
            add_menu.addAction("No playlists yet").setEnabled(False)
        for pl in playlists:
            actions.append((add_menu.addAction(pl["name"]), pl["id"]))
        chosen = menu.exec(widget.mapToGlobal(pos))
        if chosen is play:
            self.play_tracks.emit(self.db.all_tracks(), track)
        elif chosen is fav:
            self.toggle_favorite.emit(track["id"])
        else:
            for action, pid in actions:
                if chosen is action:
                    self.db.add_to_playlist(pid, track["id"])
                    break

    def _albums(self, layout: QVBoxLayout) -> None:
        layout.addWidget(SectionTitle("Albums", self.theme))
        grid_host = QWidget()
        grid = QGridLayout(grid_host)
        grid.setSpacing(14)
        albums = self.db.albums()
        if not albums:
            layout.addWidget(QLabel("No albums yet."))
            layout.addStretch()
            return
        for i, album in enumerate(albums):
            card = MediaCard(
                album["album"],
                f"{album['artist']}  ·  {album['track_count']} tracks",
                album.get("artwork_path"),
                self.theme,
            )
            card.clicked.connect(
                lambda a=album: self.show_album(a["album"], a["artist"])
            )
            grid.addWidget(card, i // 4, i % 4)
        layout.addWidget(grid_host)
        layout.addStretch()

    def _artists(self, layout: QVBoxLayout) -> None:
        layout.addWidget(SectionTitle("Artists", self.theme))
        grid_host = QWidget()
        grid = QGridLayout(grid_host)
        grid.setSpacing(14)
        artists = self.db.artists()
        if not artists:
            layout.addWidget(QLabel("No artists yet."))
            layout.addStretch()
            return
        for i, artist in enumerate(artists):
            card = MediaCard(
                artist["artist"],
                f"{artist['album_count']} albums  ·  {artist['track_count']} songs",
                artist.get("artwork_path"),
                self.theme,
            )
            card.clicked.connect(lambda a=artist: self.show_artist(a["artist"]))
            grid.addWidget(card, i // 4, i % 4)
        layout.addWidget(grid_host)
        layout.addStretch()

    def _playlists(self, layout: QVBoxLayout, compact: bool = False) -> None:
        if not compact:
            layout.addWidget(SectionTitle("Playlists", self.theme))
        playlists = self.db.playlists()
        if not playlists:
            hint = QLabel("Create a playlist from Settings or by adding songs later.")
            hint.setObjectName("muted")
            layout.addWidget(hint)
            if not compact:
                layout.addStretch()
            return
        row = QHBoxLayout()
        row.setSpacing(14)
        for pl in playlists:
            cover = self.db.playlist_cover(pl["id"])
            card = MediaCard(pl["name"], f"{pl['track_count']} tracks", cover, self.theme)
            card.clicked.connect(lambda p=pl: self.show_playlist(p["id"], p["name"]))
            row.addWidget(card)
        row.addStretch()
        host = QWidget()
        host.setLayout(row)
        layout.addWidget(host)
        if not compact:
            layout.addStretch()

    def _card_row(self, layout: QVBoxLayout, tracks: list[dict], kind: str) -> None:
        row = QHBoxLayout()
        row.setSpacing(14)
        if not tracks:
            empty = QLabel("Import music to populate this shelf.")
            empty.setObjectName("muted")
            layout.addWidget(empty)
            return
        for track in tracks:
            card = MediaCard(track["title"], track["artist"], track.get("artwork_path"), self.theme)
            card.clicked.connect(lambda t=track: self.play_tracks.emit(self.db.all_tracks(), t))
            row.addWidget(card)
        row.addStretch()
        host = QWidget()
        host.setLayout(row)
        layout.addWidget(host)
