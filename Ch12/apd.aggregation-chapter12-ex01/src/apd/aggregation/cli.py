import asyncio
import functools
import importlib.util
import logging
import signal
import typing as t
import uuid

import aiohttp
import click
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from . import collect
from .actions.runner import DataProcessor
from .actions.source import get_data_ongoing
from .database import Deployment, deployment_table
from .query import with_database

logger = logging.getLogger(__name__)


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
) -> t.Optional[int]:
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
            collect.standalone(db, attempt, api_key, echo=verbose)
        except ValueError as e:
            click.secho(str(e), err=True, fg="red")
            success = False
    return success


def load_handler_config(path: str) -> t.List[DataProcessor]:
    # Create a module called user_config backed by the file specified, and load it
    # This uses Python's import internals to fake a module in a known location
    # Based on an SO answer by Sebastian Rittau and sample code from Brett Cannon
    module_spec = importlib.util.spec_from_file_location("user_config", path)
    module = importlib.util.module_from_spec(module_spec)
    loader = module_spec.loader
    if isinstance(loader, importlib.abc.Loader):
        loader.exec_module(module)
        try:
            return module.handlers  # type: ignore
        except AttributeError as err:
            raise ValueError(f"Could not load config file from {path}") from err
    else:
        # No valid loader could be found
        raise ValueError(f"Could not load config file from {path}")


def stats_signal_handler(sig, frame, original_sigint_handler=None, handlers=None):
    for handler in handlers:
        click.echo(
            click.style(handler.name, bold=True, fg="red") + " " + handler.stats()
        )
    if sig == signal.SIGINT:
        click.secho("Press Ctrl+C again to end the process", bold=True)
        handler = signal.getsignal(signal.SIGINT)
        signal.signal(signal.SIGINT, original_sigint_handler)
        asyncio.get_running_loop().call_later(5, install_ctrl_c_signal_handler, handler)
    return


def install_ctrl_c_signal_handler(signal_handler):
    click.secho("Press Ctrl+C to view statistics", bold=True)
    signal.signal(signal.SIGINT, signal_handler)


@click.command()
@click.argument("config", nargs=1)
@click.option(
    "--db",
    metavar="<CONNECTION_STRING>",
    default="postgresql+psycopg2://localhost/apd",
    help="The connection string to a PostgreSQL database",
    envvar="APD_DB_URI",
)
@click.option(
    "--historical",
    is_flag=True,
    help="Also trigger actions for data points that were already present in the database",
)
@click.option("-v", "--verbose", is_flag=True, help="Enables verbose mode")
def run_actions(
    config: str, db: str, verbose: bool, historical: bool
) -> t.Optional[int]:
    """This runs the long-running action processors defined in a config file.

    The configuration file specified should be a Python file that defines a
    list of DataProcessor objects called processors.n
    """
    logging.basicConfig(level=logging.DEBUG if verbose else logging.WARN)

    async def main_loop():
        with with_database(db):
            logger.info("Loading configuration")
            handlers = load_handler_config(config)

            logger.info(f"Configured {len(handlers)} handlers")
            starters = [handler.start() for handler in handlers]
            await asyncio.gather(*starters)

            logger.info(f"Ingesting data")
            data = get_data_ongoing(historical=historical)

            original_sigint_handler = signal.getsignal(signal.SIGINT)
            signal_handler = functools.partial(
                stats_signal_handler,
                handlers=handlers,
                original_sigint_handler=original_sigint_handler,
            )

            for signal_name in "SIGINFO", "SIGUSR1", "SIGINT":
                try:
                    signal.signal(signal.signals[signal_name], signal_handler)
                except AttributeError:
                    pass

            async for datapoint in data:
                for handler in handlers:
                    await handler.push(datapoint)

    asyncio.run(main_loop())
    return True


@click.group()
def deployments():
    pass


@deployments.command()
@click.argument("uri")
@click.argument("name")
@click.option(
    "--db",
    metavar="<CONNECTION_STRING>",
    default="postgresql+psycopg2://localhost/apd",
    help="The connection string to a PostgreSQL database",
    envvar="APD_DB_URI",
)
@click.option("--api-key", metavar="<KEY>", envvar="APD_API_KEY")
@click.option("--colour")
def add(
    db: str, uri: str, name: str, api_key: t.Optional[str], colour: t.Optional[str],
):
    """This creates a record of a new deployment in the database.
    """
    deployment = Deployment(id=None, uri=uri, name=name, api_key=api_key, colour=colour)

    async def http_get_deployment_id():
        async with aiohttp.ClientSession() as http:
            collect.http_session_var.set(http)
            return await collect.get_deployment_id(uri)

    deployment.id = asyncio.run(http_get_deployment_id())
    insert = deployment_table.insert().values(**deployment._asdict())

    engine = create_engine(db)
    sm = sessionmaker(engine)
    Session = sm()
    Session.execute(insert)
    Session.commit()
    return True


@deployments.command()
@click.option(
    "--db",
    metavar="<CONNECTION_STRING>",
    default="postgresql+psycopg2://localhost/apd",
    help="The connection string to a PostgreSQL database",
    envvar="APD_DB_URI",
)
def list(db: str):
    """This creates a record of a new deployment in the database.
    """
    engine = create_engine(db)
    sm = sessionmaker(engine)
    Session = sm()
    deployments = Session.query(deployment_table).all()
    for deployment in deployments:
        click.secho(deployment.name, bold=True)
        click.echo(click.style("ID ", bold=True) + deployment.id.hex)
        click.echo(click.style("URI ", bold=True) + deployment.uri)
        click.echo(click.style("API key ", bold=True) + deployment.api_key)
        click.echo(click.style("Colour ", bold=True) + str(deployment.colour))
        click.echo()
    Session.rollback()
    return True


@deployments.command()
@click.argument("id")
@click.option("--uri")
@click.option("--name")
@click.option(
    "--db",
    metavar="<CONNECTION_STRING>",
    default="postgresql+psycopg2://localhost/apd",
    help="The connection string to a PostgreSQL database",
    envvar="APD_DB_URI",
)
@click.option("--api-key", metavar="<KEY>", envvar="APD_API_KEY")
@click.option("--colour")
def edit(
    db: str,
    id,
    uri: t.Optional[str],
    name: t.Optional[str],
    api_key: t.Optional[str],
    colour: t.Optional[str],
):
    """This creates a record of a new deployment in the database.
    """
    update = {}
    if uri is not None:
        update["uri"] = uri
    if name is not None:
        update["name"] = name
    if api_key is not None:
        update["api_key"] = api_key
    if colour is not None:
        update["colour"] = colour
    deployment_id = uuid.UUID(id)

    update_stmt = (
        deployment_table.update()
        .where(deployment_table.c.id == deployment_id)
        .values(**update)
    )

    engine = create_engine(db)
    sm = sessionmaker(engine)
    Session = sm()
    Session.execute(update_stmt)
    deployments = Session.query(deployment_table).filter(
        deployment_table.c.id == deployment_id
    )
    Session.commit()

    for deployment in deployments:
        click.secho(deployment.name, bold=True)
        click.echo(click.style("ID ", bold=True) + deployment.id.hex)
        click.echo(click.style("URI ", bold=True) + deployment.uri)
        click.echo(click.style("API key ", bold=True) + deployment.api_key)
        click.echo(click.style("Colour ", bold=True) + str(deployment.colour))
        click.echo()

    return True
