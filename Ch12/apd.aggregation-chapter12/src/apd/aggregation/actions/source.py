import asyncio
from contextvars import ContextVar
import logging

from apd.aggregation.query import db_session_var, get_data

refeed_queue_var: ContextVar[asyncio.Queue] = ContextVar("refeed_queue")
logger = logging.getLogger(__name__)


async def get_newest_record_id():
    from apd.aggregation.database import datapoint_table
    from sqlalchemy import func

    loop = asyncio.get_running_loop()
    db_session = db_session_var.get()
    max_id_query = db_session.query(func.max(datapoint_table.c.id))
    return await loop.run_in_executor(None, max_id_query.scalar)


async def queue_iterator(queue):
    while not queue.empty():
        yield queue.get_nowait()


async def get_data_ongoing(*args, historical=False, **kwargs):
    last_id = 0
    if not historical:
        last_id = await get_newest_record_id()
    db_session = db_session_var.get()
    refeed_queue = refeed_queue_var.get()

    while True:
        # Run a timer for 300 seconds concurrently with our work
        minimum_loop_timer = asyncio.create_task(asyncio.sleep(30))

        async for datapoint in get_data(
            *args, inserted_after_record_id=last_id, order=False, **kwargs
        ):
            if datapoint.id > last_id:
                # This is the newest datapoint we have handled so far
                last_id = datapoint.id
            yield datapoint
            # Next time, find only data points later than the latest we've seen

        while not refeed_queue.empty():
            # Process any datapoints gathered through the refeed queue
            logger.info("Passing refeed queue")
            async for datapoint in queue_iterator(refeed_queue):
                yield datapoint

        # Commit the DB to store any work that was done in this loop and
        # ensure that any isolation level issues do not prevent loading more
        # data
        db_session.commit()
        # Wait for that timer to complete. If our loop took over 5 minutes
        # this will complete immediately, otherwise it will block
        await minimum_loop_timer
        logger.info("Getting next group of data")


async def wait_for_notify(loop, raw_connection):
    waiting = True
    while waiting:
        # SQLAlchemy isn't asynchronous, poll in a new thread
        # to make sure we've received any notifications
        await loop.run_in_executor(None, raw_connection.poll)
        while raw_connection.notifies:
            # End the loop after clearing out all pending
            # notifications
            waiting = False
            raw_connection.notifies.pop()
        if waiting:
            # If we had no notifications wait 15 seconds then
            # re-check
            await asyncio.sleep(15)


async def get_data_ongoing_psql_pubsub(*args, historical=False, **kwargs):
    last_id = 0
    if not historical:
        kwargs["inserted_after_record_id"] = last_id = await get_newest_record_id()
    db_session = db_session_var.get()
    db_session.execute("LISTEN apd_aggregation;")
    loop = asyncio.get_running_loop()
    while True:
        async for datapoint in get_data(*args, order=False, **kwargs):
            if datapoint.id > last_id:
                # This is the newest datapoint we have handled so far
                last_id = datapoint.id
            yield datapoint
            # Next time, find only data points later than the latest we've seen
            kwargs["inserted_after_record_id"] = last_id
        # Commit the DB to store any work that was done in this loop and
        # ensure that any isolation level issues do not prevent loading more
        # data
        db_session.commit()

        connection = db_session.connection()
        raw_connection = connection.connection
        await wait_for_notify(loop, raw_connection)
        # Always yield new records from this point on
