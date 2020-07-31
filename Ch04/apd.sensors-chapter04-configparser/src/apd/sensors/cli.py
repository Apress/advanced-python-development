import configparser
import enum
import importlib
import sys
import typing as t

import click

from .sensors import Sensor


class ReturnCodes(enum.IntEnum):
    OK = 0
    BAD_SENSOR_PATH = 17
    BAD_CONFIG = 18


def parse_config_file(
    path: t.Union[str, t.Iterable[str]]
) -> t.Dict[str, t.Dict[str, str]]:
    parser = configparser.ConfigParser()
    parser.read(path, encoding="utf-8")
    try:
        plugin_names = [
            name for name in parser.get("config", "plugins").split() if name
        ]
    except configparser.NoSectionError:
        raise RuntimeError(f"Could not find [config] section in file")
    except configparser.NoOptionError:
        raise RuntimeError(f"Could not find plugins line in [config] section")
    plugin_data = {}
    for plugin_name in plugin_names:
        try:
            plugin_data[plugin_name] = dict(parser.items(plugin_name))
        except configparser.NoSectionError:
            raise RuntimeError(f"Could not find [{plugin_name}] section in file")
    return plugin_data


def get_sensor_by_path(sensor_path: str, **kwargs) -> Sensor[t.Any]:
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
        try:
            return sensor_class(**kwargs)
        except TypeError as error:
            message = str(error)
            if "got an unexpected" in message:
                raise RuntimeError(f"Sensor {sensor_name} " + message.split(" ", 1)[1])
            raise
    else:
        raise RuntimeError(
            f"Detected object {sensor_class!r} is not recognised as a Sensor type"
        )


def get_sensors(path: str) -> t.Iterable[Sensor[t.Any]]:
    sensors = []
    for plugin_name, sensor_data in parse_config_file(path).items():
        try:
            class_path = sensor_data.pop("plugin")
        except TypeError:
            raise RuntimeError(
                f"Could not find plugin= line in [{plugin_name}] section"
            )
        sensors.append(get_sensor_by_path(class_path, **sensor_data))
    return sensors


@click.command(help="Displays the values of the sensors")
@click.option(
    "--develop", required=False, metavar="path", help="Load a sensor by Python path"
)
@click.option(
    "--config",
    required=False,
    default="config.cfg",
    metavar="config_path",
    help="Load the specified configuration file",
)
def show_sensors(develop: str, config: str) -> None:
    sensors: t.Iterable[Sensor[t.Any]]
    if develop:
        try:
            sensors = [get_sensor_by_path(develop)]
        except RuntimeError as error:
            click.secho(str(error), fg="red", bold=True)
            sys.exit(ReturnCodes.BAD_SENSOR_PATH)
    else:
        try:
            sensors = get_sensors(config)
        except RuntimeError as error:
            click.secho(str(error), fg="red", bold=True)
            sys.exit(ReturnCodes.BAD_CONFIG)
    for sensor in sensors:
        click.secho(sensor.title, bold=True)
        click.echo(str(sensor))
        click.echo("")
    sys.exit(ReturnCodes.OK)


if __name__ == "__main__":
    show_sensors()
