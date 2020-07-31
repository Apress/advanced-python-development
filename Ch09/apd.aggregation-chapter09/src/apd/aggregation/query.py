import asyncio
import contextlib
from contextvars import ContextVar
import datetime
import typing as t
from uuid import UUID

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import Session


from apd.aggregation.database import (
    datapoint_table,
    DataPoint,
    deployment_table,
    Deployment,
)


db_session_var: ContextVar[Session] = ContextVar("db_session")


@contextlib.contextmanager
def with_database(uri: t.Optional[str] = None) -> t.Iterator[Session]:
    """Given a URI, set up a DB connection, and return a Session as a context manager """
    if uri is None:
        uri = "postgresql+psycopg2://localhost/apd"
    engine = create_engine(uri)
    sm = sessionmaker(engine)
    Session = sm()
    token = db_session_var.set(Session)
    try:
        yield Session
        Session.commit()
    finally:
        db_session_var.reset(token)
        Session.close()


async def get_data(
    sensor_name: t.Optional[str] = None,
    deployment_id: t.Optional[UUID] = None,
    collected_before: t.Optional[datetime.datetime] = None,
    collected_after: t.Optional[datetime.datetime] = None,
) -> t.AsyncIterator[DataPoint]:
    db_session = db_session_var.get()
    loop = asyncio.get_running_loop()
    query = db_session.query(datapoint_table)
    if sensor_name:
        query = query.filter(datapoint_table.c.sensor_name == sensor_name)
    if deployment_id:
        query = query.filter(datapoint_table.c.deployment_id == deployment_id)
    if collected_before:
        query = query.filter(datapoint_table.c.collected_at < collected_before)
    if collected_after:
        query = query.filter(datapoint_table.c.collected_at > collected_after)
    query = query.order_by(
        datapoint_table.c.deployment_id,
        datapoint_table.c.sensor_name,
        datapoint_table.c.collected_at,
    )

    rows = await loop.run_in_executor(None, query.all)
    for row in rows:
        yield DataPoint.from_sql_result(row)


async def get_deployment_ids() -> t.List[UUID]:
    db_session = db_session_var.get()
    loop = asyncio.get_running_loop()
    query = db_session.query(datapoint_table.c.deployment_id).distinct()
    return [row.deployment_id for row in await loop.run_in_executor(None, query.all)]


async def get_deployment_by_id(deployment_id: UUID) -> Deployment:
    db_session = db_session_var.get()
    loop = asyncio.get_running_loop()
    query = db_session.query(deployment_table).filter(
        deployment_table.c.id == deployment_id
    )
    return [
        Deployment.from_sql_result(row)
        for row in await loop.run_in_executor(None, query.all)
    ][0]


async def get_data_by_deployment(
    *args: t.Any, **kwargs: t.Any
) -> t.AsyncIterator[t.Tuple[UUID, t.AsyncIterator[DataPoint]]]:
    """Return an Async Iterator that contains two-item pairs.
    These pairs are a string (deployment_id), and an async iterator that contains
    the datapoints with that deployment_id.

    Usage example:

        async for deployment_id, datapoints in get_data_by_deployment():
            print(deployment_id)
            async for datapoint in datapoints:
                print(datapoint)
            print()
    """
    # Get the data, using the arguments to this function as filters
    data = get_data(*args, **kwargs)

    # The two levels of iterator share the item variable, initialise it with the
    # first item from the iterator. Also set last_deployment_id to None, so the
    # outer iterator knows to start a new group.
    last_deployment_id: t.Optional[UUID] = None
    try:
        item = await data.__anext__()
    except StopAsyncIteration:
        # There were no items in the underlying query, return immediately
        return

    async def subiterator(group_id: UUID) -> t.AsyncIterator[DataPoint]:
        """Using a closure, create an iterator that yields the current
        item, then yields all items from data while the deployment_id matches
        group_id, leaving the first that doesn't match as item in the enclosing
        scope."""
        # item is from the enclosing scope
        nonlocal item
        while item.deployment_id == group_id:
            # yield items from data while they match the group_id this iterator represents
            yield item
            try:
                # Advance the underlying iterator
                item = await data.__anext__()
            except StopAsyncIteration:
                # The underlying iterator came to an end, so end the subiterator too
                return

    while True:
        while item.deployment_id == last_deployment_id:
            # We are trying to advance the outer iterator while the underlying iterator
            # is still part-way through a group. Speed through the underlying until we
            # hit an item where the deployment_id is different to the last one (or, is not
            # None, in the case of the start of the iterator)
            try:
                item = await data.__anext__()
            except StopAsyncIteration:
                # We hit the end of the underlying iterator: end this iterator too
                return
        last_deployment_id = item.deployment_id
        # Don't yield an iterator for unclassified deployments
        if last_deployment_id is not None:
            # Instantiate a subiterator for this group
            yield last_deployment_id, subiterator(last_deployment_id)
