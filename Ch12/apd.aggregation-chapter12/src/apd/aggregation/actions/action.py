import asyncio
import dataclasses
import datetime
import logging
import typing as t

import aiohttp

from ..database import DataPoint
from ..collect import handle_result
from ..query import db_session_var
from .base import Action
from .source import refeed_queue_var

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class OnlyOnChangeActionWrapper(Action):
    """An action that requires another action as a parameter.
    The `wrapped` action will be delegated to so long as the previous
    invocation's `data` attribute is different to the current one.
    The first invocation will always be delegated."""

    wrapped: Action

    async def start(self) -> None:
        self.last_value = None
        return await self.wrapped.start()

    async def handle(self, datapoint: DataPoint) -> bool:
        if datapoint.data == self.last_value:
            return False
        else:
            self.last_value = datapoint.data
            return await self.wrapped.handle(datapoint)


@dataclasses.dataclass
class OnlyOnValueActionWrapper(Action):
    """An action that requires another action as a parameter.
    The `wrapped` action will be delegated to so long as the previous
    invocation's `data` attribute is the value specified."""

    wrapped: Action
    value: t.Any

    async def start(self) -> None:
        return await self.wrapped.start()

    async def handle(self, datapoint: DataPoint) -> bool:
        if datapoint.data == self.value:
            return await self.wrapped.handle(datapoint)
        else:
            return False


@dataclasses.dataclass
class OnlyAfterDateActionWrapper(Action):
    """An action that requires another action and a date
    as parameters. The `wrapped` action will be delegated to
    for all data points with a date strictly after `date_threshold`."""

    wrapped: Action
    date_threshold: datetime.datetime

    async def start(self) -> None:
        return await self.wrapped.start()

    async def handle(self, datapoint: DataPoint) -> bool:
        if datapoint.collected_at <= self.date_threshold:
            return False
        return await self.wrapped.handle(datapoint)


class SaveToDatabaseAction(Action):
    """An action that stores any generated data points back to the DB"""

    async def start(self) -> None:
        return

    async def handle(self, datapoint: DataPoint) -> bool:
        loop = asyncio.get_running_loop()
        session = db_session_var.get()
        await loop.run_in_executor(None, handle_result, [datapoint], session)
        return True


class LoggingAction(Action):
    """An action that stores any generated data points back to the DB"""

    async def start(self) -> None:
        return

    async def handle(self, datapoint: DataPoint) -> bool:
        logger.warn(datapoint)
        return True


class RefeedAction(Action):
    """An action that puts data points into a special queue to be consumed
    by the analysis programme"""

    async def start(self) -> None:
        return

    async def handle(self, datapoint: DataPoint) -> bool:
        refeed_queue = refeed_queue_var.get()
        if refeed_queue is None:
            logger.error("Refeed queue has not been initialised")
            return False
        else:
            logger.info(f"Re-fed {datapoint} to aggregation queue")
            await refeed_queue.put(datapoint)
            return True


@dataclasses.dataclass
class WebhookAction(Action):
    """An action that runs a webhook"""

    uri: str

    async def start(self) -> None:
        return

    async def handle(self, datapoint: DataPoint) -> bool:
        async with aiohttp.ClientSession() as http:
            async with http.post(
                self.uri,
                json={
                    "value1": datapoint.sensor_name,
                    "value2": str(datapoint.data),
                    "value3": datapoint.deployment_id.hex,
                },
            ) as request:
                logger.info(
                    f"Made webhook request for {datapoint} with status {request.status}"
                )
                return request.status == 200
