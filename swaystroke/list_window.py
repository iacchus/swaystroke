import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk
import cairo
from .storage import StorageManager
from .config import GESTURE_FILE
import math

def fit_points(pts, w, h, pad):
    if not pts:
        return []
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    span_x = max_x - min_x or 1e-6
    span_y = max_y - min_y or 1e-6
    scale = min((w - 2 * pad) / span_x, (h - 2 * pad) / span_y)
    off_x = pad + ((w - 2 * pad) - span_x * scale) / 2
    off_y = pad + ((h - 2 * pad) - span_y * scale) / 2
    return [((p[0] - min_x) * scale + off_x,
             (p[1] - min_y) * scale + off_y) for p in pts]

class GestureDrawingArea(Gtk.DrawingArea):
    def __init__(self, points):
        super().__init__()
        self.points = points
        self.set_size_request(80, 80)
        self.connect("draw", self.on_draw)

    def on_draw(self, widget, cr):
        width = self.get_allocated_width()
        height = self.get_allocated_height()

        # Draw background (rounded rectangle could be nice, but simple rect is fine)
        cr.set_source_rgb(0.15, 0.15, 0.15) # dark theme background
        cr.rectangle(0, 0, width, height)
        cr.fill()

        if not self.points:
            return False

        fitted = fit_points(self.points, width, height, 10)

        # Draw line
        cr.set_source_rgb(0.53, 0.7, 0.98) # soft blue
        cr.set_line_width(3)
        cr.set_line_cap(cairo.LINE_CAP_ROUND)
        cr.set_line_join(cairo.LINE_JOIN_ROUND)

        cr.move_to(fitted[0][0], fitted[0][1])
        for x, y in fitted[1:]:
            cr.line_to(x, y)
        cr.stroke()

        # Draw start point (greenish)
        cr.set_source_rgb(0.65, 0.89, 0.63)
        cr.arc(fitted[0][0], fitted[0][1], 4, 0, 2 * math.pi)
        cr.fill()

        # Draw end point (reddish/orange)
        cr.set_source_rgb(0.98, 0.7, 0.52)
        cr.arc(fitted[-1][0], fitted[-1][1], 4, 0, 2 * math.pi)
        cr.fill()

        return False

class GestureListWindow(Gtk.Window):
    def __init__(self, gestures):
        super().__init__(title="Swaystroke Gestures")
        self.set_default_size(450, 600)
        self.set_border_width(10)
        
        # Setup dark theme preference
        settings = Gtk.Settings.get_default()
        if settings:
            settings.set_property("gtk-application-prefer-dark-theme", True)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.add(vbox)

        header = Gtk.Label()
        header.set_markup("<big><b>Recorded Gestures</b></big>")
        header.set_halign(Gtk.Align.START)
        vbox.pack_start(header, False, False, 5)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        vbox.pack_start(scrolled, True, True, 0)

        listbox = Gtk.ListBox()
        listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        scrolled.add(listbox)

        if not gestures:
            empty_label = Gtk.Label(label="No gestures recorded yet.")
            empty_label.set_margin_top(20)
            listbox.add(empty_label)

        for g in gestures:
            row = Gtk.ListBoxRow()
            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=15)
            row.add(hbox)

            # Drawing area for the gesture form
            da = GestureDrawingArea(g.points)
            da.set_margin_top(10)
            da.set_margin_bottom(10)
            da.set_margin_start(10)
            hbox.pack_start(da, False, False, 0)

            # Text VBox
            text_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            text_vbox.set_valign(Gtk.Align.CENTER)
            hbox.pack_start(text_vbox, True, True, 0)

            name_label = Gtk.Label()
            name_label.set_markup(f"<b><big>{g.name}</big></b>")
            name_label.set_halign(Gtk.Align.START)
            text_vbox.pack_start(name_label, False, False, 0)

            cmd = g.command if g.command else "<i>No command</i>"
            cmd_label = Gtk.Label()
            cmd_label.set_markup(f"<span foreground='gray'>Command:</span> {cmd}")
            cmd_label.set_halign(Gtk.Align.START)
            text_vbox.pack_start(cmd_label, False, False, 0)
            
            pts_label = Gtk.Label()
            pts_label.set_markup(f"<span foreground='gray' size='small'>Points: {len(g.points)}</span>")
            pts_label.set_halign(Gtk.Align.START)
            text_vbox.pack_start(pts_label, False, False, 0)

            listbox.add(row)

        self.connect("destroy", Gtk.main_quit)

def show_gesture_list():
    storage = StorageManager(GESTURE_FILE)
    gestures = storage.load_all()
    
    win = GestureListWindow(gestures)
    win.show_all()
    Gtk.main()
