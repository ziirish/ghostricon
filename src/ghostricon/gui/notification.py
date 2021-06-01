import gi

from ghostricon import constants
from ghostricon.config import get_config

gi.require_version('Notify', '0.7')
gi.require_version('GdkPixbuf', '2.0')

# pylint: disable=E402
from gi.repository import Notify         # noqa: E402
from gi.repository import GdkPixbuf      # noqa: E402
# pylint: enable=E402

Notify.init(constants.APPNAME)


class Notification:
    _cache: Notify.Notification
    _cache = None

    @classmethod
    def display(cls, *args):
        if not get_config().getboolean("Global", "notifications"):
            return
        if cls._cache:
            cls._cache.update(*args)
            cls._cache.show()
            return
        cls._cache = Notify.Notification.new(*args)
        image = GdkPixbuf.Pixbuf.new_from_file(constants.ICON)
        cls._cache.set_icon_from_pixbuf(image)
        cls._cache.set_image_from_pixbuf(image)
        cls._cache.show()
