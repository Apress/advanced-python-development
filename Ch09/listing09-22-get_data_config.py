@dataclasses.dataclass
class Config:
    title: str
    clean: t.Callable[[t.AsyncIterator[DataPoint]], t.AsyncIterator[t.Tuple[datetime.datetime, float]]]
    get_data: t.Optional[
        t.Callable[..., t.AsyncIterator[t.Tuple[UUID, t.AsyncIterator[DataPoint]]]]
    ] = None
    ylabel: str
    sensor_name: dataclasses.InitVar[str] = None

    def __post_init__(self, sensor_name=None):
        if self.get_data is None:
            if sensor_name is None:
                raise ValueError("You must specify either get_data or sensor_name")
            self.get_data = get_one_sensor_by_deployment(sensor_name)

def get_one_sensor_by_deployment(sensor_name):
    return functools.partial(get_data_by_deployment, sensor_name=sensor_name)

