from collections import deque
import typing
from datetime import timedelta


class Playlist(object):

    def __init__(self, limit=100):
        self.limit = limit
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

    def isempty(self):
        return len(self) == 0

    def clear(self):
        self.playque.clear()


class Track(object):

    def __init__(self, id: str, title: str, url: str, duration: typing.Any, filename: str):
        self.id = id
        self.title = title
        self.url = url
        self.duration = int(duration)
        self.filename = filename

    def details(self):
        return "({duration})({id})[{title}](url={url})".format(
            duration=timedelta(seconds=self.duration),
            id=self.id,
            title=self.title,
            url=self.url)

    def __str__(self):
        return "({duration})[{title}]".format(
            duration=timedelta(seconds=self.duration),
            title=self.title)


class Skip(object):

    def __init__(self, limit=2):
        self.limit = limit
        self.register = set()

    def add(self, user) -> bool:
        if user in self.register:
            return False
        self.register.add(user)
        return True

    def clear(self):
        self.register.clear()

    def ready(self) -> bool:
        return len(self.register) >= self.limit

    def status(self):
        return "{votes} votes, {limit} needed".format(votes=len(self.register), limit=self.limit)
