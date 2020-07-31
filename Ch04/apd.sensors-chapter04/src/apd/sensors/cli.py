import enum
import importlib
import sys
import pkg_resources
import typing as t

import click

from .sensors import Sensor


class ReturnCodes(enum.IntEnum):
    OK = 0
    BAD_SENSOR_PATH = 17


def get_sensor_by_path(sensor_path: str) -> Sensor[t.Any]:
    try:
        module_name, sensor_name = sensor_path.split(":")
    except ValueError:
        raise RuntimeError(
            "Sensor path must be in the format dotted.path.to.module:ClassName"
        )
    try:
        module = importlib.import_module(module_name)
    except ImportError:
        raise RuntimeError(f"Could not import module {module_name}")
    try:
        sensor_class = getattr(module, sensor_name)
    except AttributeError:
        raise RuntimeError(f"Could not find attribute {sensor_name} in {module_name}")
    if (
        isinstance(sensor_class, type)
        and issubclass(sensor_class, Sensor)
        and sensor_class != Sensor
    ):
        return sensor_class()
    else:
        raise RuntimeError(
            f"Detected object {sensor_class!r} is not recognised as a Sensor type"
        )


def get_sensors() -> t.Iterable[Sensor[t.Any]]:
    sensors = []
    for sensor_class in pkg_resources.iter_entry_points("apd.sensors.sensors"):
        class_ = sensor_class.load()
        sensors.append(t.cast(Sensor[t.Any], class_()))
    return sensors


@click.command(help="Displays the values of the sensors")
@click.option(
    "--develop", required=False, metavar="path", help="Load a sensor by Python path"
)
def show_sensors(develop: str) -> None:
    sensors: t.Iterable[Sensor[t.Any]]
    if develop:
        try:
            sensors = [get_sensor_by_path(develop)]
        except RuntimeError as error:
            click.secho(str(error), fg="red", bold=True)
            sys.exit(ReturnCodes.BAD_SENSOR_PATH)
    else:
        sensors = get_sensors()
    for sensor in sensors:
        click.secho(sensor.title, bold=True)
        click.echo(str(sensor))
        click.echo("")
    sys.exit(ReturnCodes.OK)


if __name__ == "__main__":
    show_sensors()
