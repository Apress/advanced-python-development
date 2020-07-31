import asyncio
import itertools
import typing as t

async def sum_ints(data: asyncio.Queue) -> t.AsyncIterator[int]:
    """Yields a running total a queue, until a None is found"""
    total = 0
    while True:
        num = await data.get()
        if num is None:
            data.task_done()
            break
        total += num
        data.task_done()
        yield total
        

def numbers() -> t.Iterator[int]:
    yield 1
    yield 1
    yield 1


async def test():
    # Start with 1, feed output back in, limit to 3 items
    data = asyncio.Queue()
    sums = sum_ints(data)

    # Send the initial value
    await data.put(1)
    result = []
    async for last in sums:
        if len(result) == 3:
            # Stop the summer at 3 items
            await data.put(None)
        else:
            # Send the last value retrieved back
            await data.put(last)
            result.append(last)
    assert result == [1, 2, 4]


    # Add 3 items from a standard iterable
    data = asyncio.Queue()
    sums = sum_ints(data)

    for number in numbers():
        await data.put(number)
    await data.put(None)
    result = [value async for value in sums]
    assert result == [1, 2, 3]

