# Aria Music Player

A modern desktop music player built with Python and PyQt6, inspired by premium glassmorphism audio apps. It includes a translucent interface, customizable background, music library browsing, queue controls, favorites, and playback controls.

## Features

- Frameless glassmorphism desktop UI
- Dark cinematic default theme
- Customizable background image or solid color
- Adjustable background opacity, blur, and dark overlay
- Music library with album/artist/song views
- Playback controls: play, pause, previous, next, seek, shuffle, repeat
- Favorite tracking and queue management
- Metadata extraction with embedded album art support
- Supports common audio formats including MP3, WAV, FLAC, OGG, M4A, AAC, WMA, MP4, and OPUS when available in the backend

## Tech Stack

- Python
- PyQt6
- Mutagen
- Pillow

## Project Structure

```text
music/
├── main.py
├── requirements.txt
├── README.md
├── assets/
│   ├── backgrounds/
│   └── icons/
├── config/
│   └── settings.json
├── core/
│   ├── __init__.py
│   ├── database.py
│   ├── library.py
│   ├── metadata.py
│   ├── player.py
│   ├── playlist.py
│   └── settings.py
└── ui/
    ├── __init__.py
    ├── background.py
    ├── components.py
    ├── main_window.py
    ├── music_library.py
    ├── player_bar.py
    ├── settings_panel.py
    ├── sidebar.py
    └── styles.py
```

## Requirements

Python 3.10+ recommended.

Install dependencies:

```bash
pip install -r requirements.txt
```

## Run the app

From the project folder:

```bash
python main.py
```

## Notes

- The app uses Qt Multimedia with FFmpeg, so FFmpeg support is recommended for smoother playback and format compatibility.
- Settings are stored in `config/settings.json`.
- You can import a default music folder from the settings panel or add music from the sidebar.

## License

This project is provided as-is for learning and personal use.
