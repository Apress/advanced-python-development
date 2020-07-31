class DataProcessor:
    ...

    def action_complete(self, start, task):
        action_taken = task.result()
        if action_taken:
            elapsed = time.time() - start
            self.total_out += 1
            self.last_times.append(elapsed)
        self.input.task_done()

    async def process(self) -> None:
        while True:
            data = await self.input.get()
            start = time.time()
            self.total_in += 1
            try:
                processed = await self.trigger.handle(data)
            except ValueError:
                self.input.task_done()
                continue
            else:
                result = asyncio.create_task(self.action.handle(processed))
                result.add_done_callback(functools.partial(self.action_complete, start))

