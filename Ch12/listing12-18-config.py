import operator

from apd.aggregation.actions.action import (
    OnlyOnChangeActionWrapper,
    LoggingAction,
)
from apd.aggregation.actions.runner import DataProcessor
from apd.aggregation.actions.trigger import ValueThresholdTrigger

handlers = [
    DataProcessor(
        name="TemperatureBelow18",
        action=OnlyOnChangeActionWrapper(LoggingAction()),
        trigger=ValueThresholdTrigger(
            name="TemperatureBelow18",
            threshold=18,
            comparator=operator.lt,
            sensor_name="Temperature",
        ),
    )
]

