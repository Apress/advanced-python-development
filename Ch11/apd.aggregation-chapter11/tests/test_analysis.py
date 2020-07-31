import collections.abc
import datetime
import functools
import uuid
import warnings

import pytest

from apd.aggregation import analysis
from apd.aggregation.database import DataPoint, datapoint_table
from apd.aggregation.query import db_session_var


async def generate_datapoints(datas):
    deployment_id = uuid.uuid4()
    for i, (time, data) in enumerate(datas, start=1):
        yield DataPoint(
            id=i,
            collected_at=time,
            sensor_name="TestSensor",
            data=data,
            deployment_id=deployment_id,
        )


@functools.singledispatch
def consume(input_iterator):
    items = [item for item in input_iterator]

    def inner_iterator():
        for item in items:
            yield item

    return inner_iterator()


@consume.register
async def consume_async(input_iterator: collections.abc.AsyncIterator):
    items = [item async for item in input_iterator]

    async def inner_iterator():
        for item in items:
            yield item

    return inner_iterator()


class TestPassThroughCleaner:
    @pytest.fixture
    def cleaner(self):
        return analysis.clean_passthrough

    @pytest.mark.asyncio
    async def test_float_passthrough(self, cleaner):
        data = [
            (datetime.datetime(2020, 4, 1, 12, 0, 0), 65.0),
            (datetime.datetime(2020, 4, 1, 13, 0, 0), 65.5),
        ]
        datapoints = generate_datapoints(data)
        output = [(time, data) async for (time, data) in cleaner(datapoints)]
        assert output == data

    @pytest.mark.asyncio
    async def test_Nones_are_skipped(self, cleaner):
        data = [
            (datetime.datetime(2020, 4, 1, 12, 0, 0), None),
            (datetime.datetime(2020, 4, 1, 13, 0, 0), 65.5),
        ]
        datapoints = generate_datapoints(data)
        output = [(time, data) async for (time, data) in cleaner(datapoints)]
        assert output == [
            (datetime.datetime(2020, 4, 1, 13, 0, 0), 65.5),
        ]


class TestTemperatureCleaner:
    @pytest.fixture
    def cleaner(self):
        return analysis.clean_temperature_fluctuations

    @pytest.mark.asyncio
    async def test_window_not_full(self, cleaner):
        data = [
            (
                datetime.datetime(2020, 4, 1, 12, 0, 0),
                {"magnitude": 21.0, "unit": "degC"},
            ),
        ]
        datapoints = generate_datapoints(data)
        output = [(time, data) async for (time, data) in cleaner(datapoints)]
        assert output == [(datetime.datetime(2020, 4, 1, 12, 0, 0), 21.0)]

    @pytest.mark.asyncio
    async def test_window_exactly_full(self, cleaner):
        data = [
            (
                datetime.datetime(2020, 4, 1, 12, 0, 0),
                {"magnitude": 21.0, "unit": "degC"},
            ),
            (
                datetime.datetime(2020, 4, 1, 12, 0, 1),
                {"magnitude": 21.0, "unit": "degC"},
            ),
            (
                datetime.datetime(2020, 4, 1, 12, 0, 2),
                {"magnitude": 21.0, "unit": "degC"},
            ),
        ]
        datapoints = generate_datapoints(data)
        output = [(time, data) async for (time, data) in cleaner(datapoints)]
        assert output == [
            (datetime.datetime(2020, 4, 1, 12, 0, 0), 21.0),
            (datetime.datetime(2020, 4, 1, 12, 0, 1), 21.0),
            (datetime.datetime(2020, 4, 1, 12, 0, 2), 21.0),
        ]

    @pytest.mark.asyncio
    async def test_window_overfilled(self, cleaner):
        data = [
            (
                datetime.datetime(2020, 4, 1, 12, 0, 0),
                {"magnitude": 21.0, "unit": "degC"},
            ),
            (
                datetime.datetime(2020, 4, 1, 12, 0, 1),
                {"magnitude": 21.0, "unit": "degC"},
            ),
            (
                datetime.datetime(2020, 4, 1, 12, 0, 2),
                {"magnitude": 21.0, "unit": "degC"},
            ),
            (
                datetime.datetime(2020, 4, 1, 12, 0, 3),
                {"magnitude": 21.0, "unit": "degC"},
            ),
            (
                datetime.datetime(2020, 4, 1, 12, 0, 4),
                {"magnitude": 21.0, "unit": "degC"},
            ),
        ]
        datapoints = generate_datapoints(data)
        output = [(time, data) async for (time, data) in cleaner(datapoints)]
        assert output == [
            (datetime.datetime(2020, 4, 1, 12, 0, 0), 21.0),
            (datetime.datetime(2020, 4, 1, 12, 0, 1), 21.0),
            (datetime.datetime(2020, 4, 1, 12, 0, 2), 21.0),
            (datetime.datetime(2020, 4, 1, 12, 0, 3), 21.0),
            (datetime.datetime(2020, 4, 1, 12, 0, 4), 21.0),
        ]

    @pytest.mark.asyncio
    async def test_outlier_dropped(self, cleaner):
        data = [
            (
                datetime.datetime(2020, 4, 1, 12, 0, 0),
                {"magnitude": 21.0, "unit": "degC"},
            ),
            (
                datetime.datetime(2020, 4, 1, 12, 0, 1),
                {"magnitude": 61.0, "unit": "degC"},
            ),
            (
                datetime.datetime(2020, 4, 1, 12, 0, 2),
                {"magnitude": 21.0, "unit": "degC"},
            ),
        ]
        datapoints = generate_datapoints(data)
        output = [(time, data) async for (time, data) in cleaner(datapoints)]
        assert output == [
            (datetime.datetime(2020, 4, 1, 12, 0, 0), 21.0),
            (datetime.datetime(2020, 4, 1, 12, 0, 2), 21.0),
        ]

    @pytest.mark.asyncio
    async def test_limited_to_DHT22_range(self, cleaner):
        data = [
            (
                datetime.datetime(2020, 4, 1, 12, 0, 0),
                {"magnitude": 91.0, "unit": "degC"},
            ),
            (
                datetime.datetime(2020, 4, 1, 12, 0, 1),
                {"magnitude": 91.0, "unit": "degC"},
            ),
            (
                datetime.datetime(2020, 4, 1, 12, 0, 2),
                {"magnitude": 91.0, "unit": "degC"},
            ),
        ]
        datapoints = generate_datapoints(data)
        output = [(time, data) async for (time, data) in cleaner(datapoints)]
        assert output == []

    @pytest.mark.asyncio
    async def test_Nones_dropped(self, cleaner):
        data = [
            (
                datetime.datetime(2020, 4, 1, 12, 0, 0),
                {"magnitude": 31.0, "unit": "degC"},
            ),
            (datetime.datetime(2020, 4, 1, 12, 0, 1), None,),
            (
                datetime.datetime(2020, 4, 1, 12, 0, 2),
                {"magnitude": 32.0, "unit": "degC"},
            ),
        ]
        datapoints = generate_datapoints(data)
        output = [(time, data) async for (time, data) in cleaner(datapoints)]
        assert output == [
            (datetime.datetime(2020, 4, 1, 12, 0, 0), 31.0),
            (datetime.datetime(2020, 4, 1, 12, 0, 2), 32.0),
        ]


class TestWattHourCleaner:
    @pytest.fixture
    def cleaner(self):
        return analysis.clean_watthours_to_watts

    @pytest.fixture(scope="class")
    def huge_data_set(self):
        date = datetime.datetime(2020, 4, 1, 12, 0, 0)
        power = 500
        data = []
        for i in range(50_000):
            date += datetime.timedelta(hours=1)
            power += i
            data.append((date, {"magnitude": power, "unit": "watt_hour"},))
        return data

    @pytest.mark.asyncio
    async def test_one_entry_insufficient_to_find_diff(self, cleaner):
        data = [
            (
                datetime.datetime(2020, 4, 1, 12, 0, 0),
                {"magnitude": 1.0, "unit": "watt_hour"},
            ),
        ]
        datapoints = generate_datapoints(data)
        output = [(time, data) async for (time, data) in cleaner(datapoints)]
        assert output == []

    @pytest.mark.asyncio
    async def test_two_entries_provides_diff_with_second_time(self, cleaner):
        data = [
            (
                datetime.datetime(2020, 4, 1, 12, 0, 0),
                {"magnitude": 1.0, "unit": "watt_hour"},
            ),
            (
                datetime.datetime(2020, 4, 1, 13, 0, 0),
                {"magnitude": 10.0, "unit": "watt_hour"},
            ),
        ]
        datapoints = generate_datapoints(data)
        output = [(time, data) async for (time, data) in cleaner(datapoints)]
        assert len(output) == 1
        assert output[0][0] == datetime.datetime(2020, 4, 1, 13, 0, 0)
        assert output[0][1] == pytest.approx(9.0, 0.0001)

    @pytest.mark.asyncio
    async def test_nonstandard_units_can_be_used(self, cleaner):
        data = [
            (
                datetime.datetime(2020, 4, 1, 12, 0, 0),
                {"magnitude": 1.0, "unit": "watt_hour"},
            ),
            (
                datetime.datetime(2020, 4, 1, 13, 0, 0),
                {"magnitude": 10000.0, "unit": "joule"},
            ),
            (
                datetime.datetime(2020, 4, 1, 14, 0, 0),
                {"magnitude": 3.0, "unit": "watt_hour"},
            ),
        ]
        datapoints = generate_datapoints(data)
        output = [(time, data) async for (time, data) in cleaner(datapoints)]
        assert len(output) == 2
        assert output[0][0] == datetime.datetime(2020, 4, 1, 13, 0, 0)
        assert output[0][1] == pytest.approx(1.7777, 0.001)
        assert output[1][0] == datetime.datetime(2020, 4, 1, 14, 0, 0)
        assert output[1][1] == pytest.approx(0.22222, 0.001)

    @pytest.mark.asyncio
    async def test_fractional_hour(self, cleaner):
        data = [
            (
                datetime.datetime(2020, 4, 1, 12, 0, 0),
                {"magnitude": 1.0, "unit": "watt_hour"},
            ),
            (
                datetime.datetime(2020, 4, 1, 12, 23, 42),
                {"magnitude": 10.0, "unit": "watt_hour"},
            ),
        ]
        datapoints = generate_datapoints(data)
        output = [(time, data) async for (time, data) in cleaner(datapoints)]
        assert len(output) == 1
        assert output[0][0] == datetime.datetime(2020, 4, 1, 12, 23, 42)
        assert output[0][1] == pytest.approx(22.7848, 0.001)

    @pytest.mark.asyncio
    async def test_diff_happens_pairwise(self, cleaner):
        data = [
            (
                datetime.datetime(2020, 4, 1, 12, 0, 0),
                {"magnitude": 1.0, "unit": "watt_hour"},
            ),
            (
                datetime.datetime(2020, 4, 1, 12, 23, 42),
                {"magnitude": 10.0, "unit": "watt_hour"},
            ),
            (
                datetime.datetime(2020, 4, 1, 13, 23, 42),
                {"magnitude": 13.0, "unit": "watt_hour"},
            ),
        ]
        datapoints = generate_datapoints(data)
        output = [(time, data) async for (time, data) in cleaner(datapoints)]
        assert len(output) == 2
        assert output[0][0] == datetime.datetime(2020, 4, 1, 12, 23, 42)
        assert output[0][1] == pytest.approx(22.7848, 0.001)
        assert output[1][0] == datetime.datetime(2020, 4, 1, 13, 23, 42)
        assert output[1][1] == pytest.approx(3, 0.001)

    @pytest.mark.asyncio
    async def test_None_ignored(self, cleaner):
        data = [
            (
                datetime.datetime(2020, 4, 1, 12, 0, 0),
                {"magnitude": 1.0, "unit": "watt_hour"},
            ),
            (datetime.datetime(2020, 4, 1, 12, 58, 0), None,),
            (
                datetime.datetime(2020, 4, 1, 13, 0, 0),
                {"magnitude": 10.0, "unit": "watt_hour"},
            ),
        ]
        datapoints = generate_datapoints(data)
        output = [(time, data) async for (time, data) in cleaner(datapoints)]
        assert len(output) == 1
        assert output[0][0] == datetime.datetime(2020, 4, 1, 13, 0, 0)
        assert output[0][1] == pytest.approx(9.0, 0.0001)

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_performance_of_cleaner(self, cleaner, huge_data_set):
        import cProfile

        # Generate data point objects before profiling starts
        datapoints = await consume(generate_datapoints(huge_data_set))
        profiler = cProfile.Profile()
        profiler.enable()

        # Run the cleaner to completion
        await consume(cleaner(datapoints))

        profiler.disable()
        cleaner_stat = [
            stat for stat in profiler.getstats() if stat.code == cleaner.__code__
        ][0]
        # Assert that the cleaner may take no more than 0.5 seconds to process
        # these 50k data points
        assert cleaner_stat.totaltime < 0.5


class TestTemperatureMap:
    @pytest.fixture
    def temperature_data(self):
        return {
            (53.8667, -1.3333): -1,
            (53.35, -2.2833): 1,
            (52.45, -1.7333): 3,
            (51.5, -0.1333): 6,
            (51.55, -2.5667): 5,
            (54.9667, -1.6167): -1,
            (55.9667, -3.2167): -1,
            (54.7667, -1.5833): 0,
            (53.7667, -0.3): 1,
            (53.7667, -3.0167): 0,
            (51.4833, -3.1833): 4,
            (53.2667, -3.5167): 2,
            (52.0833, -2.8): 2,
            (52.0167, -0.6): 2,
            (52.6667, 1.2667): 5,
            (50.4333, -4.9833): 9,
            (50.35, -4.1167): 10,
            (50.5167, -2.45): 9,
            (50.8333, -1.1667): 9,
            (56.45, -5.4333): 4,
            (57.5333, -4.05): -2,
            (54.5167, -3.6167): 3,
            (53.0833, 0.2667): 4,
            (51.35, 1.3333): 7,
            (50.8833, 0.3167): 8,
            (58.45, -3.1): 3,
            (50.1, -5.6667): 9,
            (58.2167, -6.3333): 4,
            (55.6833, -6.25): 7,
        }

    @pytest.fixture
    def temperature_datapoints(self, migrated_db, db_session, temperature_data):
        datas = []
        now = datetime.datetime.now()
        for (coord, temp) in temperature_data.items():
            deployment_id = uuid.uuid4()
            datas.append(
                DataPoint(
                    sensor_name="Location",
                    deployment_id=deployment_id,
                    collected_at=now,
                    data=coord,
                )
            )
            datas.append(
                DataPoint(
                    sensor_name="Temperature",
                    deployment_id=deployment_id,
                    collected_at=now,
                    data=temp,
                )
            )
        return datas

    @pytest.fixture
    def populated_db(self, migrated_db, db_session, temperature_datapoints):
        for data in temperature_datapoints:
            insert = datapoint_table.insert().values(**data._asdict())
            db_session.execute(insert)

    @pytest.fixture
    def cleaner(self):
        return analysis.get_map_cleaner_for("Temperature")

    @pytest.fixture
    def get_data(self, db_session):
        db_session_var.set(db_session)
        return analysis.get_all_data()

    @pytest.mark.asyncio
    async def test_latest_coord_temp_cleaner(
        self, temperature_data, populated_db, get_data, cleaner
    ):
        data = get_data()
        deployments = 0
        async for deployment, data_points in data:
            deployments += 1
            cleaned = {a async for a in cleaner(data_points)}
        # There should only be one deployment
        assert deployments == 1
        expected = set(temperature_data.items())
        assert cleaned == expected

    @pytest.mark.asyncio
    async def test_newer_items_superceed_older(
        self, db_session, temperature_datapoints, populated_db, get_data, cleaner
    ):
        # Pick any of the deployment ids and find the pair of DataPoints in that deployment id
        deployment_1 = temperature_datapoints[0].deployment_id
        existing = [
            datapoint
            for datapoint in temperature_datapoints
            if datapoint.deployment_id == deployment_1
        ]
        old_location = [
            datapoint for datapoint in existing if datapoint.sensor_name == "Location"
        ][0]
        old_temperature = [
            datapoint
            for datapoint in existing
            if datapoint.sensor_name == "Temperature"
        ][0]

        new_location = DataPoint(
            sensor_name="Location",
            deployment_id=deployment_1,
            collected_at=datetime.datetime(2031, 4, 1, 12, 0, 0),
            data=(-10.5, 150.1),
        )
        new_temperature = DataPoint(
            sensor_name="Temperature",
            deployment_id=deployment_1,
            collected_at=datetime.datetime(2031, 4, 1, 12, 0, 0),
            data=21,
        )
        for data in [new_location, new_temperature]:
            insert = datapoint_table.insert().values(**data._asdict())
            db_session.execute(insert)

        data = get_data()
        deployments = 0
        async for deployment, data_points in data:
            deployments += 1
            cleaned = {a async for a in cleaner(data_points)}
        # There should only be one deployment
        assert deployments == 1

        # We expect the newer one, not the older
        assert (new_location.data, new_temperature.data) in cleaned
        assert (old_location.data, old_temperature.data) not in cleaned
        # The cleaner converts two data points to one plottable
        assert len(cleaned) == len(temperature_datapoints) / 2


def test_deprecation_warning_raised_by_config_with_no_getdata():
    with warnings.catch_warnings(record=True) as captured_warnings:
        warnings.simplefilter("always", DeprecationWarning)
        analysis.Config(
            sensor_name="Temperature",
            clean=analysis.clean_passthrough,
            title="Temperaure",
            ylabel="Deg C",
        )
        assert len(captured_warnings) == 1
        deprecation_warning = captured_warnings[0]
        assert deprecation_warning.filename == __file__
        assert deprecation_warning.category == DeprecationWarning
        assert str(deprecation_warning.message) == (
            "The sensor_name parameter is deprecated. Please pass "
            "get_data=get_one_sensor_by_deployment('Temperature') "
            "to ensure the same behaviour. The sensor_name= parameter "
            "will be removed in apd.aggregation 3.0."
        )
