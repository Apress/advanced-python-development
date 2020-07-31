import asyncio
from uuid import UUID

import ipywidgets as widgets
from matplotlib import pyplot as plt

from apd.aggregation.query import with_database
from apd.aggregation.analysis import get_known_configs, plot_sensor, wrap_coroutine


@wrap_coroutine
async def plot(*args, **kwargs):
    location_names = {
     UUID('53998a51-60de-48ae-b71a-5c37cd1455f2'): "Loft",
     UUID('1bc63cda-e223-48bc-93c2-c1f651779d69'): "Living Room",
     UUID('ea0683de-6772-4678-bfe7-6014f54ffc8e'): "Office",
     UUID('5aaa901a-7564-41fb-8eba-50cdd6fe9f80'): "Outside",
    }

    with with_database("postgresql+psycopg2://apd@localhost/apd") as session:
        coros = []
        figure = plt.figure(figsize = (20, 10), dpi=300)
        configs = get_known_configs().values()
        for i, config in enumerate(configs, start=1):
            plot = figure.add_subplot(2, 2, i)
            coros.append(plot_sensor(config, plot, location_names, *args, **kwargs))
        await asyncio.gather(*coros)
    return figure


start = widgets.DatePicker(
    description='Start date',
)
end = widgets.DatePicker(
    description='End date',
)
out = widgets.interactive(plot, collected_after=start, collected_before=end)
display(out)

