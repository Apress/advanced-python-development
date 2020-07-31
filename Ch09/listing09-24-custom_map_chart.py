def get_literal_data():
    # Get manually entered temperature data, as our particular deployment
    # does not contain data of this shape
    raw_data = {...}
    now = datetime.datetime.now()
    async def points():
        for (coord, temp) in raw_data.items():
            deployment_id = uuid.uuid4()
            yield DataPoint(sensor_name="Location", deployment_id=deployment_id,
                            collected_at=now, data=coord)
            yield DataPoint(sensor_name="Temperature", deployment_id=deployment_id,
                            collected_at=now, data=temp)
    async def deployments(*args, **kwargs):
        yield None, points()
    return deployments

def draw_map_with_gb(plot, x, y, colour):
    # Draw the map and add an explicit coastline
    gb_boundary = [...]
    draw_map(plot, x, y, colour)
    plot.plot(
        [merc_x(coord[0]) for coord in gb_boundary],
        [merc_y(coord[1]) for coord in gb_boundary],
        "k-",
    )

country = Config(
    get_data=get_literal_data(),
    clean=get_map_cleaner_for("Temperature"),
    title="Country wide temperature",
    ylabel="",
    draw=draw_map_with_gb,
)

out = widgets.interactive(interactable_plot_multiple_charts(configs=configs + (country, )), collected_after=start, collected_before=end)

