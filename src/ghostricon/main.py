#!/usr/bin/env python3
import os
import trio
import logging
from getpass import getuser

from ghostricon import config
from ghostricon.gui import Indicator
from ghostricon.daemon import Daemon
from ghostricon.bridge import Proxy
from ghostricon.privileged import Launcher

import gi
gi.require_version('Gtk', '3.0')
# pylint: disable=E402
from gi.repository import Gtk    # noqa: E402

import trio_gtk                  # noqa: E402

# pylint: enable=E402


async def async_main():
    user = getuser()
    socket = config.SOCKET
    if os.path.exists(socket):
        os.unlink(socket)

    logging.debug(f"Starting with user: {user} on {socket}")

    privileged = Launcher(socket, user)
    privileged.start()

    vpn = Proxy(socket)

    nursery: trio.Nursery
    async with trio.open_nursery() as nursery:
        indicator = Indicator(vpn, nursery)

        daemon = Daemon(indicator, vpn, privileged)

        nursery.start_soon(vpn.start)
        nursery.start_soon(daemon.start)


def main():
    logging.basicConfig(level=logging.DEBUG)

    logging.info("Starting main process now")
    trio_gtk.run(async_main)
    logging.info("Exiting")


if __name__ == "__main__":
    main()
