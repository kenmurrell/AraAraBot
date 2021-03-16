from collections import deque
import typing
from datetime import timedelta


class Playlist(object):

    def __init__(self, limit=100):
        self.limit = 100
        self.playque = deque()

    def __len__(self):
        return len(self.playque)

    def add(self, track):
        if len(self) > self.limit:
            raise Exception("Queue limit reached")
        else:
            self.playque.append(track)

    def next(self):
        if len(self.playque) == 0:
            return None
        return self.playque.popleft()

    def clear(self):
        self.playque.clear()


class Track(object):

    def __init__(self, id, title, url, duration, filename):
        self.id = id
        self.title = title
        self.url = url
        self.duration = int(duration)
        self.filename = filename

    def details(self):
        return "({duration})({id})[{title}](url={url})".format(
            duration=self.timestr(),
            id=self.id,
            title=self.title,
            url=self.url)

    def timestr(self):
        return timedelta(seconds=self.duration)

    def __str__(self):
        return "({duration})[{title}]".format(
            duration=self.timestr(),
            title=self.title)
