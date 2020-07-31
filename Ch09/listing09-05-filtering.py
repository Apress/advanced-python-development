from apd.aggregation.query import with_database, get_data

from matplotlib import pyplot as plt

async def plot():
    points = [(dp.collected_at, dp.data) async for dp in get_data(sensor_name="RelativeHumidity")]
    x, y = zip(*points)
    plt.plot_date(x, y, "o", xdate=True)

with with_database("postgresql+psycopg2://apd@localhost/apd") as session:
    await plot()
plt.show()

