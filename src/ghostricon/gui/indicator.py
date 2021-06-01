#!/usr/bin/env python3
import trio
import sys
from functools import partial

from ghostricon import constants
from ghostricon.config import get_config
from ghostricon.bridge import Proxy
from ghostricon.gui.notification import Notification
from ghostricon.gui.configuration import Configuration

import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('AppIndicator3', '0.1')
gi.require_version('GdkPixbuf', '2.0')

# pylint: disable=E402
from gi.repository import Gtk            # noqa: E402
from gi.repository import Gdk            # noqa: E402
from gi.repository import AppIndicator3  # noqa: E402
from gi.repository import GdkPixbuf      # noqa: E402
# pylint: enable=E402


class Indicator:
    def __init__(self, vpn: Proxy, nursery: trio.Nursery):
        self.state = False

        self.indicator = AppIndicator3.Indicator.new(
            constants.APPNAME,
            constants.APPNAME,
            AppIndicator3.IndicatorCategory.APPLICATION_STATUS
        )
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        self.set_icon()
        self.indicator.set_menu(self.build_menu())
        self.vpn = vpn
        self.config = get_config()["Global"]
        self.nursery = nursery
        self.running = True

    def build_menu(self):
        menu = Gtk.Menu()

        if not self.state:
            menu_connect = Gtk.MenuItem.new_with_label("Connect")
            menu_connect.connect("activate", self.connect)
            menu.append(menu_connect)
        else:
            menu_disconnect = Gtk.MenuItem.new_with_label("Disconnect")
            menu_disconnect.connect("activate", self.disconnect)
            menu.append(menu_disconnect)

        menu_favorite = Gtk.MenuItem.new_with_label("Favorites")
        menu_favorite.set_submenu(self.build_favorite_menu())
        menu.append(menu_favorite)

        menu.append(Gtk.SeparatorMenuItem())

        menu_configuration = Gtk.MenuItem.new_with_label("Configuration")
        menu_configuration.connect("activate", self.configuration)
        menu.append(menu_configuration)

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

    def build_favorite_menu(self):
        favorite_menu = Gtk.Menu()

        for i in range(50):
            entry = Gtk.MenuItem.new_with_label(f"Entry {i}")
            favorite_menu.append(entry)

        return favorite_menu

    def menu_about_response(self, widget):
        widget.set_sensitive(False)
        about = Gtk.AboutDialog()
        about.set_name(constants.APPNAME)
        about.set_version(constants.VERSION)
        about.set_copyright("Copyright (c) 2021\nziirish")
        about.set_comments(constants.APPNAME)
        about.set_logo(GdkPixbuf.Pixbuf.new_from_file(constants.ICON))
        about.set_icon(GdkPixbuf.Pixbuf.new_from_file(constants.ICON))
        about.set_program_name(constants.APPNAME)

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

    def configuration(self, widget):
        widget.set_sensitive(False)
        configuration = Configuration(self.nursery, self.vpn)
        response = configuration.run()
        if response == Gtk.ResponseType.ACCEPT:
            configuration.save()
        configuration.destroy()
        widget.set_sensitive(True)

    def set_icon(self, active=True):
        if active == self.state:
            return
        self.state = active
        if self.state:
            icon = constants.ICON_ACTIVED
        else:
            icon = constants.ICON_PAUSED
        self.indicator.set_icon_full(icon, constants.APPNAME)
        self.indicator.set_menu(self.build_menu())

    def quit(self, menu_item):
        self.running = False

    def disconnect(self, menu_item):
        def callback(status):
            self.set_icon(status)
            if status:
                Notification.display("Failed to disconnect!")
            else:
                Notification.display("Successfully disconnected")

        func = partial(self.vpn.send, "disconnect", callback=callback)
        self.nursery.start_soon(func)

    def connect(self, menu_item):
        def callback(status):
            self.set_icon(status)
            if not status:
                Notification.display("Failed to connect!")
            else:
                Notification.display("Successfully connected")

        func = partial(self.vpn.send, "connect", callback=callback)
        self.nursery.start_soon(func)

    def toggle(self, menu_item):
        self.set_icon(not self.state)


if __name__ == "__main__":
    indicator = Indicator()
    Gtk.main()
