import collections
import datetime
import typing as t

from apd.aggregation.database import DataPoint


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
        if len(three_temperatures) == 3:
            # Find the temperatures of the datapoints in the window, then average
            # the first and last and compare that to the middle point.
            window_temperatures = [dp.data["magnitude"] for dp in window_datapoints]
            avg_first_last = (window_temperatures[0] + window_temperatures[2]) / 2
            diff_middle_avg = abs(window_temperatures[1] - avg_first_last)
            if diff_middle_avg > allowed_jitter:
                pass
            else:
                yield window_datapoints[1].collected_at, window_temperatures[1]
        else:
            # The first two items in the iterator can't be compared to both neighbours
            # so they should be yielded
            yield datapoint.collected_at, datapoint.data["magnitude"]
    # When the iterator ends the final item is not yet in the middle
    # of the window, so the last item must be explicitly yielded
    if datapoint_ok(datapoint):
        yield datapoint.collected_at, datapoint.data["magnitude"]

