from eos.storage import StorageEngine


class EventWriter:
    def __init__(self, path: str):
        self.storage = StorageEngine(path)

    def __call__(self, event):
        self.storage.append(event)

    def close(self):
        self.storage.close()
