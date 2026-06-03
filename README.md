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

### Gesture Recognition Algorithm

Swaystroke uses a simplified implementation of the **$1 Unistroke Recognizer** algorithm (specifically, a point-cloud matching variation) to identify gestures:
1. **Resampling:** The drawn path is resampled into a fixed number of evenly spaced points (32 points) so that the speed of drawing doesn't affect the shape.
2. **Scaling:** The points are scaled to fit within a standardized bounding box (1x1) so that the size of the gesture doesn't matter.
3. **Translation:** The points are translated so that the centroid (center of mass) of the gesture sits at the origin `(0, 0)`.
4. **Matching:** It computes the average Euclidean distance between the corresponding points of the drawn gesture and the stored templates. The closest match (with the lowest average distance) is selected as the recognized gesture.

*Swaystroke also features **Directional Invariance** (gestures are matched both forwards and backwards) and **Multi-stroke support** (you can lift your mouse to draw complex shapes like an "X" before the timeout triggers).*

## Installation

Swaystroke requires GTK3, GTK Layer Shell, and PyGObject bindings. These are best installed via your system package manager.

### Arch Linux

Install the required system dependencies:
```bash
sudo pacman -S gtk3 gtk-layer-shell python-gobject python-cairo python-pipx
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
swaystroke record [--type TYPE] [--global] [--app-id ID] [--app-class CLASS] [--get-app-id-or-class] <name> [command]
```
Click and drag to draw your gesture in the transparent overlay.
Options:
- `--type`: Action type to execute: `command` (default shell command), `key` (native wayland keypress via wtype/ydotool), `text` (native text typing).
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

### Daemon Mode (Zero-Latency)
For zero startup latency, you can run Swaystroke in daemon mode. This keeps the GTK overlay in the background.
```bash
swaystroke daemon &
```
Trigger the listening overlay instantly via:
```bash
swaystroke trigger
```
Bind `swaystroke trigger` to a mouse button in your sway config for the best experience.

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

