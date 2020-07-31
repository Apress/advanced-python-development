import typing as t
from uuid import UUID

from apd.aggregation.database import DataPoint
from apd.aggregation.query import get_data


async def get_data_by_deployment(
    *args, **kwargs
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
        # Instantiate a subiterator for this group
        yield last_deployment_id, subiterator(last_deployment_id)

