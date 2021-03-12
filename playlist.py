from collections import deque


class Playlist:

    def __init__(self):
        self.playque = deque()

    def __len__(self):
        return len(self.playque)

    def add(self, track):
        self.playque.append(track)

     def next(self):
        self.playque.popleft()
        if len(self.playque) == 0:
            return None
        return self.playque[0]

    def empty(self):
        self.playque.clear()


class Track:

    def __init__(self, title, id, url, duration):
        self.id = id
        self.title = title
        self.url = url
        self.duration = duration

    def __str__(self):
        return "({duration})[title]".format(duration=self.duration, title=self.title)
