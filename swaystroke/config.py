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
HISTORY_FILE = os.path.join(CONFIG_DIR, 'gestures_history.json')
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
    "multistroke_timeout": 500,
    "history_limit": 30
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
    "multistroke_timeout": 500,
    "history_limit": 30
}

if os.path.exists(CONFIG_FILE):
    try:
        with open(CONFIG_FILE, 'rb') as f:
            user_config = tomllib.load(f)
            for section in ["trail", "overlay"]:
                if section in user_config:
                    for key, val in user_config[section].items():
                        CONFIG[section][key] = val
            if "multistroke_timeout" in user_config:
                CONFIG["multistroke_timeout"] = user_config["multistroke_timeout"]
            elif "general" in user_config and "multistroke_timeout" in user_config["general"]:
                CONFIG["multistroke_timeout"] = user_config["general"]["multistroke_timeout"]
                
            if "history_limit" in user_config:
                CONFIG["history_limit"] = user_config["history_limit"]
            elif "general" in user_config and "history_limit" in user_config["general"]:
                CONFIG["history_limit"] = user_config["general"]["history_limit"]
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

[general]
multistroke_timeout = 500
history_limit = 30
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

def save_config():
    import datetime
    import shutil
    
    if os.path.exists(CONFIG_FILE):
        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_file = f"{CONFIG_FILE}.{timestamp}.backup"
        try:
            shutil.copy2(CONFIG_FILE, backup_file)
            print(f"Backed up config to {backup_file}")
        except Exception as e:
            print(f"Error backing up config: {e}")
            
    try:
        with open(CONFIG_FILE, 'w') as f:
            f.write("[trail]\n")
            f.write(f'color = "{CONFIG["trail"]["color"]}"\n')
            f.write(f'opacity = {CONFIG["trail"]["opacity"]}\n')
            f.write(f'width = {CONFIG["trail"]["width"]}\n\n')
            
            f.write("[overlay]\n")
            f.write(f'color = "{CONFIG["overlay"]["color"]}"\n')
            f.write(f'opacity = {CONFIG["overlay"]["opacity"]}\n')
            f.write(f'text = "{CONFIG["overlay"]["text"]}"\n\n')
            
            f.write("[general]\n")
            f.write(f'multistroke_timeout = {CONFIG["multistroke_timeout"]}\n')
            f.write(f'history_limit = {CONFIG["history_limit"]}\n')
    except Exception as e:
        print(f"Error saving {CONFIG_FILE}: {e}")

# Recognition threshold (higher is more strict)
MATCH_THRESHOLD = 0.8
