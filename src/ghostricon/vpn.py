import os
import re
import typing
import logging
import subprocess
from shlex import quote

from ghostricon.commands import server_types
from ghostricon.config import get_config


class Vpn:
    logger = logging.getLogger("VPNTOOL")
    reg = re.compile(r"^\|\s*\d+\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|$")

    def __init__(self, user: str):
        self.user = user
        self.config = get_config(user)["Global"]
        self.connected()

    def _run(self, args: typing.List[str]) -> str:
        self.logger.debug("running as " +
                          f"{subprocess.check_output(['/usr/bin/whoami'])}")
        self.logger.debug(f"substitute as {self.user}")
        env = os.environ
        env["USER"] = self.user
        cmd = ["/usr/bin/cyberghostvpn"]
        cmd += args
        cmd = [quote(x) for x in cmd]
        self.logger.debug(f"COMMAND: {cmd}")
        ret = subprocess.check_output(cmd, env=env).decode("utf-8").rstrip()
        self.logger.debug(f"RET: {ret}")
        return ret

    def list(self, kind: str = None, *args) -> typing.List[str]:
        fargs = ["--country-code"]
        if kind and kind in server_types:
            fargs.insert(0, server_types[kind])
            fargs += args
        ret = self._run(fargs)
        servers = []
        for line in ret.splitlines():
            match = self.reg.match(line)
            if match:
                servers.append((match.group(1), match.group(2)))
        return servers

    def status(self) -> bool:
        ret = self._run(["--status"])
        return ret != "No VPN connections found."

    def disconnect(self):
        if not self.connected():
            return False
        self._run(["--stop"])
        return self.connected()

    def connect(self,
                kind: str = None,
                country: str = None,
                platform: str = None) -> bool:
        if self.connected():
            return True
        args = ["--connect"]
        if not kind or kind not in server_types:
            kind = self.config.get("default_type")
            if kind not in server_types:
                kind = "traffic"
        args.append(server_types[kind])
        if kind == "streaming":
            args.append(platform)
        if not country:
            country = self.config.get("default_country")
        args += ["--country-code", country]
        self._run(args)
        return self.connected()

    def connected(self) -> bool:
        self._connected = self.status()
        self.logger.debug(f"CONNECTED: {self._connected}")
        return self._connected

    def changed(self) -> bool:
        if self.status() != self._connected:
            self._connected = not self._connected
            return True
        return False
