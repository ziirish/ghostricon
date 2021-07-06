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


class Settings(Gtk.Dialog):
    def __init__(self, nursery: trio.Nursery, vpn: Proxy):
        super(Settings, self).__init__("VPN Settings")
        self.set_icon_from_file(constants.ICON)
        self.set_modal(True)
        self.set_default_size(500, 500)
        self.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
        self.add_button("Connect", Gtk.ResponseType.ACCEPT)
        self.config = get_config()
        self.nursery = nursery
        self.vpn = vpn
        self.connect('realize', self.on_realize)
        self.init_ui()
        self.show_all()
        self.load()

    def save(self, update_default: bool = False):
        if update_default:
            current_page = self.notebook.get_current_page()
            label, liststore = self.pages[current_page]
            path, _ = getattr(self, f"{label.lower()}_treeview").get_cursor()
            if path:
                row = liststore[path]
                self.config["Global"]["default_type"] = label
                self.config["Global"]["default_country"] = row[0]

        for kind, liststore in self.pages:
            fav = []
            for row in liststore:
                if row[2]:
                    fav.append(row[0])
            self.config["Favorite"][kind.lower()] = ";".join(fav)

        save_config()

    def load(self):
        func0 = partial(self.vpn.send, "list", callback=self.refresh_traffic_servers)
        func1 = partial(self.vpn.send, "list",
                        "streaming", callback=self.refresh_streaming_servers)
        func2 = partial(self.vpn.send, "list",
                        "torrent", callback=self.refresh_torrent_servers)
        self.nursery.start_soon(func0)
        self.nursery.start_soon(func1)
        self.nursery.start_soon(func2)

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

        self.notebook = Gtk.Notebook()
        frame1.add(self.notebook)

        self.current_filter_server = None

        self.traffic_liststore = Gtk.ListStore(str, str, bool)
        self.streaming_liststore = Gtk.ListStore(str, str, bool)
        self.torrent_liststore = Gtk.ListStore(str, str, bool)
        self.pages = [
            ["Traffic", self.traffic_liststore],
            ["Streaming", self.streaming_liststore],
            ["Torrent", self.torrent_liststore],
        ]
        default_loading = [["Loading", "...", False]]
        for label, liststore in self.pages:
            self.build_page(label, liststore, default_loading)

    def build_page(self, label: str, liststore: Gtk.Widget, servers: list):
        for server in servers:
            liststore.append(list(server))

        # Creating the filter, feeding it with the liststore model
        server_filter = liststore.filter_new()
        # setting the filter function, note that we're not using the
        server_filter.set_visible_func(self.server_filter_func)

        treeview = Gtk.TreeView(model=server_filter)
        setattr(self, f"{label.lower()}_treeview", treeview)

        for i, column_title in enumerate(
            ["Country Name", "Country Code", "Favorite"]
        ):
            if column_title == "Favorite":
                renderer = Gtk.CellRendererToggle()
                renderer.connect("toggled",
                                 getattr(self, f"on_cell_{label.lower()}_toggled"))
                column = Gtk.TreeViewColumn(column_title, renderer, active=i)
            else:
                renderer = Gtk.CellRendererText()
                column = Gtk.TreeViewColumn(column_title, renderer, text=i)
            treeview.append_column(column)

        scroll_tree = Gtk.ScrolledWindow()
        scroll_tree.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll_tree.add(treeview)
        scroll_tree.set_min_content_height(450)
        self.notebook.append_page(scroll_tree, Gtk.Label(label))
        self.show_all()

    def on_cell_traffic_toggled(self, widget, path):
        self.traffic_liststore[path][2] = not self.traffic_liststore[path][2]

    def on_cell_streaming_toggled(self, widget, path):
        self.streaming_liststore[path][2] = not self.streaming_liststore[path][2]

    def on_cell_torrent_toggled(self, widget, path):
        self.torrent_liststore[path][2] = not self.torrent_liststore[path][2]

    def refresh_traffic_servers(self, servers):
        self.traffic_liststore.clear()
        fav = self.config["Favorite"].get("traffic").split(";")
        for server in servers:
            lst = list(server)
            self.traffic_liststore.append(lst + [lst[0] in fav])
        self.show_all()

    def refresh_streaming_servers(self, servers):
        self.streaming_liststore.clear()
        fav = self.config["Favorite"].get("streaming").split(";")
        for server in servers:
            lst = list(server)
            self.streaming_liststore.append(lst + [lst[0] in fav])
        self.show_all()

    def refresh_torrent_servers(self, servers):
        self.torrent_liststore.clear()
        fav = self.config["Favorite"].get("torrent").split(";")
        for server in servers:
            lst = list(server)
            self.torrent_liststore.append(lst + [lst[0] in fav])
        self.show_all()

    def server_filter_func(self, model, path, data):
        """Tests if the server in the row is the one in the filter"""
        if (
            self.current_filter_server is None
            or self.current_filter_server == "None"
        ):
            return True
        else:
            return model[path][2] == self.current_filter_server
