import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GtkLayerShell', '0.1')
from gi.repository import Gtk, Gdk, GtkLayerShell, GLib
import cairo
from .gesture import Gesture
from .config import CONFIG

def hex_to_rgba(hex_color, opacity=1.0):
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 6:
        r = int(hex_color[0:2], 16) / 255.0
        g = int(hex_color[2:4], 16) / 255.0
        b = int(hex_color[4:6], 16) / 255.0
        return r, g, b, opacity
    return 0.0, 0.0, 0.0, opacity

class GestureGUI(Gtk.Window):
    def __init__(self, on_finished=None):
        super().__init__()
        self.on_finished = on_finished
        self.is_drawing = False
        self.gesture = None
        self.strokes = []
        self.current_stroke = []
        self.timeout_id = None

        # Configure Layer Shell to cover the whole screen
        GtkLayerShell.init_for_window(self)
        # OVERLAY layer ensures it's above other windows
        GtkLayerShell.set_layer(self, GtkLayerShell.Layer.OVERLAY)
        # Exclusive zone is not needed, we just want to cover the screen
        GtkLayerShell.set_namespace(self, "swaystroke")
        
        # Anchor to all edges
        for edge in [GtkLayerShell.Edge.TOP, GtkLayerShell.Edge.BOTTOM, GtkLayerShell.Edge.LEFT, GtkLayerShell.Edge.RIGHT]:
            GtkLayerShell.set_anchor(self, edge, True)
            
        # Enable Transparency
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual and screen.is_composited():
            self.set_visual(visual)
        self.set_app_paintable(True)
        
        # We need to receive pointer events
        self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK | 
                        Gdk.EventMask.BUTTON_RELEASE_MASK | 
                        Gdk.EventMask.POINTER_MOTION_MASK |
                        Gdk.EventMask.KEY_PRESS_MASK)
                        
        self.connect("draw", self.on_draw)
        self.connect("button-press-event", self.on_button_press)
        self.connect("button-release-event", self.on_button_release)
        self.connect("motion-notify-event", self.on_motion_notify)
        self.connect("key-press-event", self.on_key_press)
        
        # Ensure we have keyboard focus to catch Escape
        GtkLayerShell.set_keyboard_mode(self, GtkLayerShell.KeyboardMode.ON_DEMAND)

    def on_key_press(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            self.hide()
            if self.on_finished:
                self.on_finished(None)
            return True
        return False

    def on_button_press(self, widget, event):
        if self.timeout_id:
            GLib.source_remove(self.timeout_id)
            self.timeout_id = None
            
        self.is_drawing = True
        self.current_stroke = [(event.x, event.y)]
        self.strokes.append(self.current_stroke)
        
        if not self.gesture:
            self.gesture = Gesture()
            
        self.gesture.add_point(event.x, event.y)
        self.queue_draw()
        return True

    def on_motion_notify(self, widget, event):
        if self.is_drawing:
            self.current_stroke.append((event.x, event.y))
            self.gesture.add_point(event.x, event.y)
            self.queue_draw()
        return True

    def on_button_release(self, widget, event):
        if self.is_drawing:
            self.is_drawing = False
            self.current_stroke.append((event.x, event.y))
            self.gesture.add_point(event.x, event.y)
            self.queue_draw()
            
            timeout_ms = CONFIG.get("multistroke_timeout", 500)
            self.timeout_id = GLib.timeout_add(timeout_ms, self.finish_gesture)
        return True

    def finish_gesture(self):
        self.timeout_id = None
        self.hide()
        if self.on_finished:
            self.on_finished(self.gesture)
        return False

    def on_draw(self, widget, cr):
        width = self.get_allocated_width()
        
        # Clear background using config overlay settings
        bg_r, bg_g, bg_b, bg_a = hex_to_rgba(CONFIG["overlay"]["color"], CONFIG["overlay"]["opacity"])
        cr.set_source_rgba(bg_r, bg_g, bg_b, bg_a)
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.paint()
        cr.set_operator(cairo.OPERATOR_OVER)
        
        # Draw overlay text if present
        overlay_text = CONFIG["overlay"].get("text", "")
        if overlay_text:
            cr.set_source_rgba(1.0, 1.0, 1.0, 0.8)  # White text
            cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            cr.set_font_size(24)
            extents = cr.text_extents(overlay_text)
            x = (width - extents.width) / 2
            y = 50
            cr.move_to(x, y)
            cr.show_text(overlay_text)
        
        # Draw the gesture trail using config settings
        trail_r, trail_g, trail_b, trail_a = hex_to_rgba(CONFIG["trail"]["color"], CONFIG["trail"]["opacity"])
        cr.set_source_rgba(trail_r, trail_g, trail_b, trail_a)
        cr.set_line_width(CONFIG["trail"]["width"])
        cr.set_line_cap(cairo.LINE_CAP_ROUND)
        cr.set_line_join(cairo.LINE_JOIN_ROUND)

        for stroke in self.strokes:
            if len(stroke) < 2:
                continue
            cr.move_to(stroke[0][0], stroke[0][1])
            for x, y in stroke[1:]:
                cr.line_to(x, y)
            cr.stroke()
        return False

def capture_gesture_gui():
    gesture_result = []
    def on_finished(g):
        gesture_result.append(g)
        Gtk.main_quit()
        
    win = GestureGUI(on_finished=on_finished)
    win.show_all()
    Gtk.main()
    
    gesture = gesture_result[0] if gesture_result else None
    
    # Crucial: Destroy the window and flush events so Wayland refocuses the underlying window
    win.destroy()
    while Gtk.events_pending():
        Gtk.main_iteration()
        
    if gesture and len(gesture.points) > 5:
        return gesture
    return None
