import datetime
import operator

import pytest

from apd.aggregation.actions.trigger import ValueThresholdTrigger

from .test_analysis import generate_datapoints


class TestValueThresholdTrigger:
    @pytest.fixture
    def subject(self):
        return ValueThresholdTrigger

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "comparison,expected",
        [
            (operator.gt, [False, False, False, True]),
            (operator.eq, [False, False, True, False]),
            (operator.le, [True, True, True, False]),
        ],
    )
    async def test_simple_value(self, subject, comparison, expected):
        trigger = subject(
            name=f"TestSensor{comparison.__name__}21",
            threshold=21,
            comparator=comparison,
            sensor_name="TestSensor",
        )

        data = [
            (datetime.datetime(2020, 4, 1, 12, 0, 0), 19.0),
            (datetime.datetime(2020, 4, 1, 12, 0, 0), 20.0),
            (datetime.datetime(2020, 4, 1, 12, 0, 0), 21.0),
            (datetime.datetime(2020, 4, 1, 12, 0, 0), 22.0),
        ]
        datapoints = generate_datapoints(data)

        outputs = []
        async for datapoint in datapoints:
            assert await trigger.match(datapoint)
            outputs.append(await trigger.extract(datapoint))

        assert outputs == expected

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "comparison,expected",
        [
            (operator.gt, [False, False, False, True]),
            (operator.eq, [False, False, True, False]),
            (operator.le, [True, True, True, False]),
        ],
    )
    async def test_magnitude_value(self, subject, comparison, expected):
        trigger = subject(
            name=f"TestSensor{comparison.__name__}21",
            threshold=21,
            comparator=comparison,
            sensor_name="TestSensor",
        )

        data = [
            (
                datetime.datetime(2020, 4, 1, 12, 0, 0),
                {"magnitude": 19.0, "unit": "degC"},
            ),
            (
                datetime.datetime(2020, 4, 1, 12, 0, 0),
                {"magnitude": 20.0, "unit": "degC"},
            ),
            (
                datetime.datetime(2020, 4, 1, 12, 0, 0),
                {"magnitude": 21.0, "unit": "degC"},
            ),
            (
                datetime.datetime(2020, 4, 1, 12, 0, 0),
                {"magnitude": 22.0, "unit": "degC"},
            ),
        ]
        datapoints = generate_datapoints(data)

        outputs = []
        async for datapoint in datapoints:
            assert await trigger.match(datapoint)
            outputs.append(await trigger.extract(datapoint))

        assert outputs == expected

    @pytest.mark.asyncio
    async def test_different_data_format_fails_to_extract(self, subject):
        trigger = subject(
            name="TestSensorAbove21",
            threshold=21,
            comparator=operator.eq,
            sensor_name="TestSensor",
        )

        data = [
            (datetime.datetime(2020, 4, 1, 12, 0, 0), "21.0"),
        ]
        datapoints = generate_datapoints(data)

        async for datapoint in datapoints:
            assert await trigger.match(datapoint)
            with pytest.raises(ValueError):
                await trigger.extract(datapoint)
            assert await trigger.handle(datapoint) is None

    @pytest.mark.asyncio
    async def test_different_sensors_are_not_matched(self, subject):
        trigger = subject(
            name="TestSensorAbove21",
            threshold=21,
            comparator=operator.eq,
            sensor_name="OtherSensor",
        )

        data = [
            (datetime.datetime(2020, 4, 1, 12, 0, 0), 21.0),
        ]
        datapoints = generate_datapoints(data)

        async for datapoint in datapoints:
            assert not await trigger.match(datapoint)
