import asyncio
import contextlib
from contextvars import ContextVar
import typing as t

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import Session


from apd.aggregation.collect import datapoint_table, DataPoint


db_session_var: ContextVar[Session] = ContextVar("db_session")


@contextlib.contextmanager
def with_database(uri: t.Optional[str] = None) -> t.Iterator[Session]:
    """Given a URI, set up a DB connection, and return a Session as a context manager """
    if uri is None:
        uri = "postgresql+psycopg2://localhost/apd"
    engine = create_engine(uri)
    sm = sessionmaker(engine)
    Session = sm()
    token = db_session_var.set(Session)
    yield Session
    db_session_var.reset(token)
    Session.commit()
    Session.close()


async def get_data() -> t.AsyncIterator[DataPoint]:
    db_session = db_session_var.get()
    loop = asyncio.get_running_loop()
    query = db_session.query(datapoint_table)
    rows = await loop.run_in_executor(None, query.all)
    for row in rows:
        yield DataPoint.from_sql_result(row)
