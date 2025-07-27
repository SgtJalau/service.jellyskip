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
            
                # Log the full API call
                LOG.info(f"Making API call to: {self._jellyfin_server}/{api_endpoint}")
            
                ret = self.make_request(api_endpoint)
            
                # Log the raw response
                LOG.info(f"Raw API response: {ret}")
            
                if ret and 'Items' in ret:
                    media_segments_response = MediaSegmentResponse.from_json(ret)
                    self.media_segments = media_segments_response
                    LOG.info(f"MediaSegments: {media_segments_response}")
                else:
                    LOG.info(f"API returned empty or invalid response: {ret}")
            else:
                LOG.info("No itemid")
        except Exception as e:
            LOG.info(f"API call failed with error: {e}")
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



    def get_next_episode(self):
        """Get next episode information using Jellyfin's episode ordering"""
        try:
            if not self.jellyfin_itemid:
                LOG.info("No jellyfin_itemid for next episode lookup")
                return None
                
            self.setup_jellyfin_server()
            
            # Get current item details
            current_item_endpoint = f"Items/{self.jellyfin_itemid}"
            LOG.info(f"Getting current item: {current_item_endpoint}")
            current_item = self.make_request(current_item_endpoint)
            
            if current_item.get('Type') != 'Episode':
                LOG.info(f"Current item is not an episode: {current_item.get('Type')}")
                return None
                
            # Get series info
            series_id = current_item.get('SeriesId')
            if not series_id:
                LOG.info("No SeriesId found")
                return None
            
            LOG.info(f"Current episode: {current_item.get('Name', 'Unknown')}")
            
            # Get ALL episodes for the series in proper viewing order
            # Use SortBy to get episodes in the correct sequence
            all_episodes_endpoint = f"Shows/{series_id}/Episodes?SortBy=SortName&SortOrder=Ascending&Fields=ParentIndexNumber,IndexNumber"
            LOG.info(f"Getting all episodes in viewing order")
            
            all_episodes_response = self.make_request(all_episodes_endpoint)
            all_episodes = all_episodes_response.get('Items', [])
            
            LOG.info(f"Found {len(all_episodes)} total episodes")
            
            # Find current episode in the list
            current_episode_index = None
            for i, episode in enumerate(all_episodes):
                if episode.get('Id') == self.jellyfin_itemid:
                    current_episode_index = i
                    LOG.info(f"Found current episode at index {i}")
                    break
            
            if current_episode_index is None:
                LOG.info("Could not find current episode in series episode list")
                return None
            
            # Get the next episode (skip Season 0/specials if needed)
            for next_index in range(current_episode_index + 1, len(all_episodes)):
                next_episode = all_episodes[next_index]
                next_season = next_episode.get('ParentIndexNumber', 0)
                
                # Skip Season 0 (specials) - look for regular seasons
                if next_season == 0:
                    LOG.info(f"Skipping Season 0 episode: {next_episode.get('Name', 'Unknown')}")
                    continue
                
                # Found a valid next episode
                next_ep_num = next_episode.get('IndexNumber', 0)
                next_name = next_episode.get('Name', 'Unknown')
                LOG.info(f"Found next episode: S{next_season:02d}E{next_ep_num:02d} - {next_name}")
                return next_episode
            
            LOG.info("No next episode found (end of series or only specials remaining)")
            return None
            
        except Exception as e:
            LOG.info(f"Error getting next episode: {e}")
            return None
