import yappi

from apd.aggregation.analysis import interactable_plot_multiple_charts, Config, clean_temperature_fluctuations, get_data_by_deployment
from apd.aggregation.utils import jupyter_page_file, profile_with_yappi, YappiPackageFilter

async def filter_and_clean_temperature_fluctuations(datapoints):
    filtered = (item async for item in datapoints if item.sensor_name=="Temperature")
    cleaned = clean_temperature_fluctuations(filtered)
    async for item in cleaned:
        yield item

filter_in_python = Config(
    clean=filter_and_clean_temperature_fluctuations,
    title="Ambient temperature",
    ylabel="Degrees C",
    get_data=get_data_by_deployment,
)

with profile_with_yappi():
    plot = interactable_plot_multiple_charts(configs=[filter_in_python])
    plot()

yappi.get_func_stats().print_all()

