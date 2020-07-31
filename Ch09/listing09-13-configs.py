import dataclasses
import datetime
import typing as t


# Additional functions in main codebase

@dataclasses.dataclass(frozen=True)
class Config:
    title: str
    sensor_name: str
    clean: t.Callable[[t.AsyncIterator[DataPoint]], t.AsyncIterator[t.Tuple[datetime.datetime, float]]]
    ylabel: str


configs = (
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
)


def get_known_configs() -> t.Dict[str, Config]:
    return {config.title: config for config in configs}


async def plot_sensor(config: Config, plot: t.Any, location_names: t.Dict[UUID,str], **kwargs) -> t.Any:
    locations = []
    async for deployment, query_results in get_data_by_deployment(sensor_name=config.sensor_name, 
                                                                  **kwargs):
        points = [dp async for dp in config['clean'](query_results)]
        if not points:
            continue
        locations.append(deployment)
        x, y = zip(*points)
        plot.set_title(config['title'])
        plot.set_ylabel(config['ylabel'])
        plot.plot_date(x, y, "-", xdate=True)
    plot.legend([location_names.get(l, l) for l in locations])
    return plot

