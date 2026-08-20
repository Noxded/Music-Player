from __future__ import annotations

import hashlib
from io import BytesIO
from pathlib import Path

from mutagen import File as MutagenFile
from mutagen.flac import FLAC, Picture
from mutagen.id3 import ID3
from mutagen.mp4 import MP4
from PIL import Image

from core.settings import COVERS_DIR

AUDIO_EXTENSIONS = {
    ".mp3",
    ".wav",
    ".flac",
    ".ogg",
    ".oga",
    ".m4a",
    ".aac",
    ".wma",
    ".mp4",
    ".opus",
    ".aiff",
    ".aif",
}


def _text(value: object, fallback: str) -> str:
    if value is None:
        return fallback
    if isinstance(value, list):
        value = value[0] if value else fallback
    text = str(value).strip()
    return text or fallback


def _save_artwork(data: bytes, stem: str) -> str | None:
    try:
        image = Image.open(BytesIO(data))
        image = image.convert("RGB")
        image.thumbnail((640, 640), Image.Resampling.LANCZOS)
        digest = hashlib.sha1(data[:4096] + stem.encode("utf-8")).hexdigest()[:20]
        dest = COVERS_DIR / f"{digest}.jpg"
        if not dest.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
            image.save(dest, "JPEG", quality=88)
        return str(dest)
    except Exception:
        return None


def _extract_artwork(audio, path: Path) -> str | None:
    try:
        if isinstance(audio, MP4) and audio.tags and "covr" in audio.tags:
            cover = audio.tags["covr"][0]
            data = bytes(cover)
            return _save_artwork(data, path.stem)
        if isinstance(audio, FLAC) and audio.pictures:
            return _save_artwork(audio.pictures[0].data, path.stem)
        if audio is not None and getattr(audio, "tags", None):
            tags = audio.tags
            if tags is None:
                return None
            for key in tags:
                frame = tags[key]
                if hasattr(frame, "data") and "APIC" in str(key):
                    return _save_artwork(frame.data, path.stem)
                if isinstance(frame, list) and frame and isinstance(frame[0], Picture):
                    return _save_artwork(frame[0].data, path.stem)
        try:
            id3 = ID3(path)
            for key in id3:
                if key.startswith("APIC"):
                    return _save_artwork(id3[key].data, path.stem)
        except Exception:
            pass
    except Exception:
        return None
    return None


def read_metadata(path: str | Path) -> dict:
    file_path = Path(path)
    title = file_path.stem
    artist = "Unknown Artist"
    album = "Unknown Album"
    duration_ms = 0
    year = None
    genre = None
    track_number = None
    artwork_path = None

    try:
        audio = MutagenFile(file_path)
        if audio is not None:
            info = getattr(audio, "info", None)
            if info is not None and getattr(info, "length", None):
                duration_ms = int(float(info.length) * 1000)
            tags = audio.tags or {}
            easy = {}
            for key in ("title", "artist", "album", "date", "genre", "tracknumber"):
                if key in tags:
                    easy[key] = tags[key]
            if hasattr(tags, "get"):
                title = _text(tags.get("title") or tags.get("TIT2") or tags.get("\xa9nam"), title)
                artist = _text(
                    tags.get("artist") or tags.get("TPE1") or tags.get("\xa9ART"),
                    artist,
                )
                album = _text(
                    tags.get("album") or tags.get("TALB") or tags.get("\xa9alb"),
                    album,
                )
                year = _text(tags.get("date") or tags.get("TDRC") or tags.get("\xa9day"), "") or None
                genre = _text(tags.get("genre") or tags.get("TCON") or tags.get("\xa9gen"), "") or None
                track_raw = tags.get("tracknumber") or tags.get("TRCK") or tags.get("trkn")
                if track_raw:
                    raw = track_raw[0] if isinstance(track_raw, list) else track_raw
                    if isinstance(raw, tuple):
                        track_number = int(raw[0]) if raw else None
                    else:
                        text = str(raw).split("/")[0]
                        if text.isdigit():
                            track_number = int(text)
            artwork_path = _extract_artwork(audio, file_path)
    except Exception:
        pass

    return {
        "path": str(file_path),
        "title": title,
        "artist": artist,
        "album": album,
        "duration_ms": duration_ms,
        "year": year,
        "genre": genre,
        "track_number": track_number,
        "artwork_path": artwork_path,
    }


def iter_audio_files(folder: str | Path) -> list[Path]:
    root = Path(folder)
    if not root.exists():
        return []
    files: list[Path] = []
    for item in root.rglob("*"):
        if item.is_file() and item.suffix.lower() in AUDIO_EXTENSIONS:
            files.append(item)
    return files
