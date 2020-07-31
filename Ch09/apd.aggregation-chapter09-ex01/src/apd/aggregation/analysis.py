from __future__ import annotations

import collections
import dataclasses
import datetime
import typing as t
from uuid import UUID

from matplotlib.axes._base import _AxesBase

from apd.aggregation.query import get_data_by_deployment
from apd.aggregation.database import DataPoint


@dataclasses.dataclass(frozen=True)
class Config:
    title: str
    sensor_name: str
    clean: t.Callable[
        [t.AsyncIterator[DataPoint]], t.AsyncIterator[t.Tuple[datetime.datetime, float]]
    ]
    ylabel: str


async def clean_watthours_to_watts(
    datapoints: t.AsyncIterator[DataPoint],
) -> t.AsyncIterator[t.Tuple[datetime.datetime, float]]:
    async for date, data in clean_magnitude(datapoints):
        yield (date, data)


async def clean_magnitude(
    datapoints: t.AsyncIterator[DataPoint],
) -> t.AsyncIterator[t.Tuple[datetime.datetime, float]]:
    async for datapoint in datapoints:
        if datapoint.data is None:
            continue
        yield datapoint.collected_at, datapoint.data["magnitude"]


async def clean_temperature_fluctuations(
    datapoints: t.AsyncIterator[DataPoint],
) -> t.AsyncIterator[t.Tuple[datetime.datetime, float]]:
    allowed_jitter = 2.5
    allowed_range = (-40, 80)
    window_datapoints: t.Deque[DataPoint] = collections.deque(maxlen=3)

    def datapoint_ok(datapoint: DataPoint) -> bool:
        """Return False if this data point does not contain a valid temperature"""
        if datapoint.data is None:
            return False
        elif datapoint.data["unit"] != "degC":
            # This point is in a different temperature system. While it could be converted
            # this cleaner is not yet doing that.
            return False
        elif not allowed_range[0] < datapoint.data["magnitude"] < allowed_range[1]:
            return False
        return True

    async for datapoint in datapoints:
        if not datapoint_ok(datapoint):
            # If the datapoint is invalid then skip directly to the next item
            continue

        window_datapoints.append(datapoint)
        if len(window_datapoints) == 3:
            # Find the temperatures of the datapoints in the window, then average
            # the first and last and compare that to the middle point.
            window_temperatures = [dp.data["magnitude"] for dp in window_datapoints]
            avr_first_last = (window_temperatures[0] + window_temperatures[2]) / 2
            diff_middle_avr = abs(window_temperatures[1] - avr_first_last)
            if diff_middle_avr > allowed_jitter:
                pass
            else:
                yield window_datapoints[1].collected_at, window_temperatures[1]
        elif len(window_datapoints) == 1:
            # The item in the iterator can't be compared to both neighbours
            # so should be yielded
            yield datapoint.collected_at, datapoint.data["magnitude"]
        else:
            # Otherwise, let the window fill up, it will be yieleded later
            pass
    # When the iterator ends the final item is not yet in the middle
    # of the window, so the last item must be explicitly yielded.
    if len(window_datapoints) > 1 and datapoint_ok(datapoint):
        yield datapoint.collected_at, datapoint.data["magnitude"]


async def clean_passthrough(
    datapoints: t.AsyncIterator[DataPoint],
) -> t.AsyncIterator[t.Tuple[datetime.datetime, float]]:
    async for datapoint in datapoints:
        if datapoint.data is None:
            continue
        else:
            yield datapoint.collected_at, datapoint.data


configs = (
    Config(
        sensor_name="SolarCumulativeOutput",
        clean=clean_watthours_to_watts,
        title="Solar generation",
        ylabel="Watts",
    ),
    Config(
        sensor_name="RAMAvailable",
        clean=clean_passthrough,
        title="RAM available",
        ylabel="Bytes",
    ),
    Config(
        sensor_name="RelativeHumidity",
        clean=clean_passthrough,
        title="Relative humidity",
        ylabel="Percent",
    ),
    Config(
        sensor_name="Temperature",
        clean=clean_temperature_fluctuations,
        title="Ambient temperature",
        ylabel="Degrees C",
    ),
)


def get_known_configs():
    return {config.title: config for config in configs}


async def plot_sensor(
    config: Config, plot: _AxesBase, location_names: t.Dict[UUID, str], **kwargs
):
    locations = []
    async for deployment, query_results in get_data_by_deployment(
        sensor_name=config.sensor_name, **kwargs
    ):
        # Mypy currently doesn't understand callable fields on datatypes: https://github.com/python/mypy/issues/5485
        points = [dp async for dp in config.clean(query_results)]  # type: ignore
        if not points:
            continue
        locations.append(deployment)
        x, y = zip(*points)
        plot.set_title(config.title)
        plot.set_ylabel(config.ylabel)
        plot.plot_date(x, y, f"-", xdate=True)
    plot.legend([location_names.get(l, l) for l in locations])
    return plot
