import sys
import subprocess
import time
from .config import GESTURE_FILE, generate_default_config
from .storage import StorageManager
from .recognizer import Recognizer
from .gesture import Gesture
from .overlay import capture_gesture_gui
from .focus import focus_window_at, get_window_info_at
from .visualizer import GestureVisualizer
from .list_window import show_gesture_list

def print_help():
    print("Swaystroke - A gesture recognition tool for Sway/Wayland")
    print("\nUsage: swaystroke <command> [args...]")
    print("\nCommands:")
    print("  list                       - Print an ASCII table of all recorded gestures and their commands")
    print("  list-gui                   - Show a scrollable, graphical window of all recorded gestures")
    print("  record [--global] [--app-id ID] [--app-class CLASS] [--get-app-id-or-class] <name> [command]")
    print("                             - Record a new gesture with the given name and map it to a shell command")
    print("  listen                     - Listen for a gesture and execute the corresponding command")
    print("  debug                      - Listen for a gesture and open the visualizer to show the match and score")
    print("  show <name>                - Open the visualizer to display the recorded path for a specific gesture")
    print("  generate-config            - Generate the default configuration file in the config directory")
    print("  help, --help, -h           - Show this help message")

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ["help", "--help", "-h"]:
        print_help()
        sys.exit(0 if len(sys.argv) > 1 else 1)

    mode = sys.argv[1]

    if mode == "generate-config":
        generate_default_config()
        sys.exit(0)

    storage = StorageManager(GESTURE_FILE)

    if mode == "record":
        args = sys.argv[2:]
        app_id = None
        app_class = None
        is_global = False
        get_app_id_or_class = False
        
        positional_args = []
        i = 0
        while i < len(args):
            arg = args[i]
            if arg == "--global":
                is_global = True
            elif arg == "--get-app-id-or-class":
                get_app_id_or_class = True
            elif arg == "--app-id":
                if i + 1 < len(args):
                    app_id = args[i+1]
                    i += 1
            elif arg == "--app-class":
                if i + 1 < len(args):
                    app_class = args[i+1]
                    i += 1
            else:
                positional_args.append(arg)
            i += 1
                
        if not positional_args:
            print("Please provide a name for the gesture.")
            print("Usage: swaystroke record [--global] [--app-id ID] [--app-class CLASS] [--get-app-id-or-class] <name> [command]")
            sys.exit(1)
            
        name = positional_args[0]
        command = positional_args[1] if len(positional_args) > 1 else None
        
        templates = storage.load_all()
        if any(g.name == name for g in templates):
            resp = input(f"Gesture '{name}' already exists. Overwrite? [y/N]: ")
            if resp.lower() != 'y':
                print("Aborting.")
                sys.exit(0)
        
        print(f"A transparent overlay will appear. Click and drag to draw '{name}'. Press Esc to cancel.")
        gesture = capture_gesture_gui()
        
        if gesture:
            if get_app_id_or_class:
                from .focus import get_window_info_at
                start_x, start_y = gesture.points[0]
                win_app_id, win_app_class = get_window_info_at(start_x, start_y)
                if win_app_id:
                    app_id = win_app_id
                    print(f"Detected App ID: {app_id}")
                elif win_app_class:
                    app_class = win_app_class
                    print(f"Detected App Class: {app_class}")
                else:
                    print("Could not detect app ID or class. Saving as Global.")

            gesture.name = name
            gesture.command = command
            gesture.app_id = app_id
            gesture.app_class = app_class
            storage.save_gesture(gesture)
            print(f"Gesture '{name}' saved to {GESTURE_FILE}.")
            if command:
                print(f"Command mapped: {command}")
        else:
            print("Gesture recording cancelled or invalid.")

    elif mode in ["listen", "debug"]:
        templates = storage.load_all()
        print(f"Loaded {len(templates)} gestures.")

        print("A transparent overlay will appear. Click and drag to draw. Press Esc to cancel.")
        gesture = capture_gesture_gui()
        
        if gesture:
            start_x, start_y = gesture.points[0]
            win_app_id, win_app_class = get_window_info_at(start_x, start_y)
            
            filtered_templates = []
            for t in templates:
                if t.app_id is None and t.app_class is None:
                    filtered_templates.append(t)
                elif t.app_id and win_app_id and t.app_id == win_app_id:
                    filtered_templates.append(t)
                elif t.app_class and win_app_class and t.app_class == win_app_class:
                    filtered_templates.append(t)
            
            if not filtered_templates:
                print(f"No gestures configured for app_id={win_app_id}, app_class={win_app_class} or globally.")
                sys.exit(0)

            recognizer = Recognizer(filtered_templates)
            match, score = recognizer.recognize(gesture)
            if match:
                print(f"RECOGNIZED: {match.name} (Score: {score:.2f})")
                
                if mode == "debug":
                    vis = GestureVisualizer()
                    # We normalize the drawn gesture so they can be compared directly
                    norm_drawn = gesture.normalize()
                    norm_template = match.normalize()
                    
                    vis.show_comparison(
                        recorded=norm_drawn,
                        template=norm_template,
                        template_name=match.name,
                        score=score
                    )
                else:
                    if match.command:
                        print(f"Executing: {match.command}")
                        
                        # Focus the window that was under the mouse when drawing started
                        start_x, start_y = gesture.points[0]
                        focus_window_at(start_x, start_y)
                        
                        # Brief sleep to ensure Sway has fully refocused the underlying window
                        # after the GTK overlay was destroyed.
                        time.sleep(0.05)
                        subprocess.Popen(match.command, shell=True)
            else:
                print(f"No match. (Best score: {score:.2f})")
                if mode == "debug":
                    vis = GestureVisualizer()
                    vis.show(gesture.normalize(), title="Unrecognized Gesture", score=score)
        else:
            print("Gesture cancelled or invalid.")

    elif mode == "list":
        templates = storage.load_all()
        if not templates:
            print("No gestures found.")
            sys.exit(0)
            
        print("+" + "-"*22 + "+" + "-"*32 + "+" + "-"*12 + "+" + "-"*20 + "+")
        print(f"| {'Name':<20} | {'Command':<30} | {'Points':<10} | {'App':<18} |")
        print("+" + "-"*22 + "+" + "-"*32 + "+" + "-"*12 + "+" + "-"*20 + "+")
        for g in templates:
            cmd = g.command if g.command else "None"
            name_str = (g.name[:17] + "...") if len(g.name) > 20 else g.name
            cmd_str = (cmd[:27] + "...") if len(cmd) > 30 else cmd
            
            app_str = "Global"
            if getattr(g, "app_id", None): app_str = f"id:{g.app_id}"
            elif getattr(g, "app_class", None): app_str = f"class:{g.app_class}"
            app_str = (app_str[:15] + "...") if len(app_str) > 18 else app_str
            
            print(f"| {name_str:<20} | {cmd_str:<30} | {len(g.points):<10} | {app_str:<18} |")
        print("+" + "-"*22 + "+" + "-"*32 + "+" + "-"*12 + "+" + "-"*20 + "+")

    elif mode == "list-gui":
        show_gesture_list()

    elif mode == "show":
        if len(sys.argv) < 3:
            print("Please provide the name of the gesture to show.")
            print("Usage: swaystroke show <name>")
            sys.exit(1)
        name = sys.argv[2]
        templates = storage.load_all()
        target = next((g for g in templates if g.name == name), None)
        
        if not target:
            print(f"Gesture '{name}' not found.")
            sys.exit(1)
            
        vis = GestureVisualizer()
        vis.show(target.normalize(), title=f"Gesture: {target.name}")

    else:
        print(f"Unknown mode: {mode}")

if __name__ == "__main__":
    main()