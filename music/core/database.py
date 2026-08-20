from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from core.settings import CONFIG_DIR

DB_PATH = CONFIG_DIR / "library.db"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Database:
    def __init__(self, path: Path = DB_PATH) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self.conn = sqlite3.connect(str(path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._init()

    def _init(self) -> None:
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS tracks (
                id INTEGER PRIMARY KEY,
                path TEXT NOT NULL UNIQUE,
                title TEXT NOT NULL,
                artist TEXT NOT NULL DEFAULT 'Unknown Artist',
                album TEXT NOT NULL DEFAULT 'Unknown Album',
                duration_ms INTEGER NOT NULL DEFAULT 0,
                year TEXT,
                genre TEXT,
                track_number INTEGER,
                artwork_path TEXT,
                date_added TEXT NOT NULL,
                last_played TEXT,
                play_count INTEGER NOT NULL DEFAULT 0,
                is_favorite INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS playlists (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS playlist_tracks (
                playlist_id INTEGER NOT NULL,
                track_id INTEGER NOT NULL,
                position INTEGER NOT NULL,
                PRIMARY KEY (playlist_id, track_id),
                FOREIGN KEY (playlist_id) REFERENCES playlists(id) ON DELETE CASCADE,
                FOREIGN KEY (track_id) REFERENCES tracks(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS recently_played (
                id INTEGER PRIMARY KEY,
                track_id INTEGER NOT NULL,
                played_at TEXT NOT NULL,
                FOREIGN KEY (track_id) REFERENCES tracks(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_tracks_artist ON tracks(artist);
            CREATE INDEX IF NOT EXISTS idx_tracks_album ON tracks(album);
            CREATE INDEX IF NOT EXISTS idx_recent ON recently_played(played_at DESC);
            """
        )
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def upsert_track(self, data: dict[str, Any]) -> int:
        existing = self.conn.execute(
            "SELECT id, is_favorite, play_count, last_played FROM tracks WHERE path = ?",
            (data["path"],),
        ).fetchone()
        if existing:
            self.conn.execute(
                """
                UPDATE tracks SET title=?, artist=?, album=?, duration_ms=?, year=?,
                    genre=?, track_number=?, artwork_path=?
                WHERE id=?
                """,
                (
                    data["title"],
                    data["artist"],
                    data["album"],
                    data.get("duration_ms", 0),
                    data.get("year"),
                    data.get("genre"),
                    data.get("track_number"),
                    data.get("artwork_path"),
                    existing["id"],
                ),
            )
            self.conn.commit()
            return int(existing["id"])

        cur = self.conn.execute(
            """
            INSERT INTO tracks (
                path, title, artist, album, duration_ms, year, genre,
                track_number, artwork_path, date_added
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["path"],
                data["title"],
                data["artist"],
                data["album"],
                data.get("duration_ms", 0),
                data.get("year"),
                data.get("genre"),
                data.get("track_number"),
                data.get("artwork_path"),
                _now(),
            ),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def remove_track(self, track_id: int) -> None:
        self.conn.execute("DELETE FROM tracks WHERE id = ?", (track_id,))
        self.conn.commit()

    def get_track(self, track_id: int) -> dict[str, Any] | None:
        row = self.conn.execute("SELECT * FROM tracks WHERE id = ?", (track_id,)).fetchone()
        return dict(row) if row else None

    def all_tracks(self, query: str = "") -> list[dict[str, Any]]:
        if query:
            like = f"%{query.lower()}%"
            rows = self.conn.execute(
                """
                SELECT * FROM tracks
                WHERE lower(title) LIKE ? OR lower(artist) LIKE ? OR lower(album) LIKE ?
                ORDER BY title COLLATE NOCASE
                """,
                (like, like, like),
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT * FROM tracks ORDER BY title COLLATE NOCASE"
            ).fetchall()
        return [dict(r) for r in rows]

    def recently_added(self, limit: int = 12) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT * FROM tracks ORDER BY date_added DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]

    def favorites(self) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT * FROM tracks WHERE is_favorite = 1 ORDER BY title COLLATE NOCASE"
        ).fetchall()
        return [dict(r) for r in rows]

    def set_favorite(self, track_id: int, favorite: bool) -> None:
        self.conn.execute(
            "UPDATE tracks SET is_favorite = ? WHERE id = ?",
            (1 if favorite else 0, track_id),
        )
        self.conn.commit()

    def toggle_favorite(self, track_id: int) -> bool:
        row = self.get_track(track_id)
        if not row:
            return False
        nxt = not bool(row["is_favorite"])
        self.set_favorite(track_id, nxt)
        return nxt

    def mark_played(self, track_id: int) -> None:
        self.conn.execute(
            "UPDATE tracks SET last_played = ?, play_count = play_count + 1 WHERE id = ?",
            (_now(), track_id),
        )
        self.conn.execute(
            "INSERT INTO recently_played (track_id, played_at) VALUES (?, ?)",
            (track_id, _now()),
        )
        self.conn.execute(
            """
            DELETE FROM recently_played WHERE id NOT IN (
                SELECT id FROM recently_played ORDER BY played_at DESC LIMIT 200
            )
            """
        )
        self.conn.commit()

    def recently_played(self, limit: int = 40) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            """
            SELECT t.* FROM recently_played r
            JOIN tracks t ON t.id = r.track_id
            GROUP BY t.id
            ORDER BY MAX(r.played_at) DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]

    def albums(self) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            """
            SELECT album, artist, COUNT(*) AS track_count,
                   MIN(artwork_path) AS artwork_path, MIN(id) AS sample_id
            FROM tracks
            GROUP BY album, artist
            ORDER BY album COLLATE NOCASE
            """
        ).fetchall()
        return [dict(r) for r in rows]

    def album_tracks(self, album: str, artist: str) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            """
            SELECT * FROM tracks WHERE album = ? AND artist = ?
            ORDER BY COALESCE(track_number, 9999), title COLLATE NOCASE
            """,
            (album, artist),
        ).fetchall()
        return [dict(r) for r in rows]

    def artists(self) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            """
            SELECT artist, COUNT(*) AS track_count, COUNT(DISTINCT album) AS album_count,
                   MIN(artwork_path) AS artwork_path
            FROM tracks
            GROUP BY artist
            ORDER BY artist COLLATE NOCASE
            """
        ).fetchall()
        return [dict(r) for r in rows]

    def artist_tracks(self, artist: str) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT * FROM tracks WHERE artist = ? ORDER BY album, COALESCE(track_number, 9999)",
            (artist,),
        ).fetchall()
        return [dict(r) for r in rows]

    def create_playlist(self, name: str) -> int:
        cur = self.conn.execute(
            "INSERT INTO playlists (name, created_at) VALUES (?, ?)",
            (name, _now()),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def rename_playlist(self, playlist_id: int, name: str) -> None:
        self.conn.execute("UPDATE playlists SET name = ? WHERE id = ?", (name, playlist_id))
        self.conn.commit()

    def delete_playlist(self, playlist_id: int) -> None:
        self.conn.execute("DELETE FROM playlists WHERE id = ?", (playlist_id,))
        self.conn.commit()

    def playlists(self) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            """
            SELECT p.*, COUNT(pt.track_id) AS track_count
            FROM playlists p
            LEFT JOIN playlist_tracks pt ON pt.playlist_id = p.id
            GROUP BY p.id
            ORDER BY p.name COLLATE NOCASE
            """
        ).fetchall()
        return [dict(r) for r in rows]

    def playlist_tracks(self, playlist_id: int) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            """
            SELECT t.* FROM playlist_tracks pt
            JOIN tracks t ON t.id = pt.track_id
            WHERE pt.playlist_id = ?
            ORDER BY pt.position
            """,
            (playlist_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def add_to_playlist(self, playlist_id: int, track_id: int) -> None:
        row = self.conn.execute(
            "SELECT COALESCE(MAX(position), -1) + 1 AS pos FROM playlist_tracks WHERE playlist_id = ?",
            (playlist_id,),
        ).fetchone()
        try:
            self.conn.execute(
                "INSERT INTO playlist_tracks (playlist_id, track_id, position) VALUES (?, ?, ?)",
                (playlist_id, track_id, int(row["pos"])),
            )
            self.conn.commit()
        except sqlite3.IntegrityError:
            pass

    def remove_from_playlist(self, playlist_id: int, track_id: int) -> None:
        self.conn.execute(
            "DELETE FROM playlist_tracks WHERE playlist_id = ? AND track_id = ?",
            (playlist_id, track_id),
        )
        self.conn.commit()

    def playlist_cover(self, playlist_id: int) -> str | None:
        row = self.conn.execute(
            """
            SELECT t.artwork_path FROM playlist_tracks pt
            JOIN tracks t ON t.id = pt.track_id
            WHERE pt.playlist_id = ? AND t.artwork_path IS NOT NULL AND t.artwork_path != ''
            ORDER BY pt.position LIMIT 1
            """,
            (playlist_id,),
        ).fetchone()
        return row["artwork_path"] if row else None

    def stats(self) -> dict[str, int]:
        tracks = self.conn.execute("SELECT COUNT(*) AS n FROM tracks").fetchone()["n"]
        return {"tracks": int(tracks)}
