# -*- coding: utf-8 -*-
# GNU General Public License v2.0 (see COPYING or https://www.gnu.org/licenses/gpl-2.0.txt)
import json
import sqlite3
import urllib.request
import xbmcvfs

from .media_segments import MediaSegmentResponse
from utils import log

class JellyfinHack:
    __jellyfin_db_path = None
    _jellyfin_server = None
    _jellyfin_apikey = None

    @staticmethod
    def get_jf_item_id_from_kodi_id(kodi_id, media_type):
        if kodi_id and media_type:
            with sqlite3.connect(f"file:{JellyfinHack._jellyfin_db_path()}?mode=ro", uri=True) as conn:
                cursor = None
                try:
                    cursor = conn.cursor()
                    cursor.execute("SELECT jellyfin_id FROM jellyfin WHERE kodi_id = ? AND media_type = ?", (kodi_id, media_type,))
                    return cursor.fetchone()[0]
                finally:
                    if cursor:
                        cursor.close()

        return None

    @staticmethod
    def fetch_media_segments(jellyfin_itemid):
        JellyfinHack._setup_jellyfin_server()
        api_endpoint = f"MediaSegments/{jellyfin_itemid}"

        response = JellyfinHack._make_request(api_endpoint)
        media_segments = MediaSegmentResponse.from_json(response)
        log(f"MediaSegments: {media_segments}")

        return media_segments

    @staticmethod
    def _jellyfin_db_path():
        if JellyfinHack.__jellyfin_db_path is not None:
            return JellyfinHack.__jellyfin_db_path

        db_path = None
        try:
            with open(xbmcvfs.translatePath("special://home/addons/plugin.video.jellyfin/jellyfin_kodi/objects/obj_map.json")) as f:
                obj_map = json.load(f)
            db_path = obj_map["jellyfin"]
        except Exception:
            pass

        if not db_path:
            db_path = "special://database/jellyfin.db"

        JellyfinHack.__jellyfin_db_path = xbmcvfs.translatePath(db_path)
        return JellyfinHack.__jellyfin_db_path

    @staticmethod
    def _setup_jellyfin_server():
        if not JellyfinHack._jellyfin_server:
            with open(xbmcvfs.translatePath("special://profile/addon_data/plugin.video.jellyfin/data.json")) as f:
                jf_servers = json.load(f)
            JellyfinHack._jellyfin_apikey = jf_servers["Servers"][0]["AccessToken"]
            JellyfinHack._jellyfin_server = jf_servers["Servers"][0]["address"]

    @staticmethod
    def _make_request(api_endpoint):
        url = f"{JellyfinHack._jellyfin_server}/{api_endpoint}"
        req = urllib.request.Request(url, headers={
            "Accept": "application/json",
            "Authorization": f"MediaBrowser Token={JellyfinHack._jellyfin_apikey}",
        })

        with urllib.request.urlopen(req, timeout=5) as response:
            return json.load(response)

