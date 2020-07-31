import asyncio
import importlib.util
import logging
import typing as t

import click

from .actions.runner import DataProcessor
from .actions.source import get_data_ongoing
from .query import with_database

logger = logging.getLogger(__name__)


def load_handler_config(path: str) -> t.List[DataProcessor]:
    # Create a module called user_config backed by the file specified, and load it
    # This uses Python's import internals to fake a module in a known location
    # Based on an StackOverflow answer by Sebastian Rittau and sample code from
    # Brett Cannon
    module_spec = importlib.util.spec_from_file_location("user_config", path)
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module.handlers


@click.command()
@click.argument("config", nargs=1)
@click.option(
    "--db",
    metavar="<CONNECTION_STRING>",
    default="postgresql+psycopg2://localhost/apd",
    help="The connection string to a PostgreSQL database",
    envvar="APD_DB_URI",
)
@click.option("-v", "--verbose", is_flag=True, help="Enables verbose mode")
def run_actions(config: str, db: str, verbose: bool) -> t.Optional[int]:
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
            data = get_data_ongoing()
            async for datapoint in data:
                for handler in handlers:
                    await handler.push(datapoint)

    asyncio.run(main_loop())
    return True

