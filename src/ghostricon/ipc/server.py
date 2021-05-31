import os
import sys
import pwd
import grp
import asyncio
import logging
import typing

from multiprocessing import Process, Queue


def drop_privileges(uid_name='nobody'):
    if os.getuid() != 0:
        # We're not root so, like, whatever dude
        return

    # Get the uid/gid from the name
    running_uid = pwd.getpwnam(uid_name).pw_uid
    running_gid = grp.getgrnam(uid_name).gr_gid

    # Remove group privileges
    os.setgroups([])

    # Try setting the new uid/gid
    os.setgid(running_gid)
    os.setuid(running_uid)


class Server:
    def __init__(self, socket_path: str):
        self.path = socket_path
        self.running = False
        self.logger = logging.getLogger("IPCSERVER")

    async def run(self):
        server = await asyncio.start_unix_server(self.handler, self.path)
        async with server:
            await server.serve_forever()

    def parent(self, reader: Queue, writer: Queue):
        self.from_child = reader
        self.to_child = writer

        if hasattr(self, "user"):
            drop_privileges(self.user)

        logging.debug(f"Serving on {self.path}")
        try:
            asyncio.run(self.run())
        except KeyboardInterrupt:
            self.logger.warn("Received KeyboardInterrupt")

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

    async def handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        pass
