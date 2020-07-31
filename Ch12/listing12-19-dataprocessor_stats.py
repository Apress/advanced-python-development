@dataclasses.dataclass(unsafe_hash=True)
class DataProcessor:
    name: str
    action: Action
    trigger: Trigger[t.Any]

    def __post_init__(self):
        self._input: t.Optional[asyncio.Queue[DataPoint]] = None
        self._sub_tasks: t.Set = set()
        self.last_times = collections.deque(maxlen=10)
        self.total_in = 0
        self.total_out = 0

    async def process(self) -> None:
        while True:
            data = await self.input.get()
            start = time.time()
            self.total_in += 1
            try:
                processed = await self.trigger.handle(data)
            except ValueError:
                continue
            else:
                action_taken = await self.action.handle(processed)
                if action_taken:
                    elapsed = time.time() - start
                    self.total_out += 1
                    self.last_times.append(elapsed)
            finally:
                self.input.task_done()

    def stats(self) -> str:
        if self.last_times:
            avr_time = sum(self.last_times) / len(self.last_times)
        elif self.total_in:
            avr_time = 0
        else:
            return "Not yet started"
        return (
            f"{avr_time:0.3f} seconds per item. {self.total_in} in, "
            f"{self.total_out} out, {self.input.qsize()} waiting."
        )

