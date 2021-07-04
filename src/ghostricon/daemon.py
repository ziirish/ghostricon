import trio
import logging

from ghostricon.gui import Indicator, Notification
from ghostricon.config import get_config
from ghostricon.privileged import Launcher
from ghostricon.bridge import Proxy


class Daemon:
    def __init__(self,
                 indicator: Indicator,
                 vpn: Proxy,
                 privileged: Launcher,
                 interval: int = 5):
        self.indicator = indicator
        self.vpn = vpn
        self.privileged = privileged
        self.interval = interval
        self.config = get_config()["Global"]
        self.started = False

    async def start(self):
        try:
            self.started = True
            if self.config.getboolean("connect_on_startup"):
                status = await self.vpn.send("connect")
                if status:
                    Notification.display("Successfully connected")
                else:
                    Notification.display("Failed to connect!")
            else:
                status = await self.vpn.send("connected")
            self.indicator.set_icon(status)
            while self.indicator.running:
                logging.debug("DAEMON: checking vpn status")
                ret = await self.vpn.send("changed")
                logging.debug(f"DAEMON: status changed: {ret}")
                if ret:
                    self.indicator.toggle(None)
                await trio.sleep(self.interval)
        except KeyboardInterrupt:
            logging.warn("DAEMON: received KeyboardInterrupt")
        finally:
            await self.stop()

    async def stop(self):
        if not self.started:
            return
        if self.config.getboolean("disconnect_on_exit"):
            logging.debug("DAEMON: disconnect VPN")
            status = await self.vpn.send("disconnect")
            if not status:
                Notification.display("Successfully disconnected")
            else:
                Notification.display("Failed to disconnect!")
        logging.debug("DAEMON: exiting... now stopping proxy")
        await self.vpn.stop()
        logging.debug("DAEMON: proxy stopped... stopping privileged")
        self.privileged.stop()
        logging.debug("DAEMON: privileged done")
        self.started = False

