import sys
import subprocess
import time
from .config import GESTURE_FILE
from .storage import StorageManager
from .recognizer import Recognizer
from .gesture import Gesture
from .gui import capture_gesture_gui
from .focus import focus_window_at
from .visualizer import GestureVisualizer

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  swaystroke list")
        print("  swaystroke record <name> [command]")
        print("  swaystroke listen")
        print("  swaystroke debug")
        print("  swaystroke show <name>")
        sys.exit(1)

    mode = sys.argv[1]
    storage = StorageManager(GESTURE_FILE)

    if mode == "record":
        if len(sys.argv) < 3:
            print("Please provide a name for the gesture.")
            print("Usage: swaystroke record <name> [command]")
            sys.exit(1)
        name = sys.argv[2]
        command = sys.argv[3] if len(sys.argv) > 3 else None
        
        templates = storage.load_all()
        if any(g.name == name for g in templates):
            resp = input(f"Gesture '{name}' already exists. Overwrite? [y/N]: ")
            if resp.lower() != 'y':
                print("Aborting.")
                sys.exit(0)
        
        print(f"A transparent overlay will appear. Click and drag to draw '{name}'. Press Esc to cancel.")
        gesture = capture_gesture_gui()
        
        if gesture:
            gesture.name = name
            gesture.command = command
            storage.save_gesture(gesture)
            print(f"Gesture '{name}' saved to {GESTURE_FILE}.")
            if command:
                print(f"Command mapped: {command}")
        else:
            print("Gesture recording cancelled or invalid.")

    elif mode in ["listen", "debug"]:
        templates = storage.load_all()
        recognizer = Recognizer(templates)
        print(f"Loaded {len(templates)} gestures.")

        print("A transparent overlay will appear. Click and drag to draw. Press Esc to cancel.")
        gesture = capture_gesture_gui()
        
        if gesture:
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
            
        print("+" + "-"*22 + "+" + "-"*32 + "+" + "-"*12 + "+")
        print(f"| {'Name':<20} | {'Command':<30} | {'Points':<10} |")
        print("+" + "-"*22 + "+" + "-"*32 + "+" + "-"*12 + "+")
        for g in templates:
            cmd = g.command if g.command else "None"
            name_str = (g.name[:17] + "...") if len(g.name) > 20 else g.name
            cmd_str = (cmd[:27] + "...") if len(cmd) > 30 else cmd
            print(f"| {name_str:<20} | {cmd_str:<30} | {len(g.points):<10} |")
        print("+" + "-"*22 + "+" + "-"*32 + "+" + "-"*12 + "+")

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