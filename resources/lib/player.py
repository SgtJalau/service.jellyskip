import xbmc
from threading import Timer
from dialogue_handler import DialogueHandler
from utils import log
from jellyfin.media_segments import MediaSegmentResponse

class JellySkipPlayer(xbmc.Player):

    def __init__(self):
        super().__init__()
        self.dialogue_handler = DialogueHandler()
        self.recalculate_debounce_timer = None

    def __del__(self):
        self.terminate()
        del self.dialogue_handler

    def terminate(self):
        self._delay_recalculate_cancel()
        self.dialogue_handler.stop_loop_thread_request()

    def _delay_recalculate(self):
        self._delay_recalculate_cancel()
        self.recalculate_debounce_timer = Timer(0.2, self._debounce_recalculate_cb)
        self.recalculate_debounce_timer.daemon = True
        self.recalculate_debounce_timer.start()

    def _delay_recalculate_cancel(self):
        if self.recalculate_debounce_timer:
            self.recalculate_debounce_timer.cancel()
            self.recalculate_debounce_timer = None

    def _debounce_recalculate_cb(self):
        log(f'Recalculate debounced')
        self.dialogue_handler.trigger_recalculate()

    def _event_handler_player_stop(self):
        self.dialogue_handler.set_media_segments(None)
        self._delay_recalculate_cancel()
        self.dialogue_handler.trigger_recalculate()
        log('Reset itemid')

    def onPlayBackPaused(self):
        self.dialogue_handler.trigger_force_sleep()
        log(f'onPlayBackPaused')

    def onPlayBackResumed(self):
        log(f'onPlayBackResumed')
        self._delay_recalculate()

    def onPlayBackSpeedChanged(self, speed):
        log(f'onPlayBackSpeedChanged {speed}')
        #log(f'Player.Playing:{xbmc.getCondVisibility("Player.Playing")} Player.Forwarding:{xbmc.getCondVisibility("Player.Forwarding")} Player.Rewinding:{xbmc.getCondVisibility("Player.Rewinding")}')
        #log(f'Player.DisplayAfterSeek:{xbmc.getCondVisibility("Player.DisplayAfterSeek")} Player.Seeking:{xbmc.getCondVisibility("Player.Seeking")} Player.FrameAdvance:{xbmc.getCondVisibility("Player.FrameAdvance")}')

        if xbmc.getCondVisibility("!Player.Playing"): # assume player is Player.Rewinding or Player.Forwarding
            self.dialogue_handler.trigger_force_sleep()
            self.dialogue_handler.close_dialog()
        else:
            self._delay_recalculate()

    def onPlayBackSeek(self, time, seekOffset):
        log(f'onPlayBackSeek {time} {seekOffset}')
        self._delay_recalculate()

    def onPlayBackStopped(self):
        log('onPlayBackStopped')
        self._event_handler_player_stop()

    def onPlayBackEnded(self):
        log('onPlayBackEnded')
        self._event_handler_player_stop()

    def onPlayBackError(self):
        log('onPlayBackError')
        self._event_handler_player_stop()

    def start_tracking(self, media_segments: MediaSegmentResponse):
        if media_segments:
            self.dialogue_handler.set_media_segments(media_segments)
        self.dialogue_handler.trigger_recalculate()

        log(f"Start tracking: time={self.getTime()}, duration={self.getTotalTime()}")

