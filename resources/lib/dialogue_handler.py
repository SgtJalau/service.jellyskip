import xbmc

from threading import Thread, Event, Condition
from utils import get_player_speed, calc_wait_time, log, log_exception
from skip_dialogue import SkipDialog
from jellyfin.media_segments import MediaSegmentResponse

class DialogueHandler:

    def __init__(self):
        self.media_segments = None
        self.shown_segments = set()

        self.dialog = SkipDialog() # must create on main thread

        self.event_exit = Event()
        self.event_force_sleep = Event()
        self.event_recalculate = Event()
        self.cond = Condition()

        self.thread_loop = Thread(target=self._loop_thread, name="DialogueHandler_loop", daemon=True)
        self.thread_loop.start()

    def __del__(self):
        self.stop_loop_thread_request()
        del self.dialog

    def stop_loop_thread_request(self):
        if self.event_exit.is_set():
            return
        self._set_event(self.event_exit)
        log('Stopping DialogueHandler')

    def set_media_segments(self, media_segments: MediaSegmentResponse):
        ### XXX: Lock?
        if media_segments and self.media_segments:
            log("Media segments already assigned (should not happen)")
            return

        self.media_segments = media_segments
        self.shown_segments = set()

    def close_dialog(self):
        ### XXX: Lock?
        self.dialog.close()

    def trigger_recalculate(self):
        self._set_event(self.event_recalculate)

    def trigger_force_sleep(self):
        self._set_event(self.event_force_sleep)

    def _set_event(self, event):
        event.set()
        with self.cond:
            self.cond.notify()

    def _get_req_info_for_segment(self):
        if not self.media_segments:
            return None, None

        curr_speed = get_player_speed()
        if not curr_speed or curr_speed < 1:
            return None, None

        try:
            current_time_seconds = xbmc.Player().getTime()
        except RuntimeError:
            log_exception()
            return None, None

        return current_time_seconds, curr_speed

    def _find_suitable_item(self, current_time_seconds):
        if current_time_seconds is None:
            return None

        item = self.media_segments.get_next_item(current_time_seconds)
        if not item:
            return None

        while item.segment_id in self.shown_segments:
            item = self.media_segments.get_next_item(item.get_end_seconds())
            if not item:
                return None

        return item

    def _determine_wait_time(self, item=None, end_time=False):
        current_time_seconds, curr_speed = self._get_req_info_for_segment()
        if item is None:
            item = self._find_suitable_item(current_time_seconds)
        log(f"({current_time_seconds} {curr_speed} {end_time}) Wait time determined from {item}",)
        if item is None:
            return None
        return calc_wait_time(item.get_start_seconds() if not end_time else item.get_end_seconds(), current_time_seconds, curr_speed)

    def _run_dialog_thread(self):
        log(f"Showing skip dialog")
        self.dialog.doModal()
        log(f"Closing skip dialog")

    def _loop_thread(self):
        log("Live from DialogueHandler's loop thread")

        thread_dialog_display = None
        next_timeout = None
        force_recalc = False
        with self.cond:
            while True:
                log(f'Waiting on `cond` (timeout: {next_timeout})')
                notified = self.cond.wait(next_timeout)
                log(
                    f"notified: {notified} force_recalc: {force_recalc} thread_dialog_display: {thread_dialog_display != None} "
                    f"event_exit.is_set: {self.event_exit.is_set()} event_recalculate.is_set: {self.event_recalculate.is_set()} "
                    f"event_force_sleep.is_set: {self.event_force_sleep.is_set()}"
                )

                if notified:
                    if self.event_force_sleep.is_set():
                        self.cond.wait(None)
                        self.event_force_sleep.clear()

                if thread_dialog_display is not None:
                    self.close_dialog()
                    if thread_dialog_display.is_alive():
                        thread_dialog_display.join(0.1)
                    thread_dialog_display = None

                if self.event_exit.is_set():
                    log('Stopping DialogueHandler loop thread')
                    break

                if force_recalc or self.event_recalculate.is_set():
                    force_recalc = False
                    next_timeout = self._determine_wait_time() if self.media_segments else None
                    log(f"Recalculated, next timeout: {next_timeout}")
                    self.event_recalculate.clear()
                    continue

                if notified:
                    continue

                info = self._get_req_info_for_segment()
                log(f"Current playback info : time={info[0]}, speed={info[1]}")
                if item := self._find_suitable_item(info[0]):
                    log(f"Will show skip dialog for {item}")
                    self.shown_segments.add(item.segment_id)
                    self.dialog.setItem(item)
                    thread_dialog_display = Thread(target=self._run_dialog_thread, name="DialogueHandler_display", daemon=True)
                    thread_dialog_display.start()
                    next_timeout = self._determine_wait_time(item=item, end_time=True)
                    force_recalc = True
                    log(f"Closing dialog automatically in {next_timeout}")
                    continue

                next_timeout = None
                log(f"No segment found to display dialog for, sleeping until signalled")
