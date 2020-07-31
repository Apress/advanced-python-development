import collections

from apd.aggregation.query import with_database, get_data, get_deployment_ids

from matplotlib import pyplot as plt

async def plot(deployment_id):
    points = []
    async for dp in get_data(sensor_name="RelativeHumidity", deployment_id=deployment_id):
        points.append((dp.collected_at, dp.data))

    x, y = zip(*points)
    plt.plot_date(x, y, "o", xdate=True)

with with_database("postgresql+psycopg2://apd@localhost/apd") as session:
    deployment_ids = await get_deployment_ids()
    for deployment in deployment_ids:
        await plot(deployment)
plt.show()

