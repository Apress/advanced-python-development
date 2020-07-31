import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from sqlalchemy.orm import sessionmaker


Base = declarative_base()


class DataPoint(Base):
    __tablename__ = "datapoints"
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    sensor_name = sqlalchemy.Column(sqlalchemy.String)
    collected_at = sqlalchemy.Column(TIMESTAMP)
    data = sqlalchemy.Column(JSONB)


def main():
    engine = sqlalchemy.create_engine(
        "postgresql+psycopg2://apd@localhost/apd", echo=True
    )
    sm = sessionmaker(engine)
    Session = sm()
    if False:
        Base.metadata.create_all(engine)
    print(Session.query(DataPoint).all())
    pass


if __name__ == "__main__":
    main()
