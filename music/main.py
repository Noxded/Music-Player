from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_MEDIA_BACKEND", "ffmpeg")

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QGuiApplication
from PyQt6.QtWidgets import QApplication

from core.database import Database
from core.settings import Settings
from ui.main_window import MainWindow


def main() -> None:
    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setApplicationName("Aria")
    app.setOrganizationName("Aria")
    font = QFont("Segoe UI", 10)
    font.setHintingPreference(QFont.HintingPreference.PreferFullHinting)
    app.setFont(font)

    settings = Settings()
    db = Database()
    window = MainWindow(settings, db)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
