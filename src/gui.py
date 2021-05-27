#!/usr/bin/env python3
import trio
import sys
from functools import partial

import config
from bridge import Proxy

import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('AppIndicator3', '0.1')
gi.require_version('GdkPixbuf', '2.0')

# pylint: disable=E402
from gi.repository import Gtk            # noqa: E402
from gi.repository import Gdk            # noqa: E402
from gi.repository import GLib           # noqa: E402
from gi.repository import AppIndicator3  # noqa: E402
from gi.repository import GdkPixbuf      # noqa: E402
# pylint: enable=E402


class Indicator:
    def __init__(self, vpn: Proxy, nursery: trio.Nursery):
        self.indicator = AppIndicator3.Indicator.new(
            config.APPNAME,
            config.APPNAME,
            AppIndicator3.IndicatorCategory.APPLICATION_STATUS
        )
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        self.indicator.set_menu(self.build_menu())
        self.set_icon()
        self.vpn = vpn
        self.nursery = nursery
        self.running = True

    def build_menu(self):
        menu = Gtk.Menu()

        menu_hello = Gtk.MenuItem.new_with_label("Hello")
        menu_hello.connect("activate", self.hello)
        menu.append(menu_hello)

        menu_toggle = Gtk.MenuItem.new_with_label("Toggle")
        menu_toggle.connect("activate", self.toggle)
        menu.append(menu_toggle)

        menu.append(Gtk.SeparatorMenuItem())

        menu_connect = Gtk.MenuItem.new_with_label("Connect")
        menu_connect.connect("activate", self.connect)
        menu.append(menu_connect)

        menu_disconnect = Gtk.MenuItem.new_with_label("Disconnect")
        menu_disconnect.connect("activate", self.disconnect)
        menu.append(menu_disconnect)

        menu_list = Gtk.MenuItem.new_with_label("List")
        menu_list.connect("activate", self.list)
        menu.append(menu_list)

        menu.append(Gtk.SeparatorMenuItem())

        menu_control = Gtk.MenuItem.new_with_label("Control")
        menu_control.connect("activate", self.menu_control_response)
        menu.append(menu_control)

        menu.append(Gtk.SeparatorMenuItem())

        menu_help = Gtk.MenuItem.new_with_label("Help")
        menu_help.set_submenu(self.build_help_menu())
        menu.append(menu_help)

        menu.append(Gtk.SeparatorMenuItem())

        menu_quit = Gtk.MenuItem.new_with_label("Quit")
        menu_quit.connect("activate", self.quit)
        menu.append(menu_quit)

        menu.show_all()
        return menu

    def build_help_menu(self):
        help_menu = Gtk.Menu()

        about_item = Gtk.MenuItem.new_with_label("About")
        about_item.connect("activate", self.menu_about_response)
        help_menu.append(about_item)

        return help_menu

    def menu_about_response(self, widget):
        widget.set_sensitive(False)
        about = Gtk.AboutDialog()
        about.set_name(config.APPNAME)
        about.set_version(config.VERSION)
        about.set_copyright("Copyright (c) 2021\nziirish")
        about.set_comments(config.APPNAME)
        about.set_logo(GdkPixbuf.Pixbuf.new_from_file(config.ICON))
        about.set_icon(GdkPixbuf.Pixbuf.new_from_file(config.ICON))
        about.set_program_name(config.APPNAME)

        about.set_license("""
Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
""")

        monitor = Gdk.Display.get_primary_monitor(Gdk.Display.get_default())
        scale = monitor.get_scale_factor()
        monitor_width = monitor.get_geometry().width / scale
        monitor_height = monitor.get_geometry().height / scale
        width = about.get_preferred_width()[0]
        height = about.get_preferred_height()[0]
        about.move((monitor_width - width)/2, (monitor_height - height)/2)

        about.run()
        about.destroy()
        widget.set_sensitive(True)

    def menu_control_response(self, widget):
        widget.set_sensitive(False)
        control = Settings(self.nursery)

        func = partial(self.vpn.send, "list", callback=control.refresh_list)
        self.nursery.start_soon(func)

        control.run()
        control.destroy()
        widget.set_sensitive(True)

    def set_icon(self, active=True):
        self.state = active
        if self.state:
            icon = config.ICON_ACTIVED
        else:
            icon = config.ICON_PAUSED
        self.indicator.set_icon_full(icon, config.APPNAME)

    def quit(self, menu_item):
        self.running = False

    def disconnect(self, menu_item):
        self.nursery.start_soon(self.vpn.send, "disconnect")
        self.set_icon(False)

    def connect(self, menu_item):
        self.nursery.start_soon(self.vpn.send, "connect")
        self.set_icon()

    def list(self, menu_item):
        func = partial(self.vpn.send, "list", callback=print)
        self.nursery.start_soon(func)

    def hello(self, menu_item):
        print("Hello", menu_item)

    def toggle(self, menu_item):
        self.set_icon(not self.state)


class Settings(Gtk.Dialog):
    def __init__(self, nursery):
        self.nursery = nursery
        super(Settings, self).__init__(config.APPNAME, None)

        self.set_modal(True)
        self.set_destroy_with_parent(True)
        self.set_default_response(Gtk.ResponseType.ACCEPT)
        self.set_resizable(False)
        self.set_icon_from_file(config.ICON)
        self.connect('realize', self.on_realize)
        self.init_ui()
        self.show_all()

    def init_ui(self):
        """
        """

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

        vbox1 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.grid.add(vbox1)

        stack = Gtk.Stack()
        stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        stack.set_transition_duration(1000)

        spinner = Gtk.Spinner()
        spinner.start()
        stack.add_titled(spinner, "traffic", "Traffic")

        label = Gtk.Label()
        label.set_markup("<big>A fancy label</big>")
        stack.add_titled(label, "streaming", "Streaming")

        stack_switcher = Gtk.StackSwitcher()
        stack_switcher.set_stack(stack)
        vbox1.pack_start(stack_switcher, True, True, 0)
        vbox1.pack_start(stack, True, True, 0)
        self.stack = stack

    def refresh_list(self, servers):
        spinner = self.stack.get_child_by_name("traffic")
        spinner.stop()
        spinner.destroy()

        self.server_liststore = Gtk.ListStore(str, str)
        for server in servers:
            self.server_liststore.append(list(server))

        self.current_filter_server = None

        # Creating the filter, feeding it with the liststore model
        self.server_filter = self.server_liststore.filter_new()
        # setting the filter function, note that we're not using the
        self.server_filter.set_visible_func(self.server_filter_func)

        self.treeview = Gtk.TreeView(model=self.server_filter)
        for i, column_title in enumerate(
            ["Country Name", "Country Code"]
        ):
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(column_title, renderer, text=i)
            self.treeview.append_column(column)

        self.stack.add_titled(self.treeview, "traffic", "Traffic")
        self.show_all()

    def server_filter_func(self, model, iter, data):
        """Tests if the language in the row is the one in the filter"""
        if (
            self.current_filter_server is None
            or self.current_filter_server == "None"
        ):
            return True
        else:
            return model[iter][2] == self.current_filter_server

    def on_realize(self, *_):
        monitor = Gdk.Display.get_primary_monitor(Gdk.Display.get_default())
        scale = monitor.get_scale_factor()
        monitor_width = monitor.get_geometry().width / scale
        monitor_height = monitor.get_geometry().height / scale
        width = self.get_preferred_width()[0]
        height = self.get_preferred_height()[0]
        self.move((monitor_width - width)/2, (monitor_height - height)/2)


if __name__ == "__main__":
    indicator = Indicator()
    Gtk.main()
