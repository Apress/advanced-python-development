import sys
import traceback
import typing as t

import click


@click.command(help="Displays the values of the sensors")
@click.option(
    "--develop", required=False, metavar="path", help="Load a sensor by Python path"
)
@click.option(
    "--verbose", is_flag=True, help="Show additional info"
)
def show_sensors(develop: str, verbose: bool) -> int:
    sensors: t.Iterable[Sensor[t.Any]]
    if develop:
        try:
            sensors = [get_sensor_by_path(develop)]
        except UserFacingCLIError as error:
            if verbose:
                tb = traceback.format_exception(type(error), error, error.__traceback__)
                click.echo("".join(tb))
            click.secho(error.message, fg="red", bold=True)
            sys.exit(error.return_code)
    else:
        sensors = get_sensors()
    for sensor in sensors:
        click.secho(sensor.title, bold=True)
        try:
            click.echo(str(sensor))
        except DataCollectionError as error:
            if verbose:
                tb = traceback.format_exception(type(error), error, error.__traceback__)
                click.echo("".join(tb))
                continue
            click.echo(error)
        click.echo("")
    return 0

