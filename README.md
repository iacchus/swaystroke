# Swaystroke

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

## Installation

Swaystroke requires GTK3, GTK Layer Shell, and PyGObject bindings. These are best installed via your system package manager.

### Arch Linux

Install the required system dependencies:
```bash
sudo pacman -S gtk3 gtk-layer-shell python-gobject python-cairo
```
Then install Swaystroke via `pip` or `pipx`:
```bash
pipx install swaystroke
```
*(Note: `pipx` is recommended for installing Python applications in isolated environments.)*

### Debian / Ubuntu

Install the required system dependencies:
```bash
sudo apt update
sudo apt install libgtk-3-0 libgtk-layer-shell0 gir1.2-gtk-3.0 gir1.2-gtklayershell-0.1 python3-gi python3-gi-cairo python3-pip pipx
```
Then install Swaystroke via `pipx`:
```bash
pipx install swaystroke
```

## Usage

### Record a gesture
```bash
swaystroke record [--global] [--app-id ID] [--app-class CLASS] [--get-app-id-or-class] <name> [command]
```
Click and drag to draw your gesture in the transparent overlay.
Options:
- `--global`: Record the gesture to be available globally.
- `--app-id ID`: Bind the gesture to a specific Wayland application ID.
- `--app-class CLASS`: Bind the gesture to a specific XWayland window class.
- `--get-app-id-or-class`: Automatically get the app ID or class from the window under the gesture.

If no options are provided, it defaults to a global gesture.

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

### Delete a gesture
```bash
swaystroke delete "close"
```
Delete a recorded gesture by its name.

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

