from __future__ import annotations

import asyncio
import collections
import dataclasses
import time
import typing as t

from ..database import DataPoint
from .base import Action, Trigger

Decorated_Type = t.TypeVar("Decorated_Type", bound=t.Callable[..., t.Any])


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

    async def start(self) -> None:
        self._input = asyncio.Queue(64)
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
        coro = self.input.put(obj)
        return await asyncio.wait_for(coro, timeout=30)

    async def process(self) -> None:
        while True:
            data = await self.input.get()
            start = time.time()
            self.total_in += 1
            try:
                action_taken = False
                processed = await self.trigger.handle(data)
                if processed:
                    action_taken =await self.action.handle(processed)
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
        return f"{avr_time:0.3f} seconds per item. {self.total_in} in, {self.total_out} out, {self.input.qsize()} waiting."
