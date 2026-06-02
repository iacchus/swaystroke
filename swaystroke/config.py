import evdev

# The button that triggers gesture recording.
# BTN_RIGHT (273) is common for Easystroke-like behavior.
# BTN_SIDE (275) or BTN_EXTRA (276) are also good candidates for many mice.
TRIGGER_BUTTON = evdev.ecodes.BTN_RIGHT

import os

# Path to save gestures
XDG_CONFIG_HOME = os.environ.get('XDG_CONFIG_HOME', os.path.expanduser('~/.config'))
CONFIG_DIR = os.path.join(XDG_CONFIG_HOME, 'swaystroke')
GESTURE_FILE = os.path.join(CONFIG_DIR, 'gestures.json')

# Recognition threshold (higher is more strict)
MATCH_THRESHOLD = 0.8
