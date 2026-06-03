import evdev

# The button that triggers gesture recording.
# BTN_RIGHT (273) is common for Easystroke-like behavior.
# BTN_SIDE (275) or BTN_EXTRA (276) are also good candidates for many mice.
TRIGGER_BUTTON = evdev.ecodes.BTN_RIGHT

import os
import tomllib

# Path to save gestures
XDG_CONFIG_HOME = os.environ.get('XDG_CONFIG_HOME', os.path.expanduser('~/.config'))
CONFIG_DIR = os.path.join(XDG_CONFIG_HOME, 'swaystroke')
GESTURE_FILE = os.path.join(CONFIG_DIR, 'gestures.json')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'config.toml')

os.makedirs(CONFIG_DIR, exist_ok=True)

# Default configurations
DEFAULT_CONFIG = {
    "trail": {
        "color": "#ff0000",
        "opacity": 1.0,
        "width": 4
    },
    "overlay": {
        "color": "#000000",
        "opacity": 0.1,
        "text": ""
    },
    "multistroke_timeout": 500
}

CONFIG = {
    "trail": {
        "color": "#ff0000",
        "opacity": 1.0,
        "width": 4
    },
    "overlay": {
        "color": "#000000",
        "opacity": 0.1,
        "text": ""
    },
    "multistroke_timeout": 500
}

if os.path.exists(CONFIG_FILE):
    try:
        with open(CONFIG_FILE, 'rb') as f:
            user_config = tomllib.load(f)
            for section in ["trail", "overlay"]:
                if section in user_config:
                    for key, val in user_config[section].items():
                        CONFIG[section][key] = val
    except Exception as e:
        print(f"Error loading {CONFIG_FILE}: {e}")
DEFAULT_TOML = """[trail]
color = "#ff0000"
opacity = 1.0
width = 4

[overlay]
color = "#000000"
opacity = 0.1
text = "Swaystroke is listening for gesture..."
"""

def generate_default_config():
    if os.path.exists(CONFIG_FILE):
        print(f"Config file already exists at {CONFIG_FILE}")
        return
    try:
        with open(CONFIG_FILE, 'w') as f:
            f.write(DEFAULT_TOML)
        print(f"Generated default config at {CONFIG_FILE}")
    except Exception as e:
        print(f"Error creating {CONFIG_FILE}: {e}")

# Recognition threshold (higher is more strict)
MATCH_THRESHOLD = 0.8
