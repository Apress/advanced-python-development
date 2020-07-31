import asyncio
from concurrent.futures import ThreadPoolExecutor
import functools


def wrap_coroutine(f):
    @functools.wraps(f)
    def run_in_thread(*args, **kwargs):
        loop = asyncio.new_event_loop()
        wrapped = f(*args, **kwargs)
        with ThreadPoolExecutor(max_workers=1) as pool:
            task = pool.submit(loop.run_until_complete, wrapped)
        return task.result()
    return run_in_thread

async def main() -> None:
    print(
        add_number_from_callback(
            constant, wrap_coroutine(async_get_number_from_HTTP_request)
        )
    )


