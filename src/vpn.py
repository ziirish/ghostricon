import os
import re
import typing
import logging
import subprocess

from commands import server_types


class Vpn:
    logger = logging.getLogger("VPNTOOL")

    def __init__(self, user: str):
        self.user = user
        self.connected()

    def _run(self, args: typing.List[str]) -> str:
        self.logger.debug("running as " +
                          f"{subprocess.check_output(['/usr/bin/whoami'])}")
        self.logger.debug(f"substitute as {self.user}")
        return "No VPN connections found."
        env = os.environ
        env["USER"] = self.user
        cmd = ["/usr/bin/cyberghostvpn"]
        cmd += args
        self.logger.debug(f"COMMAND: {cmd}")
        ret = subprocess.check_output(cmd, env=env).decode("utf-8").rstrip()
        self.logger.debug(f"RET: {ret}")
        return ret

    def list(self, kind: str = None, *args) -> typing.List[str]:
        fargs = ["--country-code"]
        if kind and kind in server_types:
            fargs.insert(0, server_types[kind])
            fargs += args
        # ret = self._run(fargs)
        ret = \
            """\
+-----+----------------------+--------------+
| No. |     Country Name     | Country Code |
+-----+----------------------+--------------+
|  1  |       Andorra        |      AD      |
|  2  | United Arab Emirates |      AE      |
|  3  |       Albania        |      AL      |
|  4  |       Armenia        |      AM      |
|  5  |      Argentina       |      AR      |
|  6  |       Austria        |      AT      |
|  7  |      Australia       |      AU      |
|  8  | Bosnia & Herzegovina |      BA      |
|  9  |      Bangladesh      |      BD      |
|  10 |       Belgium        |      BE      |
|  11 |       Bulgaria       |      BG      |
|  12 |        Brazil        |      BR      |
|  13 |       Bahamas        |      BS      |
|  14 |       Belarus        |      BY      |
|  15 |        Canada        |      CA      |
|  16 |     Switzerland      |      CH      |
|  17 |        Chile         |      CL      |
|  18 |        China         |      CN      |
|  19 |       Colombia       |      CO      |
|  20 |      Costa Rica      |      CR      |
|  21 |        Cyprus        |      CY      |
|  22 |       Czechia        |      CZ      |
|  23 |       Germany        |      DE      |
|  24 |       Denmark        |      DK      |
|  25 |       Algeria        |      DZ      |
|  26 |       Estonia        |      EE      |
|  27 |        Egypt         |      EG      |
|  28 |        Spain         |      ES      |
|  29 |       Finland        |      FI      |
|  30 |        France        |      FR      |
|  31 |    United Kingdom    |      GB      |
|  32 |       Georgia        |      GE      |
|  33 |      Greenland       |      GL      |
|  34 |        Greece        |      GR      |
|  35 |      Hong Kong       |      HK      |
|  36 |       Croatia        |      HR      |
|  37 |       Hungary        |      HU      |
|  38 |      Indonesia       |      ID      |
|  39 |       Ireland        |      IE      |
|  40 |        Israel        |      IL      |
|  41 |     Isle of Man      |      IM      |
|  42 |        India         |      IN      |
|  43 |         Iran         |      IR      |
|  44 |       Iceland        |      IS      |
|  45 |        Italy         |      IT      |
|  46 |        Japan         |      JP      |
|  47 |        Kenya         |      KE      |
|  48 |       Cambodia       |      KH      |
|  49 |     South Korea      |      KR      |
|  50 |      Kazakhstan      |      KZ      |
|  51 |    Liechtenstein     |      LI      |
|  52 |      Sri Lanka       |      LK      |
|  53 |      Lithuania       |      LT      |
|  54 |      Luxembourg      |      LU      |
|  55 |        Latvia        |      LV      |
|  56 |       Morocco        |      MA      |
|  57 |        Monaco        |      MC      |
|  58 |       Moldova        |      MD      |
|  59 |      Montenegro      |      ME      |
|  60 |      Macedonia       |      MK      |
|  61 |       Mongolia       |      MN      |
|  62 |   Macau SAR China    |      MO      |
|  63 |        Malta         |      MT      |
|  64 |        Mexico        |      MX      |
|  65 |       Malaysia       |      MY      |
|  66 |       Nigeria        |      NG      |
|  67 |     Netherlands      |      NL      |
|  68 |        Norway        |      NO      |
|  69 |     New Zealand      |      NZ      |
|  70 |        Panama        |      PA      |
|  71 |     Philippines      |      PH      |
|  72 |       Pakistan       |      PK      |
|  73 |        Poland        |      PL      |
|  74 |       Portugal       |      PT      |
|  75 |        Qatar         |      QA      |
|  76 |       Romania        |      RO      |
|  77 |        Serbia        |      RS      |
|  78 |        Russia        |      RU      |
|  79 |     Saudi Arabia     |      SA      |
|  80 |        Sweden        |      SE      |
|  81 |      Singapore       |      SG      |
|  82 |       Slovenia       |      SI      |
|  83 |       Slovakia       |      SK      |
|  84 |       Thailand       |      TH      |
|  85 |        Turkey        |      TR      |
|  86 |        Taiwan        |      TW      |
|  87 |       Ukraine        |      UA      |
|  88 |    United States     |      US      |
|  89 |      Venezuela       |      VE      |
|  90 |       Vietnam        |      VN      |
|  91 |     South Africa     |      ZA      |
+-----+----------------------+--------------+
"""
        reg = re.compile(r"^\|\s*\d+\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|$")
        servers = []
        for line in ret.splitlines():
            match = reg.match(line)
            if match:
                servers.append((match.group(1), match.group(2)))
        import time
        time.sleep(3)
        return servers

    def status(self) -> bool:
        ret = self._run(["--status"])
        return ret != "No VPN connections found."

    def disconnect(self):
        self._run(["--stop"])
        self._connected = False

    def connect(self):
        self._run(["--country-code", "ie",  "--connect"])
        self._connected = True

    def connected(self) -> bool:
        self._connected = self.status()
        self.logger.debug(f"CONNECTED: {self._connected}")
        return self._connected

    def changed(self) -> bool:
        if self.status() != self._connected:
            self._connected = not self._connected
            return True
        return False
