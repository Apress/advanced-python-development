import asyncio
import typing as t
import uuid

import aiohttp
import click
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from . import collect
from .database import Deployment, deployment_table


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
            collect.standalone(db, attempt, api_key, echo=verbose)
        except ValueError as e:
            click.secho(str(e), err=True, fg="red")
            success = False
    return success


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
