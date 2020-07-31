import asyncio
import datetime
import operator

import pytest

from apd.aggregation.actions.runner import DataProcessor
from apd.aggregation.actions.base import Trigger
from apd.aggregation.actions.action import (
    OnlyOnChangeActionWrapper,
    SaveToDatabaseAction,
)
from apd.aggregation.actions.trigger import ValueThresholdTrigger
from apd.aggregation.database import DataPoint
from apd.aggregation.query import get_data
from .test_analysis import generate_datapoints


class AlwaysTrueTrigger(Trigger[bool]):
    name = "AlwaysTrue"

    async def start(self):
        pass

    async def match(self, datapoint: DataPoint) -> bool:
        return True

    async def extract(self, datapoint: DataPoint) -> bool:
        return True


class StoreAction(Trigger[bool]):
    async def start(self):
        self.data = asyncio.Queue()

    async def handle(self, datapoint: DataPoint) -> None:
        await self.data.put(datapoint)


class TestRunner:
    @pytest.fixture
    @pytest.mark.asyncio
    async def runner(self, event_loop):
        processor = DataProcessor(
            name="Test data runner", action=StoreAction(), trigger=AlwaysTrueTrigger(),
        )
        await processor.start()
        yield processor
        await processor.end()

    @pytest.mark.asyncio
    async def test_simple_flow(self, runner, event_loop):
        data = [(datetime.datetime(2020, 4, 1, 12, 0, 0), 65.0)]
        datapoints = generate_datapoints(data)
        async for datapoint in datapoints:
            await runner.push(datapoint)

        output = await runner.action.data.get()
        assert output.sensor_name == runner.trigger.name
        assert output.collected_at == data[0][0]
        assert output.data == True


class TestRealWorldRunner:
    @pytest.fixture
    @pytest.mark.asyncio
    async def runner(self, migrated_db, event_loop):
        processor = DataProcessor(
            name="TemperatureAbove20",
            action=OnlyOnChangeActionWrapper(SaveToDatabaseAction()),
            trigger=ValueThresholdTrigger(
                name="TemperatureAbove20",
                threshold=20,
                comparator=operator.gt,
                sensor_name="Temperature",
            ),
        )
        await processor.start()
        yield processor
        await processor.end()

    @pytest.mark.asyncio
    async def test_real_usecase(self, runner, event_loop):
        data = [
            (datetime.datetime(2020, 4, 1, 12, 0, 0), 19.0),
            (datetime.datetime(2020, 4, 1, 13, 0, 0), 18.0),
            (datetime.datetime(2020, 4, 1, 14, 0, 0), 21.0),
            (datetime.datetime(2020, 4, 1, 15, 0, 0), 22.0),
            (datetime.datetime(2020, 4, 1, 16, 0, 0), 21.0),
        ]

        async for datapoint in generate_datapoints(data, sensor_name="Temperature"):
            await runner.push(datapoint)

        # Wait up to 10 seconds for the runner to be idle
        await asyncio.wait_for(runner.idle(), timeout=10)

        stored_datapoints = [
            point async for point in get_data(sensor_name="TemperatureAbove20")
        ]

        assert len(stored_datapoints) == 2
        assert stored_datapoints[0].data == False
        assert stored_datapoints[0].collected_at == datetime.datetime(
            2020, 4, 1, 12, 0, 0
        )
        assert stored_datapoints[1].data == True
        assert stored_datapoints[1].collected_at == datetime.datetime(
            2020, 4, 1, 14, 0, 0
        )
