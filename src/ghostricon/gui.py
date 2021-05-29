#!/usr/bin/env python3
import trio
import sys
from functools import partial

from ghostricon import config
from ghostricon.bridge import Proxy

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
        self.state = False

        self.indicator = AppIndicator3.Indicator.new(
            config.APPNAME,
            config.APPNAME,
            AppIndicator3.IndicatorCategory.APPLICATION_STATUS
        )
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        self.set_icon()
        self.indicator.set_menu(self.build_menu())
        self.vpn = vpn
        self.nursery = nursery
        self.running = True

    def build_menu(self):
        menu = Gtk.Menu()

        """
        menu_hello = Gtk.MenuItem.new_with_label("Hello")
        menu_hello.connect("activate", self.hello)
        menu.append(menu_hello)

        menu_toggle = Gtk.MenuItem.new_with_label("Toggle")
        menu_toggle.connect("activate", self.toggle)
        menu.append(menu_toggle)
        menu_status = Gtk.MenuItem.new_with_label("Connected" if self.state
                                                  else "Disconnected")
        menu_status.set_sensitive(False)
        menu.append(menu_status)

        menu.append(Gtk.SeparatorMenuItem())
        """

        menu_spin = Gtk.MenuItem.new_with_label("Spin")
        menu_spin.connect("activate", self.show_spin)
        menu.append(menu_spin)

        if not self.state:
            menu_connect = Gtk.MenuItem.new_with_label("Connect")
            menu_connect.connect("activate", self.connect)
            menu.append(menu_connect)
        else:
            menu_disconnect = Gtk.MenuItem.new_with_label("Disconnect")
            menu_disconnect.connect("activate", self.disconnect)
            menu.append(menu_disconnect)

        """
        menu_list = Gtk.MenuItem.new_with_label("List")
        menu_list.connect("activate", self.list)
        menu.append(menu_list)
        """

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
MIT License

Permission is hereby granted, free of charge, to any person
obtaining a copy of this software and associated documentation
files (the "Software"), to deal in the Software without
restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to
whom the Software is furnished to do so, subject to the
following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY
OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT
LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
""")

        display = Gdk.Display.get_default()
        monitor = Gdk.Display.get_primary_monitor(display)
        if not monitor:
            monitor = display.get_monitor(0)
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
        # widget.set_sensitive(False)
        control = Settings(self.nursery)

        func = partial(self.vpn.send, "list", callback=control.refresh_list)
        self.nursery.start_soon(func)

        """
        control.run()
        control.destroy()
        widget.set_sensitive(True)
        """

    def set_icon(self, active=True):
        if active == self.state:
            return
        self.state = active
        if self.state:
            icon = config.ICON_ACTIVED
        else:
            icon = config.ICON_PAUSED
        self.indicator.set_icon_full(icon, config.APPNAME)
        self.indicator.set_menu(self.build_menu())

    def show_spin(self, menu_item):
        win = SpinnerWindow()
        win.show_all()

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


class Settings(Gtk.Window):
    def __init__(self, nursery):
        self.nursery = nursery

        Gtk.Window.__init__(self, title="Stack Demo")
        self.set_border_width(10)
        self.set_position(Gtk.WindowPosition.CENTER)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(vbox)

        stack = Gtk.Stack()
        stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        stack.set_transition_duration(1000)

        checkbutton = Gtk.CheckButton(label="Click me!")
        stack.add_titled(checkbutton, "check", "Check Button")

        label = Gtk.Label()
        label.set_markup("<big>A fancy label</big>")
        stack.add_titled(label, "label", "A label")

        stack_switcher = Gtk.StackSwitcher()
        stack_switcher.set_stack(stack)
        vbox.pack_start(stack_switcher, True, True, 0)
        vbox.pack_start(stack, True, True, 0)

        self.connect("destroy", self.on_destroy)
        self.show_all()

    def refresh_list(self, servers):
        print("GOT SERVERS", servers)

    def on_destroy(self, widget):
        self.destroy()


class Settings2(Gtk.Dialog):
    def __init__(self, nursery):
        self.nursery = nursery
        super(Settings, self).__init__(config.APPNAME, None)

        self.set_modal(True)
        self.set_destroy_with_parent(True)
        self.set_default_response(Gtk.ResponseType.ACCEPT)
        self.set_border_width(3)
        self.set_resizable(True)
        self.set_default_size(500, 500)
        self.set_icon_from_file(config.ICON)
        self.connect('realize', self.on_realize)
        # self.show()
        self.init_ui()
        self.show_all()

    def init_ui(self):
        self.notebook = Gtk.Notebook()
        self.get_content_area().add(self.notebook)

        self.page1 = Gtk.Box()
        self.page1.set_border_width(10)
        # self.page1.add(Gtk.Label(label="Default Page!"))
        self.page1.add(self.build_vbox_traffic())
        self.notebook.append_page(self.page1, Gtk.Label(label="Traffic"))

        self.page2 = Gtk.Box()
        self.page2.set_border_width(10)
        self.page2.add(Gtk.Label(label="A page with an image for a Title."))
        self.notebook.append_page(
            self.page2, Gtk.Image.new_from_icon_name("help-about", Gtk.IconSize.MENU)
        )

    def init_ui2(self):

        vbox0 = Gtk.VBox(spacing=5)
        vbox0.set_border_width(5)
        self.get_content_area().add(vbox0)

        """
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
        """

        """
        vbox1 = Gtk.VBox(spacing=5)
        self.grid.add(vbox1)
        """

        stack = Gtk.Stack()
        stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        stack.set_transition_duration(1000)
        stack.set_homogeneous(False)

        vbox_traffic = self.build_vbox_traffic()
        stack.add_titled(vbox_traffic, "traffic", "Traffic")

        label = Gtk.Label()
        label.set_markup("<big>A fancy label</big>")
        stack.add_titled(label, "streaming", "Streaming")

        stack_switcher = Gtk.StackSwitcher()
        stack_switcher.set_stack(stack)
        vbox0.pack_start(stack_switcher, True, True, 0)
        vbox0.pack_start(stack, True, True, 0)
        self.stack = stack

    def build_vbox_traffic(self):
        vbox_traffic = Gtk.Box()
        """
        self.spinner_traffic = Gtk.Spinner()
        self.spinner_traffic.start()
        """

        self.server_liststore = Gtk.ListStore(str, str)
        """
        for server in servers:
            self.server_liststore.append(list(server))
        """

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

        self.scrollable_treelist = Gtk.ScrolledWindow()
        self.scrollable_treelist.set_vexpand(True)
        self.scrollable_treelist.add(self.treeview)

        # vbox_traffic.pack_start(self.spinner_traffic, False, False, 0)
        vbox_traffic.pack_start(self.scrollable_treelist, True, True, 0)
        self.vbox_traffic = vbox_traffic
        self.vbox_traffic.show_all()
        self.scrollable_treelist.hide()
        return self.vbox_traffic

    def refresh_list(self, servers):
        self.server_liststore.clear()
        for server in servers:
            self.server_liststore.append(server)

        """
        self.spinner_traffic.stop()
        self.spinner_traffic.hide()
        """
        self.scrollable_treelist.show_all()
        """
        spinner = self.stack.get_child_by_name("traffic")
        spinner.stop()
        spinner.destroy()

        self.show_all()
        """

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
        display = Gdk.Display.get_default()
        monitor = Gdk.Display.get_primary_monitor(display)
        if not monitor:
            monitor = display.get_monitor(0)
        scale = monitor.get_scale_factor()
        monitor_width = monitor.get_geometry().width / scale
        monitor_height = monitor.get_geometry().height / scale
        """
        width = self.get_preferred_width()[0]
        height = self.get_preferred_height()[0]
        """
        width = 500
        height = 500
        self.move((monitor_width - width)/2, (monitor_height - height)/2)


class SpinnerWindow(Gtk.Window):
    def __init__(self, *args, **kwargs):
        Gtk.Window.__init__(self, title="Spinner Demo")
        self.set_border_width(10)

        mainBox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(mainBox)

        self.spinner = Gtk.Spinner()
        mainBox.pack_start(self.spinner, True, True, 0)

        self.label = Gtk.Label()
        mainBox.pack_start(self.label, True, True, 0)

        self.entry = Gtk.Entry()
        self.entry.set_text("10")
        mainBox.pack_start(self.entry, True, True, 0)

        self.buttonStart = Gtk.Button(label="Start timer")
        self.buttonStart.connect("clicked", self.on_buttonStart_clicked)
        mainBox.pack_start(self.buttonStart, True, True, 0)

        self.buttonStop = Gtk.Button(label="Stop timer")
        self.buttonStop.set_sensitive(False)
        self.buttonStop.connect("clicked", self.on_buttonStop_clicked)
        mainBox.pack_start(self.buttonStop, True, True, 0)

        self.timeout_id = None
        self.connect("destroy", self.on_SpinnerWindow_destroy)

    def on_buttonStart_clicked(self, widget, *args):
        """ Handles "clicked" event of buttonStart. """
        self.start_timer()

    def on_buttonStop_clicked(self, widget, *args):
        """ Handles "clicked" event of buttonStop. """
        self.stop_timer("Stopped from button")

    def on_SpinnerWindow_destroy(self, widget, *args):
        """ Handles destroy event of main window. """
        # ensure the timeout function is stopped
        if self.timeout_id:
            GLib.source_remove(self.timeout_id)
            self.timeout_id = None
        self.hide()
        self.destroy()
        # Gtk.main_quit()

    def on_timeout(self, *args, **kwargs):
        """ A timeout function.

        Return True to stop it.
        This is not a precise timer since next timeout
        is recalculated based on the current time."""
        self.counter -= 1
        if self.counter <= 0:
            self.stop_timer("Reached time out")
            return False
        self.label.set_label("Remaining: " + str(int(self.counter / 4)))
        return True

    def start_timer(self):
        """ Start the timer. """
        self.buttonStart.set_sensitive(False)
        self.buttonStop.set_sensitive(True)
        # time out will check every 250 miliseconds (1/4 of a second)
        self.counter = 4 * int(self.entry.get_text())
        self.label.set_label("Remaining: " + str(int(self.counter / 4)))
        self.spinner.start()
        self.timeout_id = GLib.timeout_add(250, self.on_timeout, None)

    def stop_timer(self, alabeltext):
        """ Stop the timer. """
        if self.timeout_id:
            GLib.source_remove(self.timeout_id)
            self.timeout_id = None
        self.spinner.stop()
        self.buttonStart.set_sensitive(True)
        self.buttonStop.set_sensitive(False)
        self.label.set_label(alabeltext)


if __name__ == "__main__":
    indicator = Indicator()
    Gtk.main()
