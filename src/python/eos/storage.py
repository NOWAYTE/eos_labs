from pathlib import Path


class StorageEngine:
    def __init__(self, path: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

        self._file = self.path.open("a", encoding="utf-8")

    def append(self, event):
        self._file.write(
            f"{event.timestamp.isoformat()},"
            f"{event.symbol},"
            f"{event.bid},"
            f"{event.ask},"
            f"{event.volume}\n"
        )

        self._file.flush()

    def close(self):
        self._file.close()
