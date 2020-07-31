from .source import refeed_queue_var

class RefeedAction(Action):
    """An action that puts data points into a special queue to be consumed
    by the analysis programme"""

    async def start(self) -> None:
        return

    async def handle(self, datapoint: DataPoint) -> bool:
        refeed_queue = refeed_queue_var.get()
        if refeed_queue is None:
            logger.error("Refeed queue has not been initialised")
            return False
        else:
            await refeed_queue.put(datapoint)
            return True

