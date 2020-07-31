from apd.aggregation.query import with_database, get_data

with with_database("postgresql+psycopg2://apd@localhost/apd") as session:
    count = 0
    async for datapoint in get_data():
        count += 1
    print(count)

