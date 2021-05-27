import trio
import logging

import config
from gui import Indicator
from privileged import Launcher
from bridge import Proxy


class Daemon:
    def __init__(self, indicator: Indicator, vpn: Proxy, privileged: Launcher):
        self.indicator = indicator
        self.vpn = vpn
        self.privileged = privileged
        self.started = False

    async def start(self):
        try:
            self.started = True
            """
            while not self.vpn.ready:
                await trio.sleep(2)
            """
            self.indicator.set_icon(await self.vpn.send("connected"))
            while self.indicator.running:
                logging.debug("DAEMON: checking vpn status")
                ret = await self.vpn.send("changed")
                logging.debug(f"DAEMON: status changed: {ret}")
                if ret:
                    self.indicator.toggle(None)
                await trio.sleep(2)
        except KeyboardInterrupt:
            logging.warn("DAEMON: received KeyboardInterrupt")
        finally:
            await self.stop()

    async def stop(self):
        if not self.started:
            return
        logging.debug("DAEMON: exiting... now stopping proxy")
        await self.vpn.stop()
        logging.debug("DAEMON: proxy stopped... stopping privileged")
        self.privileged.stop()
        logging.debug("DAEMON: privileged done")
        self.started = False

