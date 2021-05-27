import os
import sys
import trio

import config
from gui import Indicator
from daemon import Daemon
from bridge import Proxy
from privileged import Launcher

import gi
gi.require_version('Gtk', '3.0')
# pylint: disable=E402
from gi.repository import Gtk    # noqa: E402

import trio_gtk                  # noqa: E402

# pylint: enable=E402


async def main():
    user = sys.argv[1]
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


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.DEBUG)

    logging.info("Starting main process now")
    trio_gtk.run(main)
    logging.info("Exiting")
