import functools

@functools.singledispatch
def consume(input_iterator):
    items = [item for item in input_iterator]
    def inner_iterator():
        for item in items:
            yield item
    return inner_iterator()

@consume.register
async def consume_async(input_iterator: collections.abc.AsyncIterator):
    items = [item async for item in input_iterator]
    async def inner_iterator():
        for item in items:
            yield item
    return inner_iterator()

