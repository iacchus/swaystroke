import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk
import cairo
import math
import datetime

from .storage import StorageManager, load_history
from .config import GESTURE_FILE, HISTORY_FILE, CONFIG, save_config

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

        cr.set_source_rgb(0.15, 0.15, 0.15)
        cr.rectangle(0, 0, width, height)
        cr.fill()

        if not self.points:
            return False

        fitted = fit_points(self.points, width, height, 10)

        cr.set_source_rgb(0.53, 0.7, 0.98)
        cr.set_line_width(3)
        cr.set_line_cap(cairo.LINE_CAP_ROUND)
        cr.set_line_join(cairo.LINE_JOIN_ROUND)

        cr.move_to(fitted[0][0], fitted[0][1])
        for x, y in fitted[1:]:
            cr.line_to(x, y)
        cr.stroke()

        cr.set_source_rgb(0.65, 0.89, 0.63)
        cr.arc(fitted[0][0], fitted[0][1], 4, 0, 2 * math.pi)
        cr.fill()

        cr.set_source_rgb(0.98, 0.7, 0.52)
        cr.arc(fitted[-1][0], fitted[-1][1], 4, 0, 2 * math.pi)
        cr.fill()

        return False

class GesturesTab(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.set_border_width(10)
        
        storage = StorageManager(GESTURE_FILE)
        self.gestures = storage.load_all()

        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.pack_start(header_box, False, False, 5)

        header = Gtk.Label()
        header.set_markup("<big><b>Recorded Gestures</b></big>")
        header.set_halign(Gtk.Align.START)
        header_box.pack_start(header, True, True, 0)

        self.filter_options = ["All", "Global"]
        for g in self.gestures:
            if getattr(g, "app_id", None):
                opt = f"id:{g.app_id}"
                if opt not in self.filter_options: self.filter_options.append(opt)
            elif getattr(g, "app_class", None):
                opt = f"class:{g.app_class}"
                if opt not in self.filter_options: self.filter_options.append(opt)

        self.combo = Gtk.ComboBoxText()
        for opt in self.filter_options:
            self.combo.append_text(opt)
        self.combo.set_active(0)
        self.combo.connect("changed", self.on_filter_changed)
        header_box.pack_start(self.combo, False, False, 0)

        record_new_btn = Gtk.Button(label="Record New")
        record_new_btn.connect("clicked", self.on_record_new_clicked)
        header_box.pack_end(record_new_btn, False, False, 0)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.pack_start(scrolled, True, True, 0)

        self.listbox = Gtk.ListBox()
        self.listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        scrolled.add(self.listbox)

        self.populate_list()

    def on_filter_changed(self, combo):
        self.populate_list()

    def populate_list(self):
        for child in self.listbox.get_children():
            self.listbox.remove(child)

        selected_filter = self.combo.get_active_text()
        
        filtered = []
        for g in self.gestures:
            app_str = "Global"
            if getattr(g, "app_id", None): app_str = f"id:{g.app_id}"
            elif getattr(g, "app_class", None): app_str = f"class:{g.app_class}"
            
            if selected_filter == "All":
                filtered.append(g)
            elif selected_filter == "Global" and app_str == "Global":
                filtered.append(g)
            elif selected_filter == app_str:
                filtered.append(g)

        if not filtered:
            empty_label = Gtk.Label(label="No gestures match this filter.")
            empty_label.set_margin_top(20)
            self.listbox.add(empty_label)

        for g in filtered:
            row = Gtk.ListBoxRow()
            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=15)
            row.add(hbox)

            da = GestureDrawingArea(g.points)
            da.set_margin_top(10)
            da.set_margin_bottom(10)
            da.set_margin_start(10)
            hbox.pack_start(da, False, False, 0)

            text_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            text_vbox.set_valign(Gtk.Align.CENTER)
            hbox.pack_start(text_vbox, True, True, 0)

            name_label = Gtk.Label()
            g_id = f"#{g.id} " if getattr(g, 'id', None) is not None else ""
            name_label.set_markup(f"<b><big>{g_id}{g.name}</big></b>")
            name_label.set_halign(Gtk.Align.START)
            text_vbox.pack_start(name_label, False, False, 0)

            cmd = g.command if g.command else "<i>No command</i>"
            cmd_label = Gtk.Label()
            cmd_label.set_markup(f"<span foreground='gray'>Command:</span> {cmd}")
            cmd_label.set_halign(Gtk.Align.START)
            text_vbox.pack_start(cmd_label, False, False, 0)
            
            app_str = "Global"
            if getattr(g, "app_id", None): app_str = f"id:{g.app_id}"
            elif getattr(g, "app_class", None): app_str = f"class:{g.app_class}"
            
            info_label = Gtk.Label()
            info_label.set_markup(f"<span foreground='gray' size='small'>App: {app_str} | Points: {len(g.points)}</span>")
            info_label.set_halign(Gtk.Align.START)
            text_vbox.pack_start(info_label, False, False, 0)

            btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
            btn_box.set_valign(Gtk.Align.CENTER)
            hbox.pack_end(btn_box, False, False, 0)
            
            show_btn = Gtk.Button(label="Show")
            show_btn.connect("clicked", self.on_show_clicked, g)
            btn_box.pack_start(show_btn, False, False, 0)
            
            edit_cmd_btn = Gtk.Button(label="Edit")
            edit_cmd_btn.connect("clicked", self.on_edit_cmd_clicked, g)
            btn_box.pack_start(edit_cmd_btn, False, False, 0)
            
            rerecord_btn = Gtk.Button(label="Re-record")
            rerecord_btn.connect("clicked", self.on_rerecord_clicked, g)
            btn_box.pack_start(rerecord_btn, False, False, 0)
            
            delete_btn = Gtk.Button(label="Delete")
            delete_btn.get_style_context().add_class("destructive-action")
            delete_btn.connect("clicked", self.on_delete_clicked, g)
            btn_box.pack_start(delete_btn, False, False, 0)

            self.listbox.add(row)

        self.listbox.show_all()

    def on_delete_clicked(self, button, g):
        dialog = Gtk.MessageDialog(
            transient_for=self.get_toplevel(),
            flags=0,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.YES_NO,
            text=f"Delete gesture '{g.name}'?",
        )
        dialog.format_secondary_text("This action cannot be undone.")
        response = dialog.run()
        dialog.destroy()
        
        if response == Gtk.ResponseType.YES:
            storage = StorageManager(GESTURE_FILE)
            if getattr(g, "id", None) is not None:
                storage.delete_gesture(str(g.id))
            else:
                storage.delete_gesture(g.name)
            self.gestures = storage.load_all()
            self.populate_list()

    def on_rerecord_clicked(self, button, g):
        dialog = Gtk.Dialog(title=f"Re-record {g.name}", parent=self.get_toplevel(), flags=0)
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, "Record", Gtk.ResponseType.OK)
        
        box = dialog.get_content_area()
        box.set_spacing(10)
        box.set_margin_top(10)
        box.set_margin_bottom(10)
        box.set_margin_start(10)
        box.set_margin_end(10)
        
        bind_app_check = Gtk.CheckButton(label="Update app from window under new gesture")
        box.pack_start(bind_app_check, True, True, 0)
        
        dialog.show_all()
        response = dialog.run()
        bind_app = bind_app_check.get_active()
        dialog.destroy()
        
        if response != Gtk.ResponseType.OK:
            return
            
        self.get_toplevel().hide()
        while Gtk.events_pending():
            Gtk.main_iteration()
            
        from .overlay import capture_gesture_gui
        new_g = capture_gesture_gui(multi_stroke=True)
        
        if new_g:
            g.points = new_g.points
            if bind_app:
                from .focus import get_window_info_at
                start_x, start_y = new_g.points[0]
                win_app_id, win_app_class = get_window_info_at(start_x, start_y)
                g.app_id = win_app_id if win_app_id else None
                g.app_class = win_app_class if win_app_class else None
                
            storage = StorageManager(GESTURE_FILE)
            storage.save_gesture(g)
            self.gestures = storage.load_all()
            
        self.get_toplevel().show_all()
        self.populate_list()

    def on_show_clicked(self, button, g):
        import subprocess
        g_id = str(g.id) if getattr(g, "id", None) is not None else g.name
        subprocess.Popen(["swaystroke", "show", g_id])

    def on_edit_cmd_clicked(self, button, g):
        dialog = Gtk.Dialog(title=f"Edit Gesture: {g.name}", parent=self.get_toplevel(), flags=0)
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK)
        
        box = dialog.get_content_area()
        box.set_spacing(10)
        box.set_margin_top(10)
        box.set_margin_bottom(10)
        box.set_margin_start(10)
        box.set_margin_end(10)
        
        name_entry = Gtk.Entry()
        name_entry.set_text(g.name)
        box.pack_start(name_entry, True, True, 0)
        
        cmd_entry = Gtk.Entry()
        if g.command:
            cmd_entry.set_text(g.command)
        box.pack_start(cmd_entry, True, True, 0)
        
        type_combo = Gtk.ComboBoxText()
        type_combo.append_text("command")
        type_combo.append_text("key")
        type_combo.append_text("text")
        
        current_type = getattr(g, "action_type", "command")
        for i, val in enumerate(["command", "key", "text"]):
            if val == current_type:
                type_combo.set_active(i)
                break
        box.pack_start(type_combo, True, True, 0)
        
        app_id_entry = Gtk.Entry()
        app_id_entry.set_placeholder_text("App ID (optional, e.g., firefox)")
        if getattr(g, "app_id", None):
            app_id_entry.set_text(g.app_id)
        box.pack_start(app_id_entry, True, True, 0)
        
        app_class_entry = Gtk.Entry()
        app_class_entry.set_placeholder_text("App Class (optional, for XWayland)")
        if getattr(g, "app_class", None):
            app_class_entry.set_text(g.app_class)
        box.pack_start(app_class_entry, True, True, 0)
        
        dialog.show_all()
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            g.name = name_entry.get_text().strip()
            g.command = cmd_entry.get_text().strip()
            g.action_type = type_combo.get_active_text()
            
            app_id_val = app_id_entry.get_text().strip()
            app_class_val = app_class_entry.get_text().strip()
            g.app_id = app_id_val if app_id_val else None
            g.app_class = app_class_val if app_class_val else None
            
            storage = StorageManager(GESTURE_FILE)
            storage.save_gesture(g)
            self.gestures = storage.load_all()
            self.populate_list()
            
        dialog.destroy()

    def on_record_new_clicked(self, button):
        dialog = Gtk.Dialog(title="Record New Gesture", parent=self.get_toplevel(), flags=0)
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK)
        
        box = dialog.get_content_area()
        box.set_spacing(10)
        box.set_margin_top(10)
        box.set_margin_bottom(10)
        box.set_margin_start(10)
        box.set_margin_end(10)
        
        name_entry = Gtk.Entry()
        name_entry.set_placeholder_text("Gesture Name")
        box.pack_start(name_entry, True, True, 0)
        
        cmd_entry = Gtk.Entry()
        cmd_entry.set_placeholder_text("Command / Keys / Text")
        box.pack_start(cmd_entry, True, True, 0)
        
        type_combo = Gtk.ComboBoxText()
        type_combo.append_text("command")
        type_combo.append_text("key")
        type_combo.append_text("text")
        type_combo.set_active(0)
        box.pack_start(type_combo, True, True, 0)
        
        bind_app_check = Gtk.CheckButton(label="Auto-detect app from window under gesture")
        box.pack_start(bind_app_check, True, True, 0)
        
        app_id_entry = Gtk.Entry()
        app_id_entry.set_placeholder_text("App ID (optional, e.g., firefox)")
        box.pack_start(app_id_entry, True, True, 0)
        
        app_class_entry = Gtk.Entry()
        app_class_entry.set_placeholder_text("App Class (optional, for XWayland)")
        box.pack_start(app_class_entry, True, True, 0)
        
        dialog.show_all()
        response = dialog.run()
        
        name = name_entry.get_text().strip()
        cmd = cmd_entry.get_text().strip()
        action_type = type_combo.get_active_text()
        bind_app = bind_app_check.get_active()
        app_id_val = app_id_entry.get_text().strip()
        app_class_val = app_class_entry.get_text().strip()
        
        dialog.destroy()
        
        if response == Gtk.ResponseType.OK and name:
            self.get_toplevel().hide()
            while Gtk.events_pending():
                Gtk.main_iteration()
                
            from .overlay import capture_gesture_gui
            new_g = capture_gesture_gui(multi_stroke=True)
            if new_g:
                new_g.name = name
                new_g.command = cmd
                new_g.action_type = action_type
                
                if bind_app:
                    from .focus import get_window_info_at
                    start_x, start_y = new_g.points[0]
                    win_app_id, win_app_class = get_window_info_at(start_x, start_y)
                    if win_app_id:
                        new_g.app_id = win_app_id
                    elif win_app_class:
                        new_g.app_class = win_app_class
                else:
                    if app_id_val:
                        new_g.app_id = app_id_val
                    if app_class_val:
                        new_g.app_class = app_class_val

                storage = StorageManager(GESTURE_FILE)
                storage.save_gesture(new_g)
                self.gestures = storage.load_all()
                
            self.get_toplevel().show_all()
            self.populate_list()


class HistoryTab(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.set_border_width(10)
        
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.pack_start(header_box, False, False, 5)

        header = Gtk.Label()
        header.set_markup("<big><b>Gesture History</b></big>")
        header.set_halign(Gtk.Align.START)
        header_box.pack_start(header, True, True, 0)
        
        refresh_btn = Gtk.Button(label="Refresh")
        refresh_btn.connect("clicked", self.on_refresh_clicked)
        header_box.pack_end(refresh_btn, False, False, 0)
        
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.pack_start(scrolled, True, True, 0)

        self.listbox = Gtk.ListBox()
        self.listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        scrolled.add(self.listbox)

        self.populate_list()

    def on_refresh_clicked(self, button):
        self.populate_list()

    def populate_list(self):
        for child in self.listbox.get_children():
            self.listbox.remove(child)

        history = load_history(HISTORY_FILE)
        
        if not history:
            empty_label = Gtk.Label(label="History is empty.")
            empty_label.set_margin_top(20)
            self.listbox.add(empty_label)
            self.listbox.show_all()
            return

        for h in history:
            row = Gtk.ListBoxRow()
            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=15)
            row.add(hbox)

            # Extract points
            pts = h.get("points", [])
            da = GestureDrawingArea(pts)
            da.set_margin_top(10)
            da.set_margin_bottom(10)
            da.set_margin_start(10)
            hbox.pack_start(da, False, False, 0)

            text_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            text_vbox.set_valign(Gtk.Align.CENTER)
            hbox.pack_start(text_vbox, True, True, 0)

            name_label = Gtk.Label()
            matched_name = h.get("matched_name", "Unrecognized")
            score = h.get("score", 0.0)
            name_label.set_markup(f"<b><big>{matched_name}</big></b> <span foreground='gray' size='small'>(Score: {score:.2f})</span>")
            name_label.set_halign(Gtk.Align.START)
            text_vbox.pack_start(name_label, False, False, 0)

            cmd = h.get("command", "")
            cmd_label = Gtk.Label()
            if cmd:
                cmd_label.set_markup(f"<span foreground='gray'>Executed:</span> {cmd}")
            else:
                cmd_label.set_markup(f"<i>No command executed</i>")
            cmd_label.set_halign(Gtk.Align.START)
            text_vbox.pack_start(cmd_label, False, False, 0)
            
            timestamp = h.get("timestamp", "")
            info_label = Gtk.Label()
            info_label.set_markup(f"<span foreground='gray' size='small'>{timestamp}</span>")
            info_label.set_halign(Gtk.Align.START)
            text_vbox.pack_start(info_label, False, False, 0)

            self.listbox.add(row)

        self.listbox.show_all()
