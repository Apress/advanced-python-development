import asyncio

from apd.aggregation.query import db_session_var, get_data

async def get_data_ongoing(*args, **kwargs):
    last_id = 0
    db_session = db_session_var.get()
    while True:
        # Run a timer for 300 seconds concurrently with our work
        minimum_loop_timer = asyncio.create_task(asyncio.sleep(300))
        async for datapoint in get_data(*args, **kwargs):
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
        # Wait for that timer to complete. If our loop took over 5 minutes
        # this will complete immediately, otherwise it will block
        await minimum_loop_timer

