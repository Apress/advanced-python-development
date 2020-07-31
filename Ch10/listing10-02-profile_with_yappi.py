from apd.aggregation.analysis import interactable_plot_multiple_charts, configs
from apd.aggregation.utils import jupyter_page_file, profile_with_yappi, yappi_package_matches
import yappi

with profile_with_yappi():
    plot = interactable_plot_multiple_charts()
    plot()

with jupyter_page_file() as output:
    yappi.get_func_stats(filter_callback=lambda stat:
        yappi_package_matches(stat, ["apd.aggregation"])
    ).print_all(output)

