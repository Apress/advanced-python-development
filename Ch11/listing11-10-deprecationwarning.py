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

