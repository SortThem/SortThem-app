# SortThem-App

Image Organizer Application - Sort images by moving them into categorized directories using keyboard shortcuts.

## Features

- Full-screen image viewer with zoom support
- QWERTY keyboard layout buttons for sorting
- Move images to subdirectories with single key press
- Persistent key bindings saved in user config directory
- Visual feedback for which category current image belongs to
- Navigate images with arrow keys
- Move images back to root directory with Backspace

## Requirements

- Python 3.10+
- Pygame 2.6.0+

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python main.py
```

## Usage

    Arrow Keys: Navigate between images

    Letter Keys: Move current image to bound directory (or create new binding)

    Backspace: Move current image back to root directory

    Mouse Wheel: Zoom in/out on image

    ESC: Exit application

## Configuration

Key bindings are automatically saved to:

    Linux: ~/.config/sortthem/config.ini

    Windows: %APPDATA%/sortthem/config.ini


## Project Structure

SortThem-App/
├── main.py              # Entry point
├── app/                 # Application core
├── core/                # Core functionality
├── ui/                  # UI components
└── utils/               # Utilities

## License

MIT License

