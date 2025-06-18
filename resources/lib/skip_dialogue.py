import xbmcgui, xbmc
from xbmcgui import ACTION_NAV_BACK, ACTION_PREVIOUS_MENU, ACTION_STOP

import helper.utils as utils
from helper import LazyLogger

OK_BUTTON = 2101

INSTRUCTION_LABEL = 203
AUTHCODE_LABEL = 204
WARNING_LABEL = 205
CENTER_Y = 6
CENTER_X = 2

MIN_REMAINING_SECONDS = 5
LOG = LazyLogger(__name__)

class SkipSegmentDialogue(xbmcgui.WindowXMLDialog):

    def __init__(self, xmlFile, resourcePath, seek_time_seconds, segment_type):
        self.seek_time_seconds = seek_time_seconds
        self.segment_type = segment_type
        self.player = xbmc.Player()

    def onInit(self):
        skip_label = 'Skip ' + str(self.segment_type)
        skip_button = self.getControl(OK_BUTTON)
        skip_button.setLabel(skip_label)
        self.schedule_close_action()

    def get_seconds_till_segment_end(self):
        return self.seek_time_seconds - self.player.getTime()

    def schedule_close_action(self):
        """
        Schedule the dialog to close automatically when the segment ends.
        :return: None
        """

        seconds_till_segment_end = self.get_seconds_till_segment_end()

        if seconds_till_segment_end > 0:
            utils.run_threaded(self.on_automatic_close, delay=seconds_till_segment_end, kwargs={})

    def on_automatic_close(self):
        """
        Close the dialog automatically. This is called by the scheduled thread.
        :return: None
        """

        self.close()

        LOG.info("JellySkip: Auto closing dialogue")
        sender = "service.jellyskip"
        xbmc.executebuiltin("NotifyAll(%s, %s, %s)" % (sender, "Jellyskip.DialogueClosed", {}))

    def onAction(self, action):
        if action in (ACTION_NAV_BACK, ACTION_PREVIOUS_MENU, ACTION_STOP):
            self.close()

    def onControl(self, control):
        pass

    def onFocus(self, control):
        pass

    def onClick(self, control):
        if not self.player.isPlaying():
            self.close()
            return

        if control == OK_BUTTON:
            remaining_seconds = self.player.getTotalTime() - self.seek_time_seconds

            # We don't want to skip to the end of the video (give other addons time to play, like nextup service)
            if remaining_seconds < MIN_REMAINING_SECONDS:
                self.player.seekTime(self.player.getTotalTime() - MIN_REMAINING_SECONDS)
                self.close()
            else:
                self.player.seekTime(self.seek_time_seconds)

        self.close()
