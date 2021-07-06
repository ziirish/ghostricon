import trio
from functools import partial

from ghostricon import constants
from ghostricon.bridge import Proxy
from ghostricon.config import get_config, save_config
from ghostricon.commands import server_types

import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

# pylint: disable=E402
from gi.repository import Gtk            # noqa: E402
from gi.repository import Gdk            # noqa: E402
# pylint: enable=E402


def set_combo_loading(combo: Gtk.ComboBox):
    model = combo.get_model()
    model.clear()
    model.append(["Loading..."])
    combo.set_active(0)
    combo.set_sensitive(False)


def select_in_combo(combo: Gtk.ComboBox, value: str):
    model = combo.get_model()
    for i, item in enumerate(model):
        if value == item[0]:
            combo.set_active(i)
            break
    else:
        combo.set_active(0)


def get_selected_in_combo(combo: Gtk.ComboBox) -> str:
    model = combo.get_model()
    return model.get_value(combo.get_active_iter(), 0)


class Configuration(Gtk.Dialog):
    def __init__(self, nursery: trio.Nursery, vpn: Proxy):
        super(Configuration, self).__init__("Configuration")
        self.set_icon_from_file(constants.ICON)
        self.set_modal(True)
        self.add_button(Gtk.STOCK_OK, Gtk.ResponseType.ACCEPT)
        self.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
        self.set_default_response(Gtk.ResponseType.ACCEPT)
        self.set_resizable(False)
        self.config = get_config()["Global"]
        self.nursery = nursery
        self.vpn = vpn
        self.connect('realize', self.on_realize)
        self.init_ui()
        select_in_combo(self.server_type,
                        self.config.get("default_type"))
        self.show_all()
        self.load()

    def save(self):
        self.config["connect_on_startup"] = str(
            self.connect_on_startup.get_active()
        ).lower()
        self.config["disconnect_on_exit"] = str(
            self.disconnect_on_exit.get_active()
        ).lower()
        self.config["notifications"] = str(
            self.notifications.get_active()
        ).lower()
        self.config["default_type"] = get_selected_in_combo(self.server_type)
        default_country = get_selected_in_combo(self.server_country)
        if default_country != "Loading...":
            self.config["default_country"] = default_country
        save_config()

    def load(self):
        self.connect_on_startup.set_active(
            self.config.getboolean("connect_on_startup")
        )
        self.disconnect_on_exit.set_active(
            self.config.getboolean("disconnect_on_exit")
        )
        self.notifications.set_active(
            self.config.getboolean("notifications")
        )
        default_type = self.config.get("default_type")
        select_in_combo(self.server_type, default_type)

    def on_realize(self, *_):
        display = Gdk.Display.get_default()
        monitor = Gdk.Display.get_primary_monitor(display)
        if not monitor:
            monitor = display.get_monitor(0)
        scale = monitor.get_scale_factor()
        monitor_width = monitor.get_geometry().width / scale
        monitor_height = monitor.get_geometry().height / scale
        width = self.get_preferred_width()[0]
        height = self.get_preferred_height()[0]
        self.move((monitor_width - width)/2, (monitor_height - height)/2)

    def init_ui(self):
        vbox0 = Gtk.VBox(spacing=5)
        vbox0.set_border_width(5)
        self.get_content_area().add(vbox0)

        frame1 = Gtk.Frame()
        vbox0.add(frame1)

        self.grid = Gtk.Grid()
        self.grid.set_row_spacing(10)
        self.grid.set_column_spacing(10)
        self.grid.set_margin_bottom(10)
        self.grid.set_margin_start(10)
        self.grid.set_margin_end(10)
        self.grid.set_margin_top(10)
        frame1.add(self.grid)

        self.grid.attach(Gtk.Label.new("Connect on startup:"), 0, 0, 1, 1)
        self.connect_on_startup = Gtk.Switch.new()
        self.grid.attach(self.connect_on_startup, 1, 0, 1, 1)
        self.grid.attach(Gtk.Label.new("Disconnect on exit:"), 0, 1, 1, 1)
        self.disconnect_on_exit = Gtk.Switch.new()
        self.grid.attach(self.disconnect_on_exit, 1, 1, 1, 1)
        self.grid.attach(Gtk.Label.new("Show notifications:"), 0, 2, 1, 1)
        self.notifications = Gtk.Switch.new()
        self.grid.attach(self.notifications, 1, 2, 1, 1)

        self.grid.attach(Gtk.Separator(), 0, 3, 2, 1)

        label0 = Gtk.Label("Server type:")
        label0.set_alignment(0, 0.5)
        self.grid.attach(label0, 0, 4, 1, 1)

        servers = Gtk.ListStore(str)
        for st in server_types.keys():
            servers.append([st.capitalize()])

        self.server_type = Gtk.ComboBox.new_with_model(servers)
        self.server_type.connect("changed", self.on_server_type_changed)
        cell0 = Gtk.CellRendererText()
        self.server_type.pack_start(cell0, True)
        self.server_type.add_attribute(cell0, "text", 0)
        self.grid.attach(self.server_type, 1, 4, 1, 1)

        label1 = Gtk.Label("Server country:")
        label1.set_alignment(0, 0.5)
        self.grid.attach(label1, 0, 5, 1, 1)

        self.countries = Gtk.ListStore(str)

        self.server_country = Gtk.ComboBox.new_with_model(self.countries)
        cell1 = Gtk.CellRendererText()
        self.server_country.pack_start(cell1, True)
        self.server_country.add_attribute(cell1, "text", 0)
        self.grid.attach(self.server_country, 1, 5, 1, 1)

    def on_server_type_changed(self, combo: Gtk.ComboBox):
        server_type = get_selected_in_combo(combo)
        self.refresh_server_country(server_type)

    def refresh_server_country(self, server_type: str):
        set_combo_loading(self.server_country)

        def callback(countries):
            self.countries.clear()
            for country in countries:
                self.countries.append([country[0]])
            select_in_combo(self.server_country,
                            self.config.get("default_country"))
            self.server_country.set_sensitive(True)

        func = partial(self.vpn.send, "list",
                       kind=server_type.lower(), callback=callback)
        self.nursery.start_soon(func)
