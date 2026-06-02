import evdev

# The button that triggers gesture recording.
# BTN_RIGHT (273) is common for Easystroke-like behavior.
# BTN_SIDE (275) or BTN_EXTRA (276) are also good candidates for many mice.
TRIGGER_BUTTON = evdev.ecodes.BTN_RIGHT

# Path to save gestures
GESTURE_FILE = "gestures.json"

# Recognition threshold (higher is more strict)
MATCH_THRESHOLD = 0.8
