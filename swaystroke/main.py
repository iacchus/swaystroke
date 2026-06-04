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
import socket
import os

@click.group()
def main():
    """Swaystroke - A gesture recognition tool for Sway/Wayland"""
    pass

@main.command(name="generate-config")
def cmd_generate_config():
    """Generate the default configuration file in the config directory"""
    generate_default_config()

def execute_gesture_action(match, gesture):
    if not match or not match.command:
        return
        
    start_x, start_y = gesture.points[0]
    focus_window_at(start_x, start_y)
    time.sleep(0.05)
    
    action_type = getattr(match, "action_type", "command")
    if action_type == "command":
        subprocess.Popen(match.command, shell=True)
    elif action_type == "text":
        subprocess.Popen(["wtype", match.command])
    elif action_type == "key":
        keys = match.command.split('+')
        args = ["wtype"]
        for k in keys[:-1]:
            args.extend(["-M", k])
        args.extend(["-k", keys[-1]])
        for k in reversed(keys[:-1]):
            args.extend(["-m", k])
        subprocess.Popen(args)

@main.command(name="record")
@click.option("--type", "action_type", type=click.Choice(["command", "key", "text"]), default="command", help="The type of action to record (command, key, or text).")
@click.option("--global", "is_global", is_flag=True, help="Record the gesture to be available globally.")
@click.option("--app-id", help="Bind the gesture to a specific Wayland application ID.")
@click.option("--app-class", help="Bind the gesture to a specific XWayland window class.")
@click.option("--get-app-id-or-class", is_flag=True, help="Automatically get the app ID or class from the window under the gesture.")
@click.option("--multistroke-timeout", type=int, default=None, help="Timeout in milliseconds for multi-stroke gestures.")
@click.argument("name")
@click.argument("command", required=False)
def cmd_record(action_type, is_global, app_id, app_class, get_app_id_or_class, multistroke_timeout, name, command):
    """Record a new gesture with the given name and map it to a shell command"""
    storage = StorageManager(GESTURE_FILE)
    templates = storage.load_all()
    if any(g.name == name for g in templates):
        resp = input(f"Gesture '{name}' already exists. Overwrite? [y/N]: ")
        if resp.lower() != 'y':
            click.echo("Aborting.")
            sys.exit(0)
    
    click.echo(f"A transparent overlay will appear. Click and drag to draw '{name}'. Press Esc to cancel.")
    gesture = capture_gesture_gui(multi_stroke=True, timeout=multistroke_timeout)
    
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
        gesture.action_type = action_type
        storage.save_gesture(gesture)
        click.echo(f"Gesture '{name}' saved to {GESTURE_FILE}.")
        if command:
            click.echo(f"Command mapped: {command}")
    else:
        click.echo("Gesture recording cancelled or invalid.")

@main.command(name="listen")
@click.option("--multi-stroke", is_flag=True, help="Wait for multiple strokes before executing.")
@click.option("--multistroke-timeout", type=int, default=None, help="Timeout in milliseconds for multi-stroke gestures.")
def cmd_listen(multi_stroke, multistroke_timeout):
    """Listen for a gesture and execute the corresponding command"""
    _listen_or_debug(mode="listen", multi_stroke=multi_stroke, timeout=multistroke_timeout)

@main.command(name="debug")
@click.option("--multi-stroke", is_flag=True, help="Wait for multiple strokes before executing.")
@click.option("--multistroke-timeout", type=int, default=None, help="Timeout in milliseconds for multi-stroke gestures.")
def cmd_debug(multi_stroke, multistroke_timeout):
    """Listen for a gesture and open the visualizer to show the match and score"""
    _listen_or_debug(mode="debug", multi_stroke=multi_stroke, timeout=multistroke_timeout)

def _listen_or_debug(mode, multi_stroke=False, timeout=None):
    storage = StorageManager(GESTURE_FILE)
    templates = storage.load_all()
    click.echo(f"Loaded {len(templates)} gestures.")

    click.echo("A transparent overlay will appear. Click and drag to draw. Press Esc to cancel.")
    gesture = capture_gesture_gui(multi_stroke=multi_stroke, timeout=timeout)
    
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
                    click.echo(f"Executing: {match.command} (Type: {getattr(match, 'action_type', 'command')})")
                    execute_gesture_action(match, gesture)
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

@main.command(name="daemon")
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose logging for debugging.")
def cmd_daemon(verbose):
    """Run Swaystroke in the background for zero-latency triggers"""
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk, GLib
    from .overlay import GestureGUI
    
    sock_path = "/tmp/swaystroke.sock"
    if os.path.exists(sock_path):
        os.remove(sock_path)
        
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(sock_path)
    server.listen(1)
    server.setblocking(False)
    
    def on_gesture_finished(gesture):
        if not gesture or len(gesture.points) < 5:
            if verbose:
                click.echo(f"Daemon: Gesture finished but was too short or None. Points: {len(gesture.points) if gesture else 0}")
            return
            
        if verbose:
            click.echo(f"Daemon: Gesture finished with {len(gesture.points)} points.")
            
        storage = StorageManager(GESTURE_FILE)
        templates = storage.load_all()
        
        start_x, start_y = gesture.points[0]
        win_app_id, win_app_class = get_window_info_at(start_x, start_y)
        
        if verbose:
            click.echo(f"Daemon: Detected window - App ID: {win_app_id}, App Class: {win_app_class}")
        
        filtered = []
        for t in templates:
            if t.app_id is None and t.app_class is None:
                filtered.append(t)
            elif t.app_id and win_app_id and t.app_id == win_app_id:
                filtered.append(t)
            elif t.app_class and win_app_class and t.app_class == win_app_class:
                filtered.append(t)
                
        if not filtered:
            if verbose:
                click.echo("Daemon: No gestures configured for this window or globally.")
            return
            
        recognizer = Recognizer(filtered)
        match, score = recognizer.recognize(gesture)
        if match:
            if verbose:
                click.echo(f"Daemon: Recognized gesture '{match.name}' with score {score:.2f}")
            if match.command:
                if verbose:
                    click.echo(f"Daemon: Executing command '{match.command}'")
                execute_gesture_action(match, gesture)
            else:
                if verbose:
                    click.echo("Daemon: Recognized gesture has no command assigned.")
        else:
            if verbose:
                click.echo(f"Daemon: No match found. Best score was {score:.2f}")
            
    win = GestureGUI(on_finished=on_gesture_finished)
    
    def on_connection(source, condition):
        try:
            conn, addr = server.accept()
            data = conn.recv(1024).decode()
            
            if verbose:
                click.echo(f"Daemon: Received command '{data}'")
                
            parts = data.split(":")
            command_type = parts[0]
            timeout = None
            if len(parts) > 1 and parts[1].isdigit():
                timeout = int(parts[1])

            if command_type in ["trigger", "trigger_start", "trigger_multi", "trigger_start_multi"]:
                win.multi_stroke = "multi" in command_type
                win.timeout = timeout
                # Show window and clear state
                win.strokes = []
                win.current_stroke = []
                win.gesture = None
                win.is_drawing = False
                if win.timeout_id:
                    GLib.source_remove(win.timeout_id)
                    win.timeout_id = None
                win.queue_draw()
                win.show_all()
                
                if "start" in command_type:
                    win.start_gesture_external()
                    
            elif command_type in ["trigger_stop", "trigger_stop_multi"]:
                win.multi_stroke = "multi" in command_type
                win.timeout = timeout
                win.stop_gesture_external()
                
            conn.close()
        except Exception as e:
            if verbose:
                click.echo(f"Daemon: Connection error - {e}")
        return True
        
    GLib.io_add_watch(server.fileno(), GLib.IO_IN, on_connection)
    click.echo("Swaystroke daemon running...")
    Gtk.main()

@main.command(name="trigger")
@click.option("--start", is_flag=True, help="Trigger and immediately start recording a gesture.")
@click.option("--stop", is_flag=True, help="Stop a currently recording gesture that was triggered with --start.")
@click.option("--multi-stroke", is_flag=True, help="Wait for multiple strokes before executing.")
@click.option("--multistroke-timeout", type=int, default=None, help="Timeout in milliseconds for multi-stroke gestures.")
def cmd_trigger(start, stop, multi_stroke, multistroke_timeout):
    """Trigger the daemon overlay instantly"""
    sock_path = "/tmp/swaystroke.sock"
    try:
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.connect(sock_path)
        
        if start:
            cmd = b"trigger_start_multi" if multi_stroke else b"trigger_start"
        elif stop:
            cmd = b"trigger_stop_multi" if multi_stroke else b"trigger_stop"
        else:
            cmd = b"trigger_multi" if multi_stroke else b"trigger"
            
        if multistroke_timeout is not None:
            cmd += f":{multistroke_timeout}".encode()
            
        client.sendall(cmd)
            
        client.close()
    except Exception as e:
        click.echo(f"Could not connect to daemon: {e}. Is it running?")

if __name__ == "__main__":
    main()