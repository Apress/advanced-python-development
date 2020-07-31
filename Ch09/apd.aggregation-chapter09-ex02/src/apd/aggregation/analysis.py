from __future__ import annotations

import asyncio
import collections
from concurrent.futures import ThreadPoolExecutor
import dataclasses
import datetime
import functools
import math
import typing as t
from uuid import UUID

import matplotlib.pyplot as plt
from matplotlib.axes._base import _AxesBase
from matplotlib.figure import Figure
from pint import _DEFAULT_REGISTRY as ureg

from apd.aggregation.query import get_data_by_deployment, with_database
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
    last_watthours = None
    last_time = None
    async for datapoint in datapoints:
        if datapoint.data is None:
            continue
        time = datapoint.collected_at
        watthours = ureg.Quantity(datapoint.data["magnitude"], datapoint.data["unit"])
        if last_watthours:
            seconds_elapsed = (time - last_time).total_seconds()
            time_elapsed = ureg.Quantity(seconds_elapsed, ureg.second)
            additional_power = watthours - last_watthours
            power = additional_power / time_elapsed
            yield time, power.to(ureg.watt).magnitude
        last_watthours = watthours
        last_time = datapoint.collected_at


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


def get_known_configs() -> t.Dict[str, Config]:
    return {config.title: config for config in configs}


async def plot_sensor(
    config: Config, plot: _AxesBase, location_names: t.Dict[UUID, str], **kwargs: t.Any
) -> _AxesBase:
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


_Coroutine_Result = t.TypeVar("_Coroutine_Result")


def wrap_coroutine(
    f: t.Callable[..., t.Coroutine[t.Any, t.Any, _Coroutine_Result]]
) -> t.Callable[..., _Coroutine_Result]:
    """Given a coroutine, return a function that runs that coroutine
    in a new event loop in an isolated thread"""

    @functools.wraps(f)
    def run_in_thread(*args: t.Any, **kwargs: t.Any) -> _Coroutine_Result:
        loop = asyncio.new_event_loop()
        wrapped = f(*args, **kwargs)
        with ThreadPoolExecutor(max_workers=1) as pool:
            task = pool.submit(loop.run_until_complete, wrapped)
        # Mypy can get confused when nesting generic functions, like we do here
        # The fact that Task is generic means we lose the association with
        # _CoroutineResult. Adding an explicit cast restores this.
        return t.cast(_Coroutine_Result, task.result())

    return run_in_thread


async def plot_multiple_charts(*args: t.Any, **kwargs: t.Any) -> Figure:
    # These parameters are pulled from kwargs to avoid confusing function
    # introspection code in IPython widgets
    location_names = kwargs.pop("location_names", None)
    configs = kwargs.pop("configs", None)
    dimensions = kwargs.pop("dimensions", None)

    with with_database("postgresql+psycopg2://apd@localhost/apd"):
        coros = []
        if configs is None:
            # If no configs are supplied, use all known configs
            configs = get_known_configs().values()
        if dimensions is None:
            # If no dimensions are supplied, get the square root of the number
            # of configs and round it to find a number of columns. This will
            # keep the arrangement approximately square. Find rows by multiplying
            # out rows.
            total_configs = len(configs)
            columns = round(math.sqrt(total_configs))
            rows = math.ceil(total_configs / columns)
        figure = plt.figure(figsize=(10 * columns, 5 * rows), dpi=300)
        for i, config in enumerate(configs, start=1):
            plot = figure.add_subplot(columns, rows, i)
            coros.append(plot_sensor(config, plot, location_names, *args, **kwargs))
        await asyncio.gather(*coros)
    return figure


def interactable_plot_multiple_charts(
    *args: t.Any, **kwargs: t.Any
) -> t.Callable[..., Figure]:
    with_config = functools.partial(plot_multiple_charts, *args, **kwargs)
    return wrap_coroutine(with_config)
