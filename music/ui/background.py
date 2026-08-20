from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QObject, QSize, pyqtSignal, QThread
from PyQt6.QtGui import QImage, QPixmap
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter
from PIL.ImageQt import ImageQt

from core.settings import BACKGROUNDS_DIR, Settings


def ensure_default_background() -> Path:
    dest = BACKGROUNDS_DIR / "default.jpg"
    if dest.exists():
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    w, h = 1920, 1080
    img = Image.new("RGB", (w, h), (8, 8, 12))
    draw = ImageDraw.Draw(img, "RGBA")
    draw.ellipse((-200, -100, 900, 800), fill=(70, 40, 28, 90))
    draw.ellipse((900, 200, 2100, 1400), fill=(28, 36, 70, 80))
    draw.ellipse((400, 500, 1600, 1400), fill=(20, 16, 18, 110))
    img = img.filter(ImageFilter.GaussianBlur(80))
    img.save(dest, "JPEG", quality=90)
    return dest


class _BgWorker(QThread):
    ready = pyqtSignal(object)

    def __init__(self, settings: Settings, size: QSize) -> None:
        super().__init__()
        self.settings = settings
        self.size = size

    def run(self) -> None:
        w, h = max(16, self.size.width()), max(16, self.size.height())
        appearance = self.settings.data["appearance"]
        kind = appearance.get("background_type", "image")
        if kind == "color":
            color = appearance.get("background_color") or "#0b0b0e"
            img = Image.new("RGB", (w, h), color)
        else:
            path = appearance.get("background_image") or ""
            src = Path(path) if path and Path(path).exists() else ensure_default_background()
            try:
                raw = Image.open(src).convert("RGB")
            except Exception:
                raw = Image.open(ensure_default_background()).convert("RGB")
            raw = ImageEnhance.Brightness(raw).enhance(float(appearance.get("background_opacity", 0.92)))
            ratio = max(w / raw.width, h / raw.height)
            nw, nh = int(raw.width * ratio), int(raw.height * ratio)
            raw = raw.resize((nw, nh), Image.Resampling.LANCZOS)
            left = (nw - w) // 2
            top = (nh - h) // 2
            img = raw.crop((left, top, left + w, top + h))
            blur = int(appearance.get("background_blur", 24))
            if blur > 0:
                img = img.filter(ImageFilter.GaussianBlur(blur))
        overlay = float(appearance.get("dark_overlay", 0.45))
        if overlay > 0:
            shade = Image.new("RGB", (w, h), (6, 6, 8) if appearance.get("mode") != "light" else (240, 236, 228))
            img = Image.blend(img, shade, overlay)
        qimage = ImageQt(img.convert("RGBA"))
        pix = QPixmap.fromImage(QImage(qimage).copy())
        self.ready.emit(pix)


class BackgroundRenderer(QObject):
    updated = pyqtSignal(object)

    def __init__(self, settings: Settings) -> None:
        super().__init__()
        self.settings = settings
        self._worker: _BgWorker | None = None
        self._pending: QSize | None = None

    def request(self, size: QSize) -> None:
        if size.width() < 40 or size.height() < 40:
            return
        if self._worker and self._worker.isRunning():
            self._pending = size
            return
        self._worker = _BgWorker(self.settings, size)
        self._worker.ready.connect(self._done)
        self._worker.start()

    def _done(self, pixmap: QPixmap) -> None:
        self.updated.emit(pixmap)
        if self._pending is not None:
            size = self._pending
            self._pending = None
            self.request(size)
