import os

VERSION = "0.0.1-dev"
APPNAME = "GhostRicon"
ROOTDIR = os.path.abspath(os.path.dirname(__file__))
ICONDIR = os.path.normpath(os.path.join(ROOTDIR, '../../data/icons/'))
ICON_ACTIVED = os.path.join(ICONDIR, 'ghost-active.svg')
ICON_PAUSED = os.path.join(ICONDIR, 'ghost-paused.svg')
ICON = os.path.join(ICONDIR, 'ghost.svg')
SOCKET = f"/tmp/{APPNAME.lower()}.sock"
CG_BASE_URL = "https://payment.cyberghostvpn.com/cg/"
