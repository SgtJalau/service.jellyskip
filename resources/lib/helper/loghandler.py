# -*- coding: utf-8 -*-
from __future__ import division, absolute_import, print_function, unicode_literals

##################################################################################################

import os
import logging
import traceback

import xbmc
import xbmcaddon
from . import settings, kodi_version
from . import utils

##################################################################################################

__addon__ = xbmcaddon.Addon(id=utils.addon_id())
__pluginpath__ = utils.translate_path(__addon__.getAddonInfo("path"))


##################################################################################################


def getLogger(name=None):
    if name is None:
        return __LOGGER

    return __LOGGER.getChild(name)

class LogHandler(logging.StreamHandler):

    def __init__(self):

        logging.StreamHandler.__init__(self)
        self.setFormatter(MyFormatter())

        if kodi_version() > 18:
            self.level = xbmc.LOGINFO
        else:
            self.level = xbmc.LOGNOTICE

    def emit(self, record):

        if self._get_log_level(record.levelno):
            string = self.format(record)

            xbmc.log(string, level=self.level)

    @classmethod
    def _get_log_level(cls, level):

        levels = {
            logging.ERROR: 0,
            logging.WARNING: 0,
            logging.INFO: 1,
            logging.DEBUG: 2,
        }
        try:
            # log_level = int(settings("logLevel"))
            log_level = 2
        except ValueError:
            log_level = 2  # If getting settings fail, we probably want debug logging.

        return log_level >= levels[level]

class MyFormatter(logging.Formatter):

    def __init__(
        self, fmt="%(name)s -> %(levelname)s::%(relpath)s:%(lineno)s %(message)s"
    ):
        logging.Formatter.__init__(self, fmt)

    def format(self, record):
        self._gen_rel_path(record)

        # Call the original formatter class to do the grunt work
        result = logging.Formatter.format(self, record)

        return result

    def formatException(self, exc_info):
        _pluginpath_real = os.path.realpath(__pluginpath__)
        res = []

        for o in traceback.format_exception(*exc_info):
            if o.startswith('  File "'):
                # If this split can't handle your file names, you should seriously consider renaming your files.
                fn = o.split('  File "', 2)[1].split('", line ', 1)[0]
                rfn = os.path.realpath(fn)
                if rfn.startswith(_pluginpath_real):
                    o = o.replace(fn, os.path.relpath(rfn, _pluginpath_real))

            res.append(o)

        return "".join(res)

    def _gen_rel_path(self, record):
        if record.pathname:
            record.relpath = os.path.relpath(record.pathname, __pluginpath__)


__LOGGER = logging.getLogger("JELLYSKIP")
for handler in __LOGGER.handlers:
    __LOGGER.removeHandler(handler)

__LOGGER.addHandler(LogHandler())
__LOGGER.setLevel(logging.DEBUG)
