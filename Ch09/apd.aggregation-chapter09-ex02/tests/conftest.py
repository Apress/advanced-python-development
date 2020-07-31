import datetime
from uuid import UUID

from apd.aggregation.database import datapoint_table

from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.runtime.environment import EnvironmentContext
import pytest


@pytest.fixture
def db_uri():
    return "postgresql+psycopg2://apd@localhost/apd-test"


@pytest.fixture
def db_session(db_uri):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(db_uri, echo=True)
    sm = sessionmaker(engine)
    Session = sm()
    yield Session
    Session.close()


@pytest.fixture
def migrated_db(db_uri, db_session):
    config = Config()
    config.set_main_option("script_location", "apd.aggregation:alembic")
    config.set_main_option("sqlalchemy.url", db_uri)
    script = ScriptDirectory.from_config(config)

    def upgrade(rev, context):
        return script._upgrade_revs(script.get_current_head(), rev)

    def downgrade(rev, context):
        return script._downgrade_revs(None, rev)

    with EnvironmentContext(config, script, fn=upgrade):
        script.run_env()

    yield

    # Clear any pending work from the db_session connection
    db_session.rollback()

    with EnvironmentContext(config, script, fn=downgrade):
        script.run_env()


@pytest.fixture
def populated_db(migrated_db, db_session):
    datas = [
        {
            "id": 1,
            "sensor_name": "Test",
            "data": "1",
            "collected_at": datetime.datetime(2020, 4, 1, 12, 0, 1),
            "deployment_id": UUID("b4c68905-b1e4-4875-940e-69e5d27730fd"),
        },
        {
            "id": 2,
            "sensor_name": "Test",
            "data": "2",
            "collected_at": datetime.datetime(2020, 4, 1, 12, 1, 1),
            "deployment_id": UUID("b4c68905-b1e4-4875-940e-69e5d27730fd"),
        },
        {
            "id": 3,
            "sensor_name": "Test",
            "data": "3",
            "collected_at": datetime.datetime(2020, 4, 1, 12, 2, 1),
            "deployment_id": UUID("b4c68905-b1e4-4875-940e-69e5d27730fd"),
        },
        {
            "id": 4,
            "sensor_name": "Test",
            "data": "4",
            "collected_at": datetime.datetime(2020, 4, 1, 12, 3, 1),
            "deployment_id": UUID("b4c68905-b1e4-4875-940e-69e5d27730fd"),
        },
        {
            "id": 5,
            "sensor_name": "OtherTest",
            "data": "5",
            "collected_at": datetime.datetime(2020, 4, 1, 12, 4, 1),
            "deployment_id": UUID("b4c68905-b1e4-4875-940e-69e5d27730fd"),
        },
        {
            "id": 6,
            "sensor_name": "Test",
            "data": "1",
            "collected_at": datetime.datetime(2020, 4, 1, 12, 0, 1),
            "deployment_id": UUID("6e887b81-57c3-4f3b-a7e7-bad159e05e78"),
        },
        {
            "id": 7,
            "sensor_name": "Test",
            "data": "1",
            "collected_at": datetime.datetime(2020, 4, 1, 12, 1, 1),
            "deployment_id": UUID("6e887b81-57c3-4f3b-a7e7-bad159e05e78"),
        },
        {
            "id": 8,
            "sensor_name": "Test",
            "data": "2",
            "collected_at": datetime.datetime(2020, 4, 1, 12, 2, 1),
            "deployment_id": UUID("6e887b81-57c3-4f3b-a7e7-bad159e05e78"),
        },
        {
            "id": 9,
            "sensor_name": "OtherTest",
            "data": "3",
            "collected_at": datetime.datetime(2020, 4, 1, 12, 3, 1),
            "deployment_id": UUID("6e887b81-57c3-4f3b-a7e7-bad159e05e78"),
        },
    ]
    for data in datas:
        insert = datapoint_table.insert().values(**data)
        db_session.execute(insert)
