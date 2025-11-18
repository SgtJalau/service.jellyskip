import xbmc, xbmcaddon

from helper import LazyLogger
import player
import helper.utils as utils

from jellyfin.jellyfin_grabber import JellyfinHack
from skip_dialogue import SkipSegmentDialogue
from dialogue_handler import dialogue_handler

addonInfo = xbmcaddon.Addon().getAddonInfo
addonPath = utils.translate_path(addonInfo('path'))

jf_hack = JellyfinHack()

LOG = LazyLogger(__name__)


class JellySkipMonitor(xbmc.Monitor):


    def __init__(self):
        xbmc.Monitor.__init__(self)
        self.player = player.JellySkipPlayer(self)
        LOG.info('Init monitor')

    def start(self, **kwargs):
        LOG.info('Starting JellySkipMonitor')
        while not self.abortRequested():
            self.waitForAbort(1)

        self.stop()

    def _event_handler_player_change_playback(self, **_kwargs):
        LOG.info('JellySkipMonitor: player general event')
        self.start_tracking()

    def _event_handler_player_stop(self, **_kwargs):
        LOG.info('JellySkipMonitor: player stop event')
        jf_hack.reset_itemid()
        dialogue_handler.cancel_scheduled()
        LOG.info('JellySkipMonitor: reset itemid')

    def _event_handler_player_start(self, **_kwargs):
        LOG.info('JellySkipMonitor: player start event')
        jf_hack.reset_itemid()
        dialogue_handler.cancel_scheduled()

    def _event_handler_jellyskip_dialogue_closed(self, **_kwargs):
        LOG.info('JellySkipMonitor: player dialogue closed event')
        # User closed dialogue, now we want to start tracking only the next upcoming segment
        self.start_tracking(only_upcoming=True)

    EVENTS_MAP = {
        'Other.UserDataChanged': jf_hack.event_handler_jellyfin_userdatachanged,
        'Other.Jellyskip.DialogueClosed': _event_handler_jellyskip_dialogue_closed,
        # 'Player.OnPause': _event_handler_player_change_playback,
        'Player.OnResume': _event_handler_player_change_playback,
        # 'Player.OnSpeedChanged': _event_handler_player_change_playback,
        'Player.OnSeek': _event_handler_player_change_playback,
        'Player.OnStop': _event_handler_player_stop,
        'Player.OnPlay': _event_handler_player_start,
        'Player.OnAVChange': _event_handler_player_change_playback,
    }

    def stop(self):
        LOG.info('Stopping JellySkipMonitor')

    def onNotification(self, sender, method, data=None):
        """Handler for Kodi events and data transfer from plugins"""

        sender = utils.from_bytes(sender)
        method = utils.from_bytes(method)
        data = utils.from_bytes(data) if data else ''
        handler = JellySkipMonitor.EVENTS_MAP.get(method)
        if not handler:
            return

        LOG.info(f"Notification: sender={sender}, method={method}, data={data}")

        handler(self, sender=sender, data=data)

        if method == 'Other.UserDataChanged':
            while not jf_hack.has_itemid():
                self.waitForAbort(1)

            LOG.info('JellySkipMonitor: getting media segments')

            if not self.player.isPlayingVideo() or not jf_hack.has_itemid():
                return

            jf_hack._fetch_media_segments()
            self.start_tracking()

    def start_tracking(self, only_upcoming=False):
        if not self.player.isPlayingVideo():
            LOG.info('Not playing video')
            return

        time_seconds = self.player.getTime()
        duration_seconds = self.player.getTotalTime()

        media_segments = jf_hack.get_media_segments()

        # No media segments
        if not media_segments:
            LOG.info('No media segments')
            # Close any open dialogues, if any
            dialogue_handler.close_gui()
            return

        LOG.info(f"Start tracking: time={time_seconds}, duration={duration_seconds}")

        next_item = media_segments.get_next_item(time_seconds, only_upcoming)

        if not next_item:
            # Close any open dialogues, if any
            dialogue_handler.close_gui()
            LOG.info('Stopping all dialogue, because no next item')
            return

        LOG.info(f"Next item: {next_item}")

        dialogue_handler.schedule_skip_gui(next_item, time_seconds, jf_hack)


