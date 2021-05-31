import os
import sys
import subprocess


class Launcher:
    def __init__(self, socket_path: str, user: str):
        self.user = user
        self.socket_path = socket_path
        self.running = False

    def start(self):
        current = os.path.abspath(__file__)
        cmd = [
            "/usr/bin/pkexec",
            sys.executable,
            current,
            self.socket_path,
            self.user
        ]
        self.process = subprocess.Popen(cmd)
        self.running = True

    def stop(self):
        if not self.running:
            return
        self.process.kill()
        self.running = False
        self.process.wait()


def main():
    import logging
    from ghostricon.privileged_async import Privileged
    logging.basicConfig()
    socket = sys.argv[1]
    user = sys.argv[2]
    server = Privileged(socket, user)
    server.start()


if __name__ == "__main__":
    main()
