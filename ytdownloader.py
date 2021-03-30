import typing
import os
import regex as re
import youtube_dl
from musictools import Track


class YTDownloader(object):
    YT_PATTERN = re.compile("(https?\:\/\/www\.youtube\.com\/watch\?v\=[0-9A-Za-z\-\_]{11})(.*)")

    def __init__(self, options: dict, directory: str):
        self.options = options
        self.directory = directory

    def get(self, url: str) -> Track:
        s = self.YT_PATTERN.search(url)
        if not s:
            raise InvalidLinkError("Link does not match allowed structure!")
        link = s.group(1)
        try:
            with youtube_dl.YoutubeDL(self.options) as ydl:
                info_dict = ydl.extract_info(link, download=False)
                video_id = info_dict.get("id", None)
                video_title = info_dict.get("title", None)
                video_duration = info_dict.get("duration", None)
                ydl.download([link])
                video_path = os.path.join(self.directory, "{}.{}".format(video_id, "mp3"))
                track = Track(video_id, video_title, url, video_duration, video_path)
                return track
        except youtube_dl.DownloadError as ex:
            raise YTDownloaderError(str(ex))


class YTDownloaderError(Exception):
    pass


class InvalidLinkError(Exception):
    pass
