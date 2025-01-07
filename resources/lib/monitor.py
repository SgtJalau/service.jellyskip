import json
import xbmc

from jellyfin.jellyfin_grabber import JellyfinHack
from player import JellySkipPlayer
from utils import log, log_exception

class JellySkipMonitor(xbmc.Monitor):

    def __init__(self):
        super().__init__()
        self.player = JellySkipPlayer()

    def __del__(self):
        del self.player

    def run(self):
        log('Starting JellySkipMonitor')
        self.waitForAbort()
        log('Stopping JellySkipMonitor')
        self.player.terminate()

    def onNotification(self, sender, method, data):
        log(f"Notification: sender={sender}, method={method}, data={data}")
        if method == "Player.OnAVStart" and sender == "xbmc" and data:
            if not self.player.isPlayingVideo():
                return

            try:
                data = json.loads(data)["item"]
                kodi_id = data["id"]
                media_type = data["type"]

                if jellyfin_itemid := JellyfinHack.get_jf_item_id_from_kodi_id(kodi_id, media_type):
                    if media_segments := JellyfinHack.fetch_media_segments(jellyfin_itemid):
                        self.player.start_tracking(media_segments)
                else:
                    log("Couldn't determine Jellyfin item ID")
            except Exception:
                log_exception()
