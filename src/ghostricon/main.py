#!/usr/bin/env python3
import os
import trio
import logging
import argparse
from getpass import getuser
from functools import partial

from ghostricon import constants
from ghostricon.api import CyberghostAPI
from ghostricon.config import get_config, get_cg_config, save_config
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

USER = getuser()
DEFAULT_INTERVAL = 5


async def async_main(user, interval, level):
    socket = constants.SOCKET
    if os.path.exists(socket):
        os.unlink(socket)

    logging.debug(f"Starting with user: {user} on {socket}")

    privileged = Launcher(socket, user, level)
    privileged.start()

    vpn = Proxy(socket)

    get_config(user)
    get_cg_config(user)
    try:
        nursery: trio.Nursery
        async with trio.open_nursery() as nursery:
            indicator = Indicator(vpn, nursery)

            daemon = Daemon(indicator, vpn, privileged, interval)

            nursery.start_soon(vpn.start)
            nursery.start_soon(daemon.start)
    except KeyboardInterrupt:
        logging.warn("Received KeyboardInterrupt")
    finally:
        save_config(user)


def main():
    parser = argparse.ArgumentParser("GhostRicon")
    parser.add_argument(
        "-u",
        "--user",
        default=USER,
        help=f"User that have a valid cyberghost configuration (default: {USER})"
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase log level (repeat for even more logs)"
    )
    parser.add_argument(
        "-i",
        "--interval",
        type=int,
        default=DEFAULT_INTERVAL,
        help="Interval to check for VPN connection (default: {DEFAULT_INTERVAL}s)"
    )
    args = parser.parse_args()
    level = logging.WARNING
    level -= min(args.verbose * 10, 20)

    logging.basicConfig(level=level)

    real_main = partial(async_main, args.user, args.interval, level)

    logging.info("Starting main process now")
    trio_gtk.run(real_main)
    logging.info("Exiting")


if __name__ == "__main__":
    main()
