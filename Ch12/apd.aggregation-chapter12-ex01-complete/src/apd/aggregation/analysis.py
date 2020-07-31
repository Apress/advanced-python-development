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
import warnings

import matplotlib.pyplot as plt
from matplotlib.axes._base import _AxesBase
from matplotlib.figure import Figure
from pint import _DEFAULT_REGISTRY as ureg

from apd.aggregation.query import (
    get_data,
    get_data_by_deployment,
    with_database,
    get_deployment_by_id,
)
from apd.aggregation.database import DataPoint, deployment_table
from .utils import merc_x, merc_y, convert_temperature
from .typing import IntermediateMapData, T_key, T_value, CleanerFunc, Cleaned
from .typing import (
    CLEANED_COORD_FLOAT,
    CLEANED_DT_FLOAT,
    COORD_FLOAT_CLEANER,
    DT_FLOAT_CLEANER,
)

# Static UUID to represent aggregation of other deployments
GLOBAL = UUID("bd02526e-7619-4a59-b04b-1fafd1c262d1")


@dataclasses.dataclass
class Config(t.Generic[T_key, T_value]):
    title: str
    clean: CleanerFunc[Cleaned[T_key, T_value]]
    draw: t.Optional[
        t.Callable[
            [t.Any, t.Iterable[T_key], t.Iterable[T_value], t.Optional[str]], None
        ]
    ] = None
    get_data: t.Optional[
        t.Callable[..., t.AsyncIterator[t.Tuple[UUID, t.AsyncIterator[DataPoint]]]]
    ] = None
    ylabel: t.Optional[str] = None
    sensor_name: dataclasses.InitVar[str] = None

    def __post_init__(self, sensor_name: t.Optional[str] = None) -> None:
        if self.draw is None:
            self.draw = draw_date  # type: ignore
        if sensor_name is not None:
            warnings.warn(
                DeprecationWarning(
                    f"The sensor_name parameter is deprecated. Please pass "
                    f"get_data=get_one_sensor_by_deployment('{sensor_name}') "
                    f"to ensure the same behaviour. The sensor_name= parameter "
                    f"will be removed in apd.aggregation 3.0."
                ),
                stacklevel=3,
            )
            if self.get_data is None:
                self.get_data = get_one_sensor_by_deployment(sensor_name)
        if self.get_data is None:
            raise ValueError("You must specify a get_data function")


def draw_date(
    plot: _AxesBase,
    x: t.Iterable[datetime.datetime],
    y: t.Iterable[float],
    colour: t.Optional[str],
) -> None:
    plot.plot_date(x, y, color=colour, linestyle="-", marker="", xdate=True)


def draw_map(
    plot: _AxesBase,
    x: t.Iterable[t.Tuple[float, float]],
    y: t.Iterable[float],
    colour: t.Optional[str],
) -> None:
    lon = [merc_y(coord[0]) for coord in x]
    lat = [merc_x(coord[1]) for coord in x]

    for axis in "x", "y":
        plt.tick_params(
            axis=axis,
            which="both",
            bottom=False,
            top=False,
            left=False,
            right=False,
            labelbottom=False,
            labelleft=False,
        )

    plot.tricontourf(lat, lon, y)
    plot.plot(lat, lon, "wo", ms=3)
    plot.set_aspect(1.0)


def get_map_cleaner_for(sensor_name: str,) -> COORD_FLOAT_CLEANER:
    """Given a sensor_name that represents a float, return a coroutine that acts as a cleaner
    extracting that sensor's data keyed by the value of a Location sensor."""

    async def clean_latest_coord_and_value(
        datapoints: t.AsyncIterator[DataPoint],
    ) -> CLEANED_COORD_FLOAT:

        # We will iterate over data points and build an entry in cleaned_data
        # for each deployment. This lets newer data replace older data, as
        # datapoints is assumed to be in date order
        # IntermediateMapData is a typing hint for a dictionary with specific key/values
        cleaned_data: t.Dict[UUID, IntermediateMapData] = {}
        async for datapoint in datapoints:
            # Get the existing data for this deployment, if we've seen it before
            row_data = cleaned_data.get(datapoint.deployment_id, None)
            if row_data is None:
                # This is the first time we've seen this deployment
                row_data = {"coord": None, "value": None}
            if datapoint.sensor_name == "Location":
                # Coord is a 2-tuple of floats
                row_data["coord"] = (
                    float(datapoint.data[0]),
                    float(datapoint.data[1]),
                )
            elif datapoint.sensor_name == sensor_name:
                # Value is a single float
                row_data["value"] = float(datapoint.data)
            # Store the info about this deployment back into the cleaned_data set
            cleaned_data[datapoint.deployment_id] = row_data

        for data in cleaned_data.values():
            if data["coord"] is None or data["value"] is None:
                # We only got a partial record, don't plot this
                continue
            yield data["coord"], data["value"]

    # Return the set up cleaner coroutine
    return clean_latest_coord_and_value


async def clean_watthours_to_watts(
    datapoints: t.AsyncIterator[DataPoint],
) -> CLEANED_DT_FLOAT:
    last_watthours = None
    last_time = None
    async for datapoint in datapoints:
        if datapoint.data is None:
            continue
        time = datapoint.collected_at
        if datapoint.data["unit"] == "watt_hour":
            watt_hours = datapoint.data["magnitude"]
        else:
            watt_hours = (
                ureg.Quantity(datapoint.data["magnitude"], datapoint.data["unit"])
                .to(ureg.watt_hour)
                .magnitude
            )
        if last_watthours:
            seconds_elapsed = (time - last_time).total_seconds()
            hours_elapsed = seconds_elapsed / (60.0 * 60.0)
            additional_power = watt_hours - last_watthours
            power = additional_power / hours_elapsed
            yield time, power
        last_watthours = watt_hours
        last_time = datapoint.collected_at


async def clean_magnitude(datapoints: t.AsyncIterator[DataPoint],) -> CLEANED_DT_FLOAT:
    async for datapoint in datapoints:
        if datapoint.data is None:
            continue
        yield datapoint.collected_at, datapoint.data["magnitude"]


def convert_temperature_system(
    cleaner: DT_FLOAT_CLEANER, temperature_unit: str,
) -> DT_FLOAT_CLEANER:
    async def converter(datapoints: t.AsyncIterator[DataPoint],) -> CLEANED_DT_FLOAT:
        results = cleaner(datapoints)
        async for date, temp_c in results:
            yield date, convert_temperature(temp_c, "degC", temperature_unit)

    return converter


async def clean_temperature_fluctuations(
    datapoints: t.AsyncIterator[DataPoint],
) -> CLEANED_DT_FLOAT:
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
) -> CLEANED_DT_FLOAT:
    async for datapoint in datapoints:
        if datapoint.data is None:
            continue
        else:
            yield datapoint.collected_at, datapoint.data


def get_one_sensor_by_deployment(
    sensor_name: str,
) -> t.Callable[..., t.AsyncIterator[t.Tuple[UUID, t.AsyncIterator[DataPoint]]]]:
    return functools.partial(get_data_by_deployment, sensor_name=sensor_name)


def get_all_data() -> t.Callable[
    ..., t.AsyncIterator[t.Tuple[UUID, t.AsyncIterator[DataPoint]]]
]:
    async def get_all_data_inner(
        *args: t.Any, **kwargs: t.Any
    ) -> t.AsyncIterator[t.Tuple[UUID, t.AsyncIterator[DataPoint]]]:
        yield GLOBAL, get_data(*args, **kwargs)

    return get_all_data_inner


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


def get_known_configs() -> t.Dict[str, Config[t.Any, t.Any]]:
    return {config.title: config for config in configs}


async def plot_sensor(
    config: Config[t.Any, t.Any],
    plot: _AxesBase,
    location_names: t.Dict[UUID, str],
    **kwargs: t.Any,
) -> _AxesBase:
    locations = []
    if config.get_data is None:
        raise ValueError("You must provide a get_data function")
    async for deployment_id, query_results in config.get_data(**kwargs):
        if deployment_id == GLOBAL:
            name = "Global"
        else:
            try:
                deployment = await get_deployment_by_id(deployment_id)
            except IndexError:
                name = str(deployment_id)
                colour = None
            else:
                name = deployment.name or str(deployment_id)
                colour = deployment.colour
        # Mypy currently doesn't understand callable fields on datatypes: https://github.com/python/mypy/issues/5485
        points = [dp async for dp in config.clean(query_results)]  # type: ignore
        if not points:
            continue
        locations.append(name)
        x, y = zip(*points)
        plot.set_title(config.title)
        plot.set_ylabel(config.ylabel)
        if config.draw is None:
            raise ValueError("You must provide a get_data function")
        config.draw(plot, x, y, colour)
    plot.legend(locations)
    return plot


async def plot_multiple_charts(*args: t.Any, **kwargs: t.Any) -> Figure:
    # These parameters are pulled from kwargs to avoid confusing function
    # introspection code in IPython widgets
    location_names = kwargs.pop("location_names", None)
    configs = kwargs.pop("configs", None)
    dimensions = kwargs.pop("dimensions", None)
    db_uri = kwargs.pop("db_uri", "postgresql+psycopg2://apd@localhost/apd")

    with with_database(db_uri) as session:
        loop = asyncio.get_running_loop()
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
        if location_names is None:
            location_query = session.query(
                deployment_table.c.id, deployment_table.c.name
            )
            location_data = await loop.run_in_executor(None, location_query.all)
            location_names = dict(location_data)

        figure = plt.figure(figsize=(10 * columns, 5 * rows), dpi=300)
        for i, config in enumerate(configs, start=1):
            plot = figure.add_subplot(columns, rows, i)
            coros.append(plot_sensor(config, plot, location_names, *args, **kwargs))
        await asyncio.gather(*coros)
    return figure


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


def interactable_plot_multiple_charts(
    *args: t.Any, **kwargs: t.Any
) -> t.Callable[..., Figure]:
    with_config = functools.partial(plot_multiple_charts, *args, **kwargs)
    return wrap_coroutine(with_config)
