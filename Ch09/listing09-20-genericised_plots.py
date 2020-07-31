async def plot_multiple_charts(*args: t.Any, **kwargs: t.Any) -> Figure:
    # These parameters are pulled from kwargs to avoid confusing function
    # introspection code in IPython widgets
    location_names = kwargs.pop("location_names", None)
    configs = kwargs.pop("configs", None)
    dimensions = kwargs.pop("dimensions", None)
    db_uri = kwargs.pop("db_uri", "postgresql+psycopg2://apd@localhost/apd")

    with with_database(db_uri):
        coros = []
        if configs is None:
            # If no configs are supplied, use all known configs
            configs = get_known_configs().values()
        if dimensions is None:
            # If no dimensions are supplied, get the square root of the number
            # of configs and round it to find a number of columns. This will
            # keep the arrangement approximately square. Find rows by multiplying
            # out rows.
            total_configs = len(configs)
            columns = round(math.sqrt(total_configs))
            rows = math.ceil(total_configs / columns)
        figure = plt.figure(figsize=(10 * columns, 5 * rows), dpi=300)
        for i, config in enumerate(configs, start=1):
            plot = figure.add_subplot(columns, rows, i)
            coros.append(plot_sensor(config, plot, location_names, *args, **kwargs))
        await asyncio.gather(*coros)
    return figure

def interactable_plot_multiple_charts(
    *args: t.Any, **kwargs: t.Any
) -> t.Callable[..., Figure]:
    with_config = functools.partial(plot_multiple_charts, *args, **kwargs)
    return wrap_coroutine(with_config)

