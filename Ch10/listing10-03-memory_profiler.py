import tracemalloc

from apd.aggregation.analysis import interactable_plot_multiple_charts


tracemalloc.start()
plot = interactable_plot_multiple_charts()()
snapshot = tracemalloc.take_snapshot()
tracemalloc.stop()
for line in snapshot.statistics("lineno", cumulative=True):
    print(line)

