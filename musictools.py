import os
from datetime import timedelta
from typing import Any


class Track(object):

    def __init__(self, id: str, title: str, url: str, duration: Any, filename: str):
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

    def prettify(self):
        return "({duration})[{title}]".format(
            duration=timedelta(seconds=self.duration),
            title=self.title)

    def is_available(self):
        return os.path.isfile(self.filename)


class Skip(object):

    def __init__(self, limit=1):
        self.limit = limit
        self.register = set()

    def add(self, user) -> bool:
        if user in self.register:
            return False
        else:
            self.register.add(user)
            return True

    def clear(self):
        self.register.clear()

    def ready(self) -> bool:
        return len(self.register) >= self.limit

    def status(self):
        return "{votes} votes, {limit} needed".format(votes=len(self.register), limit=self.limit)
