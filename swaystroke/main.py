import sys
import subprocess
import time
import click
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

@click.group()
def main():
    """Swaystroke - A gesture recognition tool for Sway/Wayland"""
    pass

@main.command(name="generate-config")
def cmd_generate_config():
    """Generate the default configuration file in the config directory"""
    generate_default_config()

@main.command(name="record")
@click.option("--global", "is_global", is_flag=True, help="Record the gesture to be available globally.")
@click.option("--app-id", help="Bind the gesture to a specific Wayland application ID.")
@click.option("--app-class", help="Bind the gesture to a specific XWayland window class.")
@click.option("--get-app-id-or-class", is_flag=True, help="Automatically get the app ID or class from the window under the gesture.")
@click.argument("name")
@click.argument("command", required=False)
def cmd_record(is_global, app_id, app_class, get_app_id_or_class, name, command):
    """Record a new gesture with the given name and map it to a shell command"""
    storage = StorageManager(GESTURE_FILE)
    templates = storage.load_all()
    if any(g.name == name for g in templates):
        resp = input(f"Gesture '{name}' already exists. Overwrite? [y/N]: ")
        if resp.lower() != 'y':
            click.echo("Aborting.")
            sys.exit(0)
    
    click.echo(f"A transparent overlay will appear. Click and drag to draw '{name}'. Press Esc to cancel.")
    gesture = capture_gesture_gui()
    
    if gesture:
        if get_app_id_or_class:
            start_x, start_y = gesture.points[0]
            win_app_id, win_app_class = get_window_info_at(start_x, start_y)
            if win_app_id:
                app_id = win_app_id
                click.echo(f"Detected App ID: {app_id}")
            elif win_app_class:
                app_class = win_app_class
                click.echo(f"Detected App Class: {app_class}")
            else:
                click.echo("Could not detect app ID or class. Saving as Global.")

        gesture.name = name
        gesture.command = command
        gesture.app_id = app_id
        gesture.app_class = app_class
        storage.save_gesture(gesture)
        click.echo(f"Gesture '{name}' saved to {GESTURE_FILE}.")
        if command:
            click.echo(f"Command mapped: {command}")
    else:
        click.echo("Gesture recording cancelled or invalid.")

@main.command(name="listen")
def cmd_listen():
    """Listen for a gesture and execute the corresponding command"""
    _listen_or_debug(mode="listen")

@main.command(name="debug")
def cmd_debug():
    """Listen for a gesture and open the visualizer to show the match and score"""
    _listen_or_debug(mode="debug")

def _listen_or_debug(mode):
    storage = StorageManager(GESTURE_FILE)
    templates = storage.load_all()
    click.echo(f"Loaded {len(templates)} gestures.")

    click.echo("A transparent overlay will appear. Click and drag to draw. Press Esc to cancel.")
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
            click.echo(f"No gestures configured for app_id={win_app_id}, app_class={win_app_class} or globally.")
            sys.exit(0)

        recognizer = Recognizer(filtered_templates)
        match, score = recognizer.recognize(gesture)
        if match:
            click.echo(f"RECOGNIZED: {match.name} (Score: {score:.2f})")
            
            if mode == "debug":
                vis = GestureVisualizer()
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
                    click.echo(f"Executing: {match.command}")
                    
                    start_x, start_y = gesture.points[0]
                    focus_window_at(start_x, start_y)
                    
                    time.sleep(0.05)
                    subprocess.Popen(match.command, shell=True)
        else:
            click.echo(f"No match. (Best score: {score:.2f})")
            if mode == "debug":
                vis = GestureVisualizer()
                vis.show(gesture.normalize(), title="Unrecognized Gesture", score=score)
    else:
        click.echo("Gesture cancelled or invalid.")

@main.command(name="list")
def cmd_list():
    """Print an ASCII table of all recorded gestures and their commands"""
    storage = StorageManager(GESTURE_FILE)
    templates = storage.load_all()
    if not templates:
        click.echo("No gestures found.")
        sys.exit(0)
        
    click.echo("+" + "-"*6 + "+" + "-"*22 + "+" + "-"*32 + "+" + "-"*12 + "+" + "-"*20 + "+")
    click.echo(f"| {'ID':<4} | {'Name':<20} | {'Command':<30} | {'Points':<10} | {'App':<18} |")
    click.echo("+" + "-"*6 + "+" + "-"*22 + "+" + "-"*32 + "+" + "-"*12 + "+" + "-"*20 + "+")
    for g in templates:
        cmd = g.command if g.command else "None"
        name_str = (g.name[:17] + "...") if len(g.name) > 20 else g.name
        cmd_str = (cmd[:27] + "...") if len(cmd) > 30 else cmd
        
        app_str = "Global"
        if getattr(g, "app_id", None): app_str = f"id:{g.app_id}"
        elif getattr(g, "app_class", None): app_str = f"class:{g.app_class}"
        app_str = (app_str[:15] + "...") if len(app_str) > 18 else app_str
        
        g_id = str(g.id) if getattr(g, "id", None) is not None else "?"
        
        click.echo(f"| {g_id:<4} | {name_str:<20} | {cmd_str:<30} | {len(g.points):<10} | {app_str:<18} |")
    click.echo("+" + "-"*6 + "+" + "-"*22 + "+" + "-"*32 + "+" + "-"*12 + "+" + "-"*20 + "+")

@main.command(name="list-gui")
def cmd_list_gui():
    """Show a scrollable, graphical window of all recorded gestures"""
    show_gesture_list()

@main.command(name="show")
@click.argument("identifier")
def cmd_show(identifier):
    """Open the visualizer to display the recorded path for a specific gesture"""
    storage = StorageManager(GESTURE_FILE)
    templates = storage.load_all()
    if identifier.isdigit():
        target = next((g for g in templates if getattr(g, "id", None) == int(identifier)), None)
    else:
        target = next((g for g in templates if g.name == identifier), None)
    
    if not target:
        click.echo(f"Gesture '{identifier}' not found.")
        sys.exit(1)
        
    vis = GestureVisualizer()
    vis.show(target.normalize(), title=f"Gesture: {target.name}")

@main.command(name="delete")
@click.argument("identifier")
def cmd_delete(identifier):
    """Delete a recorded gesture by its ID or name"""
    storage = StorageManager(GESTURE_FILE)
    if storage.delete_gesture(identifier):
        click.echo(f"Gesture '{identifier}' deleted successfully.")
    else:
        click.echo(f"Gesture '{identifier}' not found.")

if __name__ == "__main__":
    main()