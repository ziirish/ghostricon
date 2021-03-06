import os
from configparser import ConfigParser
from pathlib import Path

_config = None
_cg_config = None

_defaults = {
    "connect_on_startup": "false",
    "notifications": "true",
    "default_type": "traffic",
    "default_country": "ie",
    "disconnect_on_exit": "false",
}


def _get_home(user: str = None) -> Path:
    if user:
        return Path(os.path.expanduser(f"~{user}"))
    return Path(os.path.expandvars("$HOME"))


def get_config_dir(user: str = None) -> Path:
    return _get_home(user) / ".config/ghostricon"


def get_cg_config_dir(user: str = None) -> Path:
    return _get_home(user) / ".cyberghost"


def get_config_path(user: str = None) -> Path:
    return get_config_dir(user) / "config.ini"


def get_cg_config_path(user: str = None) -> Path:
    return get_cg_config_dir(user) / "config.ini"


def get_cg_config(user: str = None) -> ConfigParser:
    global _cg_config
    if _cg_config:
        return _cg_config
    _cg_config = ConfigParser()
    _cg_config.read(get_cg_config_path(user))
    return _cg_config


def get_config(user: str = None, force: bool = False) -> ConfigParser:
    global _config
    if _config and not force:
        return _config
    _config = ConfigParser()
    _config.read(get_config_path(user))
    _config["DEFAULT"] = _defaults
    if "Global" not in _config:
        _config.add_section("Global")
    if "Favorite" not in _config:
        _config.add_section("Favorite")
        _config["Favorite"]["traffic"] = ""
        _config["Favorite"]["streaming"] = ""
        _config["Favorite"]["torrent"] = ""
    return _config


def reload_config(user: str = None):
    return get_config(user, True)


def save_config(user: str = None):
    if not _config:
        return
    config_dir = get_config_dir(user)
    if not config_dir.exists():
        config_dir.mkdir()
    # _config.default_section = "Global"
    # del _config["DEFAULT"]
    tmp_config = ConfigParser()
    for section, data in _config.items():
        if section == "DEFAULT":
            continue
        tmp_config[section] = data
    with open(get_config_path(user), "w") as fh:
        tmp_config.write(fh)
