import yappi
from apd.aggregation.analysis import interactable_plot_multiple_charts, Config
from apd.aggregation.analysis import convert_temperature_system, clean_temperature_fluctuations 
from apd.aggregation.analysis import get_one_sensor_by_deployment

filter_in_db = Config(
    clean=convert_temperature_system(clean_temperature_fluctuations, "degF"),
    title="Ambient temperature",
    ylabel="Degrees F",
    get_data=get_one_sensor_by_deployment("Temperature"),
)
display(interactable_plot_multiple_charts(configs=[filter_in_db])())

