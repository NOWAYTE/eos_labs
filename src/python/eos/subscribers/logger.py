class ConsoleLogger:

    def __call__(self, event):

        print(
            f"[{event.timestamp}] "
            f"{event.symbol} "
            f"{event.bid:.5f} "
            f"{event.ask:.5f}"
        )
