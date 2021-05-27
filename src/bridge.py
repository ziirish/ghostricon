import trio
import json
import typing
import logging

from ipc.client import Client
from ipc.utils import to_str, to_bytes


class Proxy(Client):
    def __init__(self, socket_path: str):
        super(Proxy, self).__init__(socket_path)
        self.command_in, self.command_out = trio.open_memory_channel(1)
        self.return_in, self.return_out = trio.open_memory_channel(1)

    async def stop(self):
        if not self.running:
            return
        logging.debug("stopping proxy")
        try:
            await self.command_in.send("QUIT")
            await trio.sleep(3)
        except trio.EndOfChannel:
            pass
        logging.debug("proxy stopped")
        self.running = False

    async def handler(self, socket: trio.SocketStream):
        async with socket:
            async with trio.open_nursery() as nursery:
                nursery.start_soon(self.sender, socket)
                nursery.start_soon(self.receiver, socket)

    async def sender(self, socket: trio.SocketStream):
        logging.debug("sender: started")
        while self.running:
            command = await self.command_out.receive()
            logging.debug(f"sender: forwarding command {command}")
            await socket.send_all(to_bytes(command + "\n"))
            logging.debug("sender: command forwarded")
            if command == "QUIT":
                logging.debug("sender: exiting")
                break
        await self.command_out.aclose()

    async def receiver(self, socket: trio.SocketStream):
        logging.debug("receiver: started")
        async for data in socket:
            await self.return_in.send(to_str(data))
        await self.return_in.aclose()

    async def send(self,
                   method: str,
                   *args,
                   callback: typing.Callable = None,
                   **kwargs):
        if not self.running:
            return
        command = {
            "method": method,
            "args": args,
            "kwargs": kwargs,
        }
        try:
            await self.command_in.send(json.dumps(command))
            ret = json.loads(await self.return_out.receive())
            if callback:
                callback(ret)
            return ret
        except trio.EndOfChannel:
            pass
