import functools
import importlib
import typing as t

import click

from .sensors import (
    Sensor,
    ACStatus,
    CPULoad,
    IPAddresses,
    PythonVersion,
    RAMAvailable,
    RelativeHumidity,
    Temperature,
)


RETURN_CODES = {"OK": 0, "BAD_SENSOR_PATH": 17}


class PythonClass(click.types.ParamType):
    name = "pythonclass"

    def __init__(self, superclass=type):
        self.superclass = superclass

    def get_sensor_by_path(
        self, sensor_path: str, fail: t.Callable[[str], None]
    ) -> t.Any:
        try:
            module_name, sensor_name = sensor_path.split(":")
        except ValueError:
            return fail(
                "Class path must be in the format dotted.path.to.module:ClassName"
            )
        try:
            module = importlib.import_module(module_name)
        except ImportError:
            return fail(f"Could not import module {module_name}")
        try:
            sensor_class = getattr(module, sensor_name)
        except AttributeError:
            return fail(f"Could not find attribute {sensor_name} in {module_name}")
        if (
            isinstance(sensor_class, type)
            and issubclass(sensor_class, self.superclass)
            and sensor_class != self.superclass
        ):
            return sensor_class
        else:
            return fail(
                f"Detected object {sensor_class!r} is"
                f" not recognised as a {self.superclass.__name__} type"
            )

    def convert(
        self,
        value: str,
        param: t.Optional[click.core.Parameter],
        ctx: t.Optional[click.core.Context],
    ) -> t.Any:
        fail = functools.partial(self.fail, param=param, ctx=ctx)
        return self.get_sensor_by_path(value, fail)

    def __repr__(self):
        return "PythonClass"


def get_sensors() -> t.Iterable[Sensor[t.Any]]:
    return [
        PythonVersion(),
        IPAddresses(),
        CPULoad(),
        RAMAvailable(),
        ACStatus(),
        Temperature(),
        RelativeHumidity(),
    ]


@click.command(help="Displays the values of the sensors")
@click.option(
    "--develop",
    required=False,
    metavar="path",
    help="Load a sensor by Python path",
    type=PythonClass(Sensor),
)
def show_sensors(develop: t.Callable[[], Sensor[t.Any]]) -> int:
    sensors: t.Iterable[Sensor[t.Any]]
    if develop:
        sensors = [develop()]
    else:
        sensors = get_sensors()
    for sensor in sensors:
        click.secho(sensor.title, bold=True)
        click.echo(str(sensor))
        click.echo("")
    return RETURN_CODES["OK"]


if __name__ == "__main__":
    show_sensors()
