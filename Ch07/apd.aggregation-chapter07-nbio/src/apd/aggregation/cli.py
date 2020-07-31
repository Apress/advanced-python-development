import typing as t

import click

from .collect import standalone


@click.command()
@click.argument("server", nargs=-1)
@click.option(
    "--db",
    metavar="<CONNECTION_STRING>",
    default="postgresql+psycopg2://localhost/apd",
    help="The connection string to a PostgreSQL database",
    envvar="APD_DB_URI",
)
@click.option("--api-key", metavar="<KEY>", envvar="APD_API_KEY")
@click.option(
    "--tolerate-failures",
    "-f",
    help="If provided, failure to retrieve some sensors' data will not abort the collection process",
    is_flag=True,
)
@click.option("-v", "--verbose", is_flag=True, help="Enables verbose mode")
def collect_sensor_data(
    db: str, server: t.Tuple[str], api_key: str, tolerate_failures: bool, verbose: bool
):
    """This loads data from one or more sensors into the specified database.

    Only PostgreSQL databases are supported, as the column definitions use
    multiple pg specific features. The database must already exist and be
    populated with the required tables.

    The --api-key option is used to specify the access token for the sensors
    being queried.

    You may specify any number of servers, the variable should be the full URL
    to the sensor's HTTP interface, not including the /v/2.0 portion. Multiple
    URLs should be separated with a space.
    """
    if tolerate_failures:
        attempts = [(s,) for s in server]
    else:
        attempts = [server]
    success = True
    for attempt in attempts:
        try:
            standalone(db, attempt, api_key, echo=verbose)
        except ValueError as e:
            click.secho(str(e), err=True, fg="red")
            success = False
    return success
