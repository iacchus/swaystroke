import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from .gui_tabs import GesturesTab, HistoryTab
from .config import CONFIG, save_config

class MainWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="Swaystroke GUI")
        self.set_default_size(500, 650)
        self.set_border_width(10)
        
        settings = Gtk.Settings.get_default()
        if settings:
            settings.set_property("gtk-application-prefer-dark-theme", True)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.add(vbox)

        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        vbox.pack_start(header_box, False, False, 0)
        
        settings_btn = Gtk.Button(label="Settings")
        settings_btn.connect("clicked", self.on_settings_clicked)
        header_box.pack_end(settings_btn, False, False, 0)

        notebook = Gtk.Notebook()
        vbox.pack_start(notebook, True, True, 0)
        
        gestures_tab = GesturesTab()
        notebook.append_page(gestures_tab, Gtk.Label(label="Gestures"))
        
        history_tab = HistoryTab()
        notebook.append_page(history_tab, Gtk.Label(label="History"))
        
        self.connect("destroy", Gtk.main_quit)

    def on_settings_clicked(self, button):
        dialog = Gtk.Dialog(title="Settings", parent=self, flags=0)
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_SAVE, Gtk.ResponseType.OK)
        
        box = dialog.get_content_area()
        box.set_spacing(10)
        box.set_margin_top(10)
        box.set_margin_bottom(10)
        box.set_margin_start(10)
        box.set_margin_end(10)
        
        settings_notebook = Gtk.Notebook()
        box.pack_start(settings_notebook, True, True, 0)
        
        # General Tab
        general_grid = Gtk.Grid(row_spacing=10, column_spacing=10)
        general_grid.set_margin_top(10)
        general_grid.set_margin_bottom(10)
        general_grid.set_margin_start(10)
        general_grid.set_margin_end(10)
        
        general_grid.attach(Gtk.Label(label="Multistroke Timeout (ms):", halign=Gtk.Align.START), 0, 0, 1, 1)
        timeout_entry = Gtk.Entry()
        timeout_entry.set_text(str(CONFIG.get("multistroke_timeout", 500)))
        general_grid.attach(timeout_entry, 1, 0, 1, 1)
        
        general_grid.attach(Gtk.Label(label="History Limit (0 to disable):", halign=Gtk.Align.START), 0, 1, 1, 1)
        history_entry = Gtk.Entry()
        history_entry.set_text(str(CONFIG.get("history_limit", 30)))
        general_grid.attach(history_entry, 1, 1, 1, 1)
        
        settings_notebook.append_page(general_grid, Gtk.Label(label="General"))
        
        # Trail Tab
        trail_grid = Gtk.Grid(row_spacing=10, column_spacing=10)
        trail_grid.set_margin_top(10)
        trail_grid.set_margin_bottom(10)
        trail_grid.set_margin_start(10)
        trail_grid.set_margin_end(10)
        
        trail_grid.attach(Gtk.Label(label="Color (Hex):", halign=Gtk.Align.START), 0, 0, 1, 1)
        trail_color_entry = Gtk.Entry()
        trail_color_entry.set_text(CONFIG["trail"].get("color", "#ff0000"))
        trail_grid.attach(trail_color_entry, 1, 0, 1, 1)
        
        trail_grid.attach(Gtk.Label(label="Opacity (0.0 - 1.0):", halign=Gtk.Align.START), 0, 1, 1, 1)
        trail_opacity_entry = Gtk.Entry()
        trail_opacity_entry.set_text(str(CONFIG["trail"].get("opacity", 1.0)))
        trail_grid.attach(trail_opacity_entry, 1, 1, 1, 1)
        
        trail_grid.attach(Gtk.Label(label="Width (px):", halign=Gtk.Align.START), 0, 2, 1, 1)
        trail_width_entry = Gtk.Entry()
        trail_width_entry.set_text(str(CONFIG["trail"].get("width", 4)))
        trail_grid.attach(trail_width_entry, 1, 2, 1, 1)
        
        settings_notebook.append_page(trail_grid, Gtk.Label(label="Trail"))
        
        # Overlay Tab
        overlay_grid = Gtk.Grid(row_spacing=10, column_spacing=10)
        overlay_grid.set_margin_top(10)
        overlay_grid.set_margin_bottom(10)
        overlay_grid.set_margin_start(10)
        overlay_grid.set_margin_end(10)
        
        overlay_grid.attach(Gtk.Label(label="Color (Hex):", halign=Gtk.Align.START), 0, 0, 1, 1)
        overlay_color_entry = Gtk.Entry()
        overlay_color_entry.set_text(CONFIG["overlay"].get("color", "#000000"))
        overlay_grid.attach(overlay_color_entry, 1, 0, 1, 1)
        
        overlay_grid.attach(Gtk.Label(label="Opacity (0.0 - 1.0):", halign=Gtk.Align.START), 0, 1, 1, 1)
        overlay_opacity_entry = Gtk.Entry()
        overlay_opacity_entry.set_text(str(CONFIG["overlay"].get("opacity", 0.1)))
        overlay_grid.attach(overlay_opacity_entry, 1, 1, 1, 1)
        
        overlay_grid.attach(Gtk.Label(label="Text Prompt:", halign=Gtk.Align.START), 0, 2, 1, 1)
        overlay_text_entry = Gtk.Entry()
        overlay_text_entry.set_text(CONFIG["overlay"].get("text", ""))
        overlay_grid.attach(overlay_text_entry, 1, 2, 1, 1)
        
        settings_notebook.append_page(overlay_grid, Gtk.Label(label="Overlay"))
        
        dialog.show_all()
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            try:
                CONFIG["multistroke_timeout"] = int(timeout_entry.get_text())
                CONFIG["history_limit"] = int(history_entry.get_text())
                CONFIG["trail"]["color"] = trail_color_entry.get_text()
                CONFIG["trail"]["opacity"] = float(trail_opacity_entry.get_text())
                CONFIG["trail"]["width"] = int(trail_width_entry.get_text())
                CONFIG["overlay"]["color"] = overlay_color_entry.get_text()
                CONFIG["overlay"]["opacity"] = float(overlay_opacity_entry.get_text())
                CONFIG["overlay"]["text"] = overlay_text_entry.get_text()
                save_config()
            except ValueError:
                print("Invalid value entered in settings.")
                
        dialog.destroy()

def run_gui():
    win = MainWindow()
    win.show_all()
    Gtk.main()
