import os
import sys
import asyncio
import logging
import typing

from multiprocessing import Process, Queue

try:
    from ghostricon.ipc.utils import drop_privileges
except ImportError:
    from utils import drop_privileges


class Server:
    def __init__(self, socket_path: str):
        self.path = socket_path
        self.running = False

    def parent(self, reader: Queue, writer: Queue):
        self.from_child = reader
        self.to_child = writer

        if hasattr(self, "user"):
            drop_privileges(self.user)

        loop = asyncio.get_event_loop()
        coro = asyncio.start_unix_server(self.handler, self.path, loop=loop)
        server = loop.run_until_complete(coro)

        logging.debug(f"Serving on {self.path}")
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            pass

        server.close()
        loop.run_until_complete(server.wait_closed())
        loop.close()

    def child(self, reader: Queue, writer: Queue):
        pass

    def start(self):
        self.running = True
        self.from_child = Queue()
        self.to_child = Queue()

        self.children = Process(target=self.child, args=(self.to_child, self.from_child))
        self.children.start()
        self.parent(self.from_child, self.to_child)
        self.children.join()

    def stop(self):
        self.running = False
        self.children.join()
        print("I'm the SERVER KILLING MYSELF NOW...")

    async def handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        pass
