# Swaystroke PoC

A modular Python-based gesture recognition tool for Sway/SwayFX (using GTK Layer Shell and `i3ipc`).

## Architecture

- `config.py`: Settings like the trigger button.
- `gesture.py`: Handles point data and normalization.
- `gui.py`: Native GTK3 Layer Shell overlay for drawing gestures.
- `storage.py`: Manages saving and loading gestures to `gestures.json`.
- `recognizer.py`: Compares new gestures against stored templates.
- `focus.py`: Uses `i3ipc` to find and focus the correct window under the mouse before executing commands.
- `main.py`: Entry point for recording, listening, and debugging.
- `visualizer.py`: Imported comparison tool to see gesture matches.

## Prerequisites

- Python 3
- `python-i3ipc`, `python-gi`, `python-xlib`, `pycairo`
- `gtk-layer-shell` library

## Usage

### Record a gesture
```bash
swaystroke record "close" "swaymsg kill"
```
Click and drag to draw your gesture in the transparent overlay.

### Listen for gestures
```bash
swaystroke listen
```
Draw your gesture. The tool will identify the window under your starting point, focus it, and run the command.

### List gestures
```bash
swaystroke list
swaystroke list-gui
```
Show all recorded gestures either in an ASCII table or a scrollable graphical window.

### Show a specific gesture
```bash
swaystroke show "close"
```
Open the visualizer to display the recorded path for a specific gesture.

### Debug gestures
```bash
swaystroke debug
```
Draw a gesture to see a side-by-side comparison with the closest match.

### Generate config
```bash
swaystroke generate-config
```
Generate the default configuration file in the config directory.

