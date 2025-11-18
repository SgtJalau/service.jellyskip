import xbmc, xbmcaddon
import helper.utils as utils

from skip_dialogue import SkipSegmentDialogue
from jellyfin.jellyfin_grabber import JellyfinHack
from helper import LazyLogger

from jellyfin.media_segments import MediaSegmentItem

addonInfo = xbmcaddon.Addon().getAddonInfo
addonPath = utils.translate_path(addonInfo('path'))

LOG = LazyLogger(__name__)

SECOND_PADDING = 1


class DialogueHandler:

    def __init__(self):
        self.dialogue = None
        self.scheduled_thread = None
        self.last_item = None

    def schedule_skip_gui(self, item: MediaSegmentItem, current_seconds, jf_hack=None):
        """
        Schedule the dialogue to open at the start of the upcoming segment.
        If the segment has already started, opens the dialogue immediately.

        :param item: the segment item to schedule
        :param current_seconds: the current playback time in seconds
        :param jf_hack: the JellyfinHack instance with current itemid
        :return: None
        """

        if not item:
            return
            
        # Store jf_hack instance for later use
        self.jf_hack = jf_hack

        # Cancel any existing scheduled thread
        self.cancel_scheduled()

        if self.last_item and not self.is_last_item_segment() and self.dialogue:
            # The last segment item is not currently playing, but our dialogue is still open possibly due to a seek
            LOG.info(f"Closing dialogue for {self.last_item.get_segment_type_display()} at {self.last_item.get_start_seconds()} as it is not currently playing")
            self.dialogue.close()
            self.dialogue = None

        if item.get_end_seconds() < current_seconds:
            # We are past the segment, no need to schedule
            return

        if item.get_start_seconds() < current_seconds:
            self.open_gui(item)
        else:
            seconds_till_start = item.get_start_seconds() - current_seconds
            self.scheduled_thread = utils.run_threaded(self.on_gui_scheduled, delay=seconds_till_start + SECOND_PADDING,
                                                       kwargs={'item': item})
            LOG.info(
                f"Scheduled dialogue for {item.get_segment_type_display()} at {item.get_start_seconds()} in {seconds_till_start} seconds")

    def on_gui_scheduled(self, item: MediaSegmentItem):
        """
        Open the dialogue for the scheduled segment item. This is called by the scheduled thread.
        :param item: the segment item to open the dialogue for
        :return: None
        """

        player = xbmc.Player()
        current_seconds = player.getTime()

        LOG.info(
            f"Opening scheduled dialogue for {item.get_segment_type_display()} at {item.get_start_seconds()} as within segment")

        if item.get_start_seconds() <= current_seconds <= item.get_end_seconds() - SECOND_PADDING:
            self.open_gui(item)
            return

        # We are not within the segment
        LOG.info(f"Skipping dialogue for {item.get_segment_type_display()} at {item.get_start_seconds()} as not within segment")

    def cancel_scheduled(self):
        """
        Cancel the scheduled dialogue thread if it is running
        :return: None
        """

        if self.scheduled_thread:
            self.scheduled_thread.cancel()
            self.scheduled_thread = None
            LOG.info("Cancelled existing scheduled dialogue")

    def close_gui(self):
        """
        Close the dialogue if it is open / stored
        :return: None
        """
        if self.dialogue:
            self.dialogue.close()
            self.dialogue = None

    def is_last_item(self, item: MediaSegmentItem):
        """
        Check if the last segment item is the same as the current segment item
        :param item:
        :return:
        """
        if not self.last_item or not item:
            return False

        return self.last_item == item

    def is_last_item_segment(self):
        """
        Check if the last item segment is currently playing (player within the segment duration)
        :return: bool - True if the last segment item is currently playing (player within the segment duration)
        """

        player = xbmc.Player()

        if not self.last_item:
            return False

        current_seconds = player.getTime()
        return self.last_item.get_start_seconds() <= current_seconds <= self.last_item.get_end_seconds()

    def open_gui(self, item: MediaSegmentItem):
        """
        Open the dialogue for the segment item. If the segment is the same as the last segment, the dialogue is skipped.
        If the user already declined the dialogue, we don't want to show it again for the same segment.

        :param item: the segment item to open the dialogue for
        :return: None
        """

        if self.is_last_item(item):
            LOG.info(f"Skipping dialogue for {item.get_segment_type_display()} at {item.get_start_seconds()} as it is the same as the last item")
            return

        self.last_item = item
        LOG.info(f"Opening dialogue for {item.get_segment_type_display()} at {item.get_start_seconds()}")
        self.close_gui()
        
        # Check if this is an outro segment and countdown is enabled
        if item.segment_type.value == 'Outro':
            try:
                addon = xbmcaddon.Addon()
                enable_countdown = addon.getSettingBool('enable_countdown')
                if enable_countdown:
                    self._show_countdown_dialogue(item)
                else:
                    self._show_skip_dialogue(item)
            except:
                # Fallback to countdown if settings don't exist yet
                self._show_countdown_dialogue(item)
        else:
            self._show_skip_dialogue(item)

    def _show_countdown_dialogue(self, item: MediaSegmentItem):
        """Show countdown dialogue for OUTRO segments"""
        try:
            # Import countdown dialogue
            from countdown_dialogue import CountdownDialogue
            
            # Use the stored jf_hack instance
            next_episode = None
            if self.jf_hack:
                next_episode = self.jf_hack.get_next_episode()
            else:
                LOG.info("No jf_hack instance available")
            
            # Get countdown duration from settings
            try:
                addon = xbmcaddon.Addon()
                countdown_duration = addon.getSettingInt('countdown_duration')
                if countdown_duration == 0:  # Default if setting doesn't exist
                    countdown_duration = 15
            except:
                countdown_duration = 15
            
            # Create and show countdown dialog
            dialog = CountdownDialogue(
                'countdown_dialogue.xml',
                addonPath,
                next_episode_title=next_episode.get("Name", "Unknown Episode") if next_episode else "Unknown Episode",
                countdown_duration=countdown_duration
            )
            
            self.dialogue = dialog
            LOG.info("Showing countdown dialog for OUTRO segment")
            dialog.doModal()
            
            # Handle user action
            if dialog.user_action == 'play_now' or dialog.user_action == 'timeout':
                self._play_next_episode(next_episode)
                LOG.info(f"User action: {dialog.user_action}, playing next episode")
            else:
                LOG.info(f"User action: {dialog.user_action}, staying on current episode")
                
            del dialog
            
        except Exception as e:
            LOG.info(f"Error showing countdown dialogue: {e}")
            # Fallback to regular skip dialog
            self._show_skip_dialogue(item)

    def _show_skip_dialogue(self, item: MediaSegmentItem):
        """Show regular skip dialogue for non-OUTRO segments"""
        try:
            dialog = SkipSegmentDialogue('script-dialog.xml', addonPath, seek_time_seconds=item.get_end_seconds(),
                                         segment_type=item.get_segment_type_display())
            self.dialogue = dialog
            LOG.info(f"Showing skip dialog for {item.get_segment_type_display()} segment")
            dialog.doModal()
            del dialog
            
        except Exception as e:
            LOG.info(f"Error showing skip dialogue: {e}")

    def _play_next_episode(self, next_episode):
        """Play the next episode using Jellyfin plugin"""
        try:
            if not next_episode:
                LOG.info("No next episode to play")
                return
                
            episode_id = next_episode.get('Id')
            if episode_id:
                # Use Jellyfin plugin URL to play next episode
                jellyfin_url = f"plugin://plugin.video.jellyfin/?mode=play&id={episode_id}"
                LOG.info(f"Playing next episode: {jellyfin_url}")
                xbmc.Player().play(jellyfin_url)
            else:
                LOG.info("No episode ID found")
                
        except Exception as e:
            LOG.info(f"Error playing next episode: {e}")


dialogue_handler = DialogueHandler()
