import datetime
import unittest.mock

import pytest

from apd.aggregation.actions.base import Action
from apd.aggregation.actions.action import (
    OnlyOnChangeActionWrapper,
    OnlyAfterDateActionWrapper,
    SaveToDatabaseAction,
)
from apd.aggregation.query import db_session_var, get_data

from .test_analysis import generate_datapoints


class TestOnlyAfterDateActionWrapper:
    @pytest.fixture
    def subject(self):
        return OnlyAfterDateActionWrapper

    @pytest.mark.asyncio
    async def test_minimum_date_before_passing(self, subject):
        wrapped = unittest.mock.Mock(spec=Action)
        wrapper = subject(
            wrapped, date_threshold=datetime.datetime(2020, 4, 1, 14, 0, 0)
        )
        await wrapper.start()

        data = [
            (datetime.datetime(2020, 4, 1, 12, 0, 0), 21.0),
            (datetime.datetime(2020, 4, 1, 13, 0, 0), 21.0),
            (datetime.datetime(2020, 4, 1, 14, 0, 0), 22.0),
            (datetime.datetime(2020, 4, 1, 15, 0, 0), 22.0),
            (datetime.datetime(2020, 4, 1, 16, 0, 0), 21.0),
        ]
        datapoints = generate_datapoints(data)
        all_datapoints = []
        async for datapoint in datapoints:
            all_datapoints.append(datapoint)
            await wrapper.handle(datapoint)

        assert len(wrapped.handle.mock_calls) == 2
        passed = [call.args[0] for call in wrapped.handle.mock_calls]
        assert passed == [all_datapoints[3], all_datapoints[4]]


class TestOnlyOnChangeActionWrapper:
    @pytest.fixture
    def subject(self):
        return OnlyOnChangeActionWrapper

    @pytest.mark.asyncio
    async def test_initial_value_always_passed(self, subject):
        wrapped = unittest.mock.Mock(spec=Action)
        wrapper = subject(wrapped)
        await wrapper.start()

        data = [
            (datetime.datetime(2020, 4, 1, 12, 0, 0), 21.0),
        ]
        datapoints = generate_datapoints(data)
        first = await datapoints.asend(None)
        await wrapper.handle(first)
        assert len(wrapped.handle.mock_calls) == 1
        assert wrapped.handle.mock_calls[0].args[0] == first

    @pytest.mark.asyncio
    async def test_subsequent_values_only_passed_when_differing(self, subject):
        wrapped = unittest.mock.Mock(spec=Action)
        wrapper = subject(wrapped)
        await wrapper.start()

        data = [
            (datetime.datetime(2020, 4, 1, 12, 0, 0), 21.0),
            (datetime.datetime(2020, 4, 1, 13, 0, 0), 21.0),
            (datetime.datetime(2020, 4, 1, 14, 0, 0), 22.0),
            (datetime.datetime(2020, 4, 1, 15, 0, 0), 22.0),
            (datetime.datetime(2020, 4, 1, 16, 0, 0), 21.0),
        ]
        datapoints = generate_datapoints(data)
        all_datapoints = []
        async for datapoint in datapoints:
            all_datapoints.append(datapoint)
            await wrapper.handle(datapoint)

        assert len(wrapped.handle.mock_calls) == 3
        passed = [call.args[0] for call in wrapped.handle.mock_calls]
        assert passed == [all_datapoints[0], all_datapoints[2], all_datapoints[4]]


class TestSaveToDatabaseAction:
    @pytest.fixture
    def subject(self):
        return SaveToDatabaseAction

    @pytest.mark.asyncio
    async def test_datapoints_are_persisted(self, subject, migrated_db):
        db_session_var.set(migrated_db)

        wrapper = subject()
        await wrapper.start()

        data = [
            (datetime.datetime(2020, 4, 1, 12, 0, 0), 21.0),
        ]
        generated_datapoints = []
        async for datapoint in generate_datapoints(data):
            generated_datapoints.append(datapoint)
            await wrapper.handle(datapoint)

        stored_datapoints = [
            point async for point in get_data(sensor_name="TestSensor")
        ]
        assert stored_datapoints[0].data == generated_datapoints[0].data
        assert (
            stored_datapoints[0].deployment_id == generated_datapoints[0].deployment_id
        )
