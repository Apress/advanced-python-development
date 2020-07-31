import collections

from apd.aggregation.query import with_database, get_data

from matplotlib import pyplot as plt

async def plot():
    legends = collections.defaultdict(list)
    async for dp in get_data(sensor_name="RelativeHumidity"):
        legends[dp.deployment_id].append((dp.collected_at, dp.data))

    for deployment_id, points in legends.items():
        x, y = zip(*points)
        plt.plot_date(x, y, "o", xdate=True)

with with_database("postgresql+psycopg2://apd@localhost/apd") as session:
    await plot()
plt.show()

