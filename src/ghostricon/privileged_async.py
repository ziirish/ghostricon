import logging
import asyncio
import json

from multiprocessing import Queue

from ghostricon.config import get_config
from ghostricon.gui import Notification
from ghostricon.ipc.server import Server
from ghostricon.ipc.utils import to_str, to_bytes
from ghostricon.vpn import Vpn


class Privileged(Server):
    def __init__(self, socket_path: str, user: str):
        super(Privileged, self).__init__(socket_path)
        self.user = user
        self.vpn = Vpn(user)
        self.config = get_config(user)["Global"]
        self.logger = logging.getLogger("PRIVILEGED")

    async def handler(self,
                      reader: asyncio.StreamReader,
                      writer: asyncio.StreamWriter):
        while self.running:
            line = await reader.readline()
            self.logger.debug(f"PARENT: received {line}")
            if not line or line == b"QUIT\n":
                self.to_child.put("QUIT\n")
                break
            self.to_child.put(to_str(line))
            self.logger.debug("PARENT: forwarding to child")
            ret = self.from_child.get()
            writer.write(to_bytes(ret + "\n"))
            await writer.drain()
        self.logger.info("PARENT: Stopping")
        self.stop()

    def child(self, reader: Queue, writer: Queue):
        try:
            while self.running:
                self.logger.debug("CHILD: waiting command")
                line = reader.get()
                if line.startswith("QUIT"):
                    self.logger.debug("CHILD: Stopping")
                    break
                data = json.loads(line)
                self.logger.debug(f"CHILD: running command {data}")
                method = data["method"]
                args = data.get("args", [])
                kwargs = data.get("kwargs", {})
                callback = getattr(self.vpn, method)
                ret = callback(*args, **kwargs)
                writer.put(json.dumps(ret))
        except KeyboardInterrupt:
            self.logger.warn("CHILD: received KeyboardInterrupt")
            if self.config.getboolean("disconnect_on_exit"):
                self.vpn.disconnect()
