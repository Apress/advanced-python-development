import asyncio

from matplotlib import pyplot as plt

from apd.aggregation.query import with_database
from apd.aggregation.analysis import get_known_configs, plot_sensor

with with_database("postgresql+psycopg2://apd@localhost/apd") as session:
    coros = []
    figure = plt.figure(figsize = (20, 5), dpi=300)
    configs = get_known_configs()
    to_display = configs["Relative humidity"], configs["RAM available"]
    for i, config in enumerate(to_display, start=1):
        plot = figure.add_subplot(1, 2, i)
        coros.append(plot_sensor(config, plot, {}))
    await asyncio.gather(*coros)

display(figure)

