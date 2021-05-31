import os
import trio
import logging


class Client:
    def __init__(self, socket_path: str):
        self.path = socket_path
        self.running = False
        self.ready = False
        self.socket = None

    async def start(self):
        try:
            self.running = True
            await self.bridge()
        except KeyboardInterrupt:
            logging.warn("IPC:Client received KeyboardInterrupt")
        finally:
            await self.stop()

    async def stop(self):
        self.running = False

    async def connect(self) -> trio.SocketStream:
        logging.debug(f"IPC:Client Connecting to {self.path}")
        while not os.path.exists(self.path):
            logging.debug("IPC:Client Waiting for server to start")
            await trio.sleep(2)
        ret = await trio.open_unix_socket(self.path)
        self.ready = True
        return ret

    async def bridge(self):
        self.socket = await self.connect()
        await self.handler(self.socket)

    async def handler(self, socket: trio.SocketStream):
        pass
