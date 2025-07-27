# -*- coding: utf-8 -*-
# GNU General Public License v2.0 (see COPYING or https://www.gnu.org/licenses/gpl-2.0.txt)
import json
import urllib.request
import xbmcvfs

from helper import LazyLogger
LOG = LazyLogger(__name__)

from .media_segments import MediaSegmentResponse

class JellyfinHack:
    def __init__(self):
        self.jellyfin_itemid = None
        self._jellyfin_server = None
        self._jellyfin_apikey = None
        self.media_segments = None

    def event_handler_jellyfin_userdatachanged(self, _, **kwargs):
        if kwargs.get("sender") != "plugin.video.jellyfin":
            return

        self.reset_itemid()

        try:
            self.jellyfin_itemid = json.loads(kwargs["data"])[0]["UserDataList"][0]["ItemId"]
        except Exception:
            self.jellyfin_itemid = None

    def setup_jellyfin_server(self):
        if not self._jellyfin_server:
            with open(xbmcvfs.translatePath("special://profile/addon_data/plugin.video.jellyfin/data.json"),
                      "rb") as f:
                jf_servers = json.load(f)
            self._jellyfin_apikey = jf_servers["Servers"][0]["AccessToken"]
            self._jellyfin_server = jf_servers["Servers"][0]["address"]

    def make_request(self, api_endpoint):
        url = f"{self._jellyfin_server}/{api_endpoint}"
        req = urllib.request.Request(url, headers={
            "Accept": "application/json",
            "Authorization": f"MediaBrowser Token={self._jellyfin_apikey}",
        })

        with urllib.request.urlopen(req, timeout=5) as response:
            return json.load(response)

    def has_itemid(self):
        return self.jellyfin_itemid is not None

    def reset_itemid(self):
        self.jellyfin_itemid = None
        self.media_segments = None

    def get_media_segments(self):
        if self.media_segments is None:
            self._fetch_media_segments()
        return self.media_segments

    def _fetch_media_segments(self):
        ret = None
        try:
            if self.jellyfin_itemid:
                self.setup_jellyfin_server()
                api_endpoint = f"MediaSegments/{self.jellyfin_itemid}"

                ret = self.make_request(api_endpoint)

                media_segments_response = MediaSegmentResponse.from_json(ret)
                self.media_segments = media_segments_response

                LOG.info(f"MediaSegments: {media_segments_response}")
            else:
                LOG.info("No itemid")
        except Exception:
            pass
        finally:
            return ret

    def get_credits_time(self):
        ret = 0
        try:
            if self.jellyfin_itemid:
                self.setup_jellyfin_server()
                api_endpoint = f"Episode/{self.jellyfin_itemid}/IntroTimestamps/v1?mode=Credits"

                ret = self.make_request(api_endpoint)["IntroStart"]
        except Exception:
            pass
        finally:
            self.jellyfin_itemid = None
            return ret
