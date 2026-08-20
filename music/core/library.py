from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal, QThread

from core.database import Database
from core.metadata import AUDIO_EXTENSIONS, iter_audio_files, read_metadata


class ScanWorker(QThread):
    progress = pyqtSignal(int, int, str)
    finished_ok = pyqtSignal(int)
    failed = pyqtSignal(str)

    def __init__(self, paths: list[str], db_path: str) -> None:
        super().__init__()
        self.paths = paths
        self.db_path = db_path

    def run(self) -> None:
        try:
            db = Database(Path(self.db_path))
            files: list[Path] = []
            for raw in self.paths:
                path = Path(raw)
                if path.is_dir():
                    files.extend(iter_audio_files(path))
                elif path.is_file() and path.suffix.lower() in AUDIO_EXTENSIONS:
                    files.append(path)
            total = len(files)
            added = 0
            for i, file in enumerate(files, start=1):
                self.progress.emit(i, total, file.name)
                meta = read_metadata(file)
                db.upsert_track(meta)
                added += 1
            db.close()
            self.finished_ok.emit(added)
        except Exception as exc:
            self.failed.emit(str(exc))


class LibraryController(QObject):
    scan_progress = pyqtSignal(int, int, str)
    scan_finished = pyqtSignal(int)
    scan_failed = pyqtSignal(str)
    changed = pyqtSignal()

    def __init__(self, db: Database) -> None:
        super().__init__()
        self.db = db
        self._worker: ScanWorker | None = None

    def import_paths(self, paths: list[str]) -> None:
        if self._worker and self._worker.isRunning():
            return
        self._worker = ScanWorker(paths, str(self.db.path))
        self._worker.progress.connect(self.scan_progress.emit)
        self._worker.finished_ok.connect(self._done)
        self._worker.failed.connect(self.scan_failed.emit)
        self._worker.start()

    def _done(self, count: int) -> None:
        self.scan_finished.emit(count)
        self.changed.emit()
