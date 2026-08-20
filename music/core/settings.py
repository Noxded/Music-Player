from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "config"
SETTINGS_PATH = CONFIG_DIR / "settings.json"
CACHE_DIR = ROOT / "assets" / "cache"
COVERS_DIR = CACHE_DIR / "covers"
BACKGROUNDS_DIR = ROOT / "assets" / "backgrounds"

DEFAULTS: dict[str, Any] = {
    "appearance": {
        "mode": "dark",
        "accent": "#c9a27a",
        "ui_scale": 1.0,
        "glass_opacity": 0.42,
        "background_type": "image",
        "background_color": "#0b0b0e",
        "background_image": "",
        "background_opacity": 0.92,
        "background_blur": 28,
        "dark_overlay": 0.48,
    },
    "audio": {
        "volume": 0.82,
        "muted": False,
        "shuffle": False,
        "repeat": "off",
    },
    "library": {
        "music_folder": "",
        "remember_last_song": True,
        "last_track_id": None,
        "last_position_ms": 0,
    },
    "window": {
        "remember_geometry": True,
        "x": None,
        "y": None,
        "width": 1280,
        "height": 800,
        "maximized": False,
    },
}


def _deep_merge(base: dict, override: dict) -> dict:
    out = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _deep_merge(out[key], value)
        else:
            out[key] = value
    return out


class Settings:
    def __init__(self, path: Path = SETTINGS_PATH) -> None:
        self.path = path
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        COVERS_DIR.mkdir(parents=True, exist_ok=True)
        BACKGROUNDS_DIR.mkdir(parents=True, exist_ok=True)
        self._data = deepcopy(DEFAULTS)
        self.load()

    def load(self) -> None:
        if not self.path.exists():
            self.save()
            return
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                self._data = _deep_merge(DEFAULTS, raw)
        except (OSError, json.JSONDecodeError):
            self._data = deepcopy(DEFAULTS)

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self._data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def get(self, section: str, key: str, default: Any = None) -> Any:
        return self._data.get(section, {}).get(key, default)

    def set(self, section: str, key: str, value: Any, persist: bool = True) -> None:
        self._data.setdefault(section, {})[key] = value
        if persist:
            self.save()

    @property
    def data(self) -> dict[str, Any]:
        return self._data
