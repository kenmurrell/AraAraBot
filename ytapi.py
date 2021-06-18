import os
from typing import List

import regex as re
import youtube_dl

from musictools import Track


class YoutubeAPI(object):
    MASTER = "^(?P<base>https?\:\/\/www\.youtube\.com\/)(?P<video>watch\?v\=[0-9A-Za-z\-\_]{11})?(?P<playlistheader>playlist\?)?(?P<playlistid>\&?list\=[0-9A-Za-z\-\_]{10,36})?"
    YT_MASTER_PATTERN = re.compile(MASTER)

    def __init__(self, options: dict, directory: str):
        self.options = options
        self.directory = directory

    async def download_track(self, track: Track) -> bool:
        if not track.filename:
            raise YTDownloaderError()
        if track.is_available():
            return True
        try:
            with youtube_dl.YoutubeDL(self.options) as ytdl:
                ytdl.download([track.url])
            return track.is_available()
        except youtube_dl.DownloadError as ex:
            raise YTDownloaderError(str(ex))

    async def create_tracks(self, url: str) -> List[Track]:
        comp = self.YT_MASTER_PATTERN.search(url)
        if not comp:
            raise InvalidLinkError("Link does not match allowed structure!")
        is_playlist = False
        if comp.group("base") and comp.group("video"):
            # quick way to clean video url
            url = comp.group("base") + comp.group("video")
        elif comp.group("base") and comp.group("playlistheader") and comp.group("playlistid"):
            is_playlist = True
            url = comp.group("base") + comp.group("playlistheader") + comp.group("playlistid")
        tracklist = list()
        try:
            info_dict = None
            with youtube_dl.YoutubeDL(self.options) as ytdl:
                info_dict = ytdl.extract_info(url, download=False)
            entries = info_dict["entries"] if is_playlist else [info_dict]
            if len(entries) == 0:
                raise YTReturnedEmptyError("Youtube returned an empty list of entries. You may have tried this playlist too many times")
            for vid in info_dict["entries"] if is_playlist else [info_dict]:
                # check if video exists
                video_path = os.path.join(self.directory, "{}.{}".format(vid["id"], "mp3"))
                track = Track(vid["id"], vid["title"], vid["webpage_url"], vid["duration"], video_path)
                tracklist.append(track)
        except youtube_dl.DownloadError as ex:
            raise YTDownloaderError(str(ex))
        return tracklist

    def get(self, url: str) -> List[Track]:
        comp = self.YT_MASTER_PATTERN.search(url)
        if not comp:
            raise InvalidLinkError("Link does not match allowed structure!")
        is_playlist = False
        if comp.group("base") and comp.group("video"):
            # quick way to clean video url
            url = comp.group("base") + comp.group("video")
        elif comp.group("base") and comp.group("playlistheader") and comp.group("playlistid"):
            is_playlist = True
            url = comp.group("base") + comp.group("playlistheader") + comp.group("playlistid")
        tracklist = list()
        with youtube_dl.YoutubeDL(self.options) as ytdl:
            try:
                info_dict = ytdl.extract_info(url, download=False)
                entries = info_dict["entries"] if is_playlist else [info_dict]
                if len(entries) == 0:
                    raise YTReturnedEmptyError("Youtube returned an empty list of entries. You may have tried this playlist too many times")
                ytdl.download([url])
                for vid in info_dict["entries"] if is_playlist else [info_dict]:
                    # check if video exists
                    video_path = os.path.join(self.directory, "{}.{}".format(vid["id"], "mp3"))
                    if not os.path.isfile(video_path):
                        continue
                    track = Track(vid["id"], vid["title"], vid["webpage_url"], vid["duration"], video_path)
                    tracklist.append(track)
            except youtube_dl.DownloadError as ex:
                raise YTDownloaderError(str(ex))
        return tracklist


class YTDownloaderError(Exception):
    pass


class YTReturnedEmptyError(Exception):
    pass


class InvalidLinkError(Exception):
    pass
