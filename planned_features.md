# Planned Features

Based on mature gesture recognition tools like **Easystroke** and the current state of **Swaystroke**, here are some functionalities and quality-of-life features that are currently lacking or could be improved:

### 1. GUI Management (CRUD operations)
*   **Editing in GUI:** The `list-gui` command is currently read-only. It would be great to have a full settings window where you can delete gestures, change their assigned commands, or modify their assigned app IDs/classes without having to drop to the terminal.
*   **Re-recording:** The ability to keep the gesture's command/app-id but re-draw the shape if you aren't happy with it.

### 2. Daemon Mode / Startup Latency
*   Currently, when you trigger a gesture via Sway, it spawns a fresh Python process (`swaystroke listen`). This can introduce a tiny bit of latency (Python interpreter startup overhead + GTK window creation).
*   **Improvement:** A daemon mode that stays running in the background and simply shows/hides a pre-warmed GTK overlay instantly when signaled (e.g., via a socket, `SIGUSR1`, or DBus) would make the interface feel much snappier.

### 3. Native Key Presses / Text Input
*   Right now, you map gestures to shell commands. If you want to simulate key presses, you have to use external tools in the command (like `ydotool` or `wtype`).
*   **Improvement:** Native integration for "Action Types" (e.g., *Command*, *Key press*, *Text snippet*), generating Wayland-native virtual keystrokes directly.

### 4. Advanced Gesture Recognition
*   **Multi-stroke gestures:** Swaystroke uses a unistroke recognizer (one continuous click-and-drag). You can't draw gestures that require you to lift the mouse (like an "X" or a "t").
*   **Directional invariance:** Whether it cares if you draw a circle clockwise vs counter-clockwise. (Right now, drawing direction *does* matter).

### 5. Advanced Triggering & Overlays
*   **Scroll actions:** Binding gestures to scroll wheels while holding a modifier button.
*   **Timeout/Cancel:** Cancelling the gesture automatically if you hold the mouse completely still for 1-2 seconds, or by right-clicking while drawing.
*   **Visual Customization:** Allowing users to configure the line thickness, color, and fading effects of the drawing trail in `config.py`.
