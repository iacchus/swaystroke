# AI Agent Instructions for Swaystroke

## Project Overview
Swaystroke is a modular Python-based gesture recognition tool for Sway/SwayFX, utilizing GTK Layer Shell and `i3ipc`.

## Architecture Details
- **`config.py`**: Settings (e.g., trigger button configuration).
- **`gesture.py`**: Handles point data and normalization.
- **`gui.py`**: Native GTK3 Layer Shell overlay for drawing gestures.
- **`storage.py`**: Manages saving and loading gestures to/from `gestures.json`.
- **`recognizer.py`**: Compares new gestures against stored templates.
- **`focus.py`**: Uses `i3ipc` to find and focus the correct window under the mouse before executing commands.
- **`main.py`**: Entry point for recording, listening, and debugging.
- **`visualizer.py`**: Imported comparison tool to see gesture matches.

## Core Dependencies
- Python 3
- `python-i3ipc`, `python-gi`, `python-xlib`, `pycairo`
- `gtk-layer-shell` library

## Command Execution & Usage
- **Listing Gestures**: `swaystroke list`
- **Recording a Gesture**: `swaystroke record [--global] [--app-id ID] [--app-class CLASS] [--get-app-id-or-class] <name> [command]`
- **Deleting a Gesture**: `swaystroke delete <name>`
- **Listening**: `swaystroke listen`
- **Debugging**: `swaystroke debug`

## Guidelines for Agents
1. **Module Separation**: Keep UI logic inside `gui.py` and logic/comparison inside `recognizer.py`/`gesture.py`.
2. **GTK/Wayland Specifics**: Assume a Wayland environment (Sway). Use `i3ipc` for window management interactions in `focus.py`.
3. **Running the App**: If making changes, instruct the user to run using the command pattern: `swaystroke <command>`.
