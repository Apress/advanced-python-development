import yappi

from apd.aggregation.analysis import interactable_plot_multiple_charts, Config
from apd.aggregation.analysis import clean_temperature_fluctuations, get_one_sensor_by_deployment
from apd.aggregation.utils import profile_with_yappi

yappi.set_clock_type("wall")

filter_in_db = Config(
    clean=clean_temperature_fluctuations,
    title="Ambient temperature",
    ylabel="Degrees C",
    get_data=get_one_sensor_by_deployment("Temperature"),
)

with profile_with_yappi():
    plot = interactable_plot_multiple_charts(configs=[filter_in_db])
    plot()

yappi.get_func_stats().print_all()

