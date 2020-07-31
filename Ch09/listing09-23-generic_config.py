import dataclasses
import typing as t
from uuid import UUID

from apd.aggregation.database import DataPoint



plot_key = t.TypeVar("plot_key")
plot_value = t.TypeVar("plot_value")

@dataclasses.dataclass
class Config(t.Generic[plot_key, plot_value]):
    title: str
    clean: t.Callable[
        [t.AsyncIterator[DataPoint]], t.AsyncIterator[t.Tuple[plot_key, plot_value]]
    ]
    draw: t.Optional[
        t.Callable[
            [t.Any, t.Iterable[plot_key], t.Iterable[plot_value], t.Optional[str]], None
        ]
    ] = None
    get_data: t.Optional[
        t.Callable[..., t.AsyncIterator[t.Tuple[UUID, t.AsyncIterator[DataPoint]]]]
    ] = None
    ylabel: t.Optional[str] = None
    sensor_name: dataclasses.InitVar[str] = None

    def __post_init__(self, sensor_name=None):
        if self.draw is None:
            self.draw = draw_date
        if self.get_data is None:
            if sensor_name is None:
                raise ValueError("You must specify either get_data or sensor_name")
            self.get_data = get_one_sensor_by_deployment(sensor_name)

