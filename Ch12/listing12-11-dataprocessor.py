@dataclasses.dataclass(unsafe_hash=True)
class DataProcessor:
    name: str
    action: Action
    trigger: Trigger[t.Any]

    def __post_init__(self):
        self._input: t.Optional[asyncio.Queue[DataPoint]] = None
        self._sub_tasks: t.Set = set()

    async def start(self) -> None:
        self._input = asyncio.Queue()
        self._task = asyncio.create_task(self.process(), name=f"{self.name}_process")
        await asyncio.gather(self.action.start(), self.trigger.start())

    @property
    def input(self) -> asyncio.Queue[DataPoint]:
        if self._input is None:
            raise RuntimeError(f"{self}.start() was not awaited")
        if self._task.done():
            raise RuntimeError("Processing has stopped") from self._task.exception()
        return self._input

    async def idle(self) -> None:
        await self.input.join()

    async def end(self) -> None:
        self._task.cancel()

    async def push(self, obj: DataPoint) -> None:
        return await self.input.put(obj)

    async def process(self) -> None:
        while True:
            data = await self.input.get()
            try:
                processed = await self.trigger.handle(data)
            except ValueError:
                continue
            else:
                action_taken = await self.action.handle(processed)
            finally:
                self.input.task_done()

