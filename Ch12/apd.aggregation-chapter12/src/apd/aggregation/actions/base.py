import typing as t

from ..typing import T_value
from ..database import DataPoint
from ..exceptions import NoDataForTrigger


class Trigger(t.Generic[T_value]):
    name: str

    async def start(self) -> None:
        """ Coroutine to do any initial setup """
        return

    async def match(self, datapoint: DataPoint) -> bool:
        """ Return True if the datapoint is of interest to this
        trigger.
        This is an optional method, called by the default implementation
        of handle(...)."""
        raise NotImplementedError

    async def extract(self, datapoint: DataPoint) -> T_value:
        """ Return the value that this datapoint implies for this trigger,
        or raise NoDataForTrigger if no value is appropriate.
        Can also raise IncompatibleTriggerError if the value is not readable.

        This is an optional method, called by the default implementation
        of handle(...).
        """
        raise NotImplementedError

    async def handle(self, datapoint: DataPoint) -> t.Optional[DataPoint]:
        """Given a data point, optionally return a datapoint that
        represents the value of this trigger. Will delegate to the
        match(...) and extract(...) functions."""
        if not await self.match(datapoint):
            # This data point isn't relevant
            return None

        try:
            value = await self.extract(datapoint)
        except NoDataForTrigger:
            # There was no value for this point
            return None

        return DataPoint(
            sensor_name=self.name,
            data=value,
            deployment_id=datapoint.deployment_id,
            collected_at=datapoint.collected_at,
        )


class Action:
    async def start(self) -> None:
        """ Coroutine to do any initial setup """
        return

    async def handle(self, datapoint: DataPoint) -> bool:
        """ Apply this datapoint to the action, returning
        a boolean to indicate success. """
        raise NotImplementedError
