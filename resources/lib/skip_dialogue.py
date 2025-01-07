import xbmc, xbmcgui, xbmcaddon
from jellyfin.media_segments import MediaSegmentItem

OK_BUTTON = 201

MIN_REMAINING_SECONDS = 5

ADDON_PATH = xbmcaddon.Addon().getAddonInfo('path')

class SkipDialog(xbmcgui.WindowXMLDialog):

    def __new__(cls):
        return super(SkipDialog, cls).__new__(cls, 'script-dialog.xml', ADDON_PATH)

    #def __init__(self, *args, **kwargs):
    #    pass

    def setItem(self, item: MediaSegmentItem):
        self.item = item

    def onInit(self):
        self.getControl(OK_BUTTON).setLabel(f'Skip {self.item.get_segment_type_display()}')

    def onAction(self, action):
        if action == xbmcgui.ACTION_PREVIOUS_MENU or action == xbmcgui.ACTION_NAV_BACK:
            self.close()
            return
        super().onAction(action)

    def onClick(self, control):
        if control == OK_BUTTON:
            player = xbmc.Player()
            if not player.isPlayingVideo():
                self.close()
                return

            duration_seconds = player.getTotalTime()
            end_seconds = self.item.get_end_seconds()
            remaining_seconds = duration_seconds - end_seconds

            # We don't want to skip to the end of the video (give other addons time to play, like nextup service)
            if remaining_seconds < MIN_REMAINING_SECONDS:
                player.seekTime(duration_seconds - MIN_REMAINING_SECONDS)
                self.close()
            else:
                player.seekTime(end_seconds)

            self.close()
