import asyncio
from contextvars import ContextVar

from apd.aggregation.query import db_session_var, get_data

refeed_queue_var = ContextVar("refeed_queue")


async def queue_as_iterator(queue):
    while not queue.empty():
        yield queue.get_nowait()


async def get_data_ongoing(*args, historical=False, **kwargs):
    last_id = 0
    if not historical:
        kwargs["inserted_after_record_id"] = last_id = await get_newest_record_id()
    db_session = db_session_var.get()
    refeed_queue = refeed_queue_var.get()

    while True:
        # Run a timer for 300 seconds concurrently with our work
        minimum_loop_timer = asyncio.create_task(asyncio.sleep(300))
        import datetime
        async for datapoint in get_data(*args, inserted_after_record_id=last_id, order=False, **kwargs):
            if datapoint.id > last_id:
                # This is the newest datapoint we have handled so far
                last_id = datapoint.id
            yield datapoint

        while not refeed_queue.empty():
            # Process any datapoints gathered through the refeed queue       
            async for datapoint in queue_as_iterator(refeed_queue):
                yield datapoint

        # Commit the DB to store any work that was done in this loop and
        # ensure that any isolation level issues do not prevent loading more
        # data
        db_session.commit()
        # Wait for that timer to complete. If our loop took over 5 minutes
        # this will complete immediately, otherwise it will block
        await minimum_loop_timer

