import contextlib
from contextvars import ContextVar
import functools
import typing as t

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import Session

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
    try:
        yield Session
        Session.commit()
    finally:
        db_session_var.reset(token)
        Session.close()

