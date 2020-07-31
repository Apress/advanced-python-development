# APD Sensor aggregator 

A programme that queries apd.sensor endpoints and aggregates their results.

Generic single-database configuration.

# Database setup

To generate the required database tables you must create an alembic.ini file, as follows:

    [alembic]
    script_location = apd.aggregation:alembic
    sqlalchemy.url = postgresql+psycopg2://apd@localhost/apd

and run `alembic upgrade head`. This should also be done after every upgrade of the software.

# Defining endpoints

Endpoints to collect from are managed with the `sensor_deployments` CLI tool. After installation
there will be no deployments defined 

    sensor_deployments add --db postgresql+psycopg2://apd@localhost/apd 
                           --api-key 97f6b3e5ceb64a6ba88968d7c3786b38
                           --colour xkcd:red
                           http://rpi4:8081
                           Loft

The optional colour argument is the colour to use when plotting charts with the built-in charting
tools. This uses matplotlib's colour specification system, documented at https://matplotlib.org/tutorials/colors/colors.html

The sensors can then be listed with `sensor_deployments list`:

    Loft
    ID 53998a5160de48aeb71a5c37cd1455f2
    URI http://rpi4:8081
    API key 97f6b3e5ceb64a6ba88968d7c3786b38
    Colour xkcd:red

The ID is the deployment ID, as set by the endpoint. It is only possible to add endpoints if they can be
connected to at the time.

# Collating data

Data can be collated from all defined endpoints with the `collect_sensor_data` command line tool.
Although you can specify URLs and an API key to explicitly load data from a one-off endpoint, running
without specifying these will use the configured endpoints from the database.

    collect_sensor_data --db postgresql+psycopg2://apd@localhost/apd

# Viewing data

You can write scripts to visualise the data from the database. I recommend using Jupyter for this, as it
has good support for drawing charts and interactivity.

All configured charts can be displayed with:

    from apd.aggregation.analysis import plot_multiple_charts
    display(await plot_multiple_charts())

More complex charting can be achieved by passing `configs=` to this function, consisting of configuration
objects as defined in `apd.aggregation.analysis`. Iteractivity can be achieved using the
`interactable_plot_multiple_charts` function with Jupyter/IPyWidgets' existing interactivity support.

More control can be achieved using other functions from this module, such as getting all data points from
a given sensor with:

    from apd.aggregation.query import with_database, get_data

    with with_database("postgresql+psycopg2://apd@localhost/apd") as session:
        points = [(dp.collected_at, dp.data) async for dp in get_data() if dp.sensor_name=="RelativeHumidity"]
    
These can be called from any Python code, not just Jupyter notebooks

# Analysis and triggers

The aggregator allows for a long-running process that processes records as they are inserted to the database
and apply rules to them.

This is configured with a Python-based configuration file, such as the following to log any time the
Temperature fluctuates above or below 18c:

    import operator

    from apd.aggregation.actions.action import OnlyOnChangeActionWrapper, LoggingAction
    from apd.aggregation.actions.runner import DataProcessor
    from apd.aggregation.actions.trigger import ValueThresholdTrigger


    handlers = [
        DataProcessor(
            name="TemperatureBelow18",
            action=OnlyOnChangeActionWrapper(LoggingAction()),
            trigger=ValueThresholdTrigger(
                name="TemperatureBelow18",
                threshold=18,
                comparator=operator.lt,
                sensor_name="Temperature",
            ),
        )
    ]

This is run with:

    run_apd_actions --db postgresql+psycopg2://apd@localhost/apd sample_actions.py

The optional `--historical` option causes the actions to be triggered for all events in the database.
If it's omitted then the default behaviour applies, which is to only analyse data that is added to the
database after the actions process has started.

The possible actions are:

* `apd.aggregation.actions.action.LoggingAction()` - Log data points
* `apd.aggregation.actions.action.SaveToDatabaseAction()` - Save data points to the db

These can be wrapped with `OnlyOnChangeActionWrapper(subaction)` to only trigger an action when
the underlying value changes and/or with `OnlyAfterDateActionWrapper(subaction, min_date)` to 
only trigger if the date on the discovered objects is strictly after `min_date`.

The possible triggers are:

* `apd.aggregation.actions.trigger.ValueThresholdTrigger(...)` - This compares the value of a sensor with threshold, using the specified comparator.
    Any records that don't match the `sensor_name` and `deployment_id` parameters are excluded.


# Tips

The `--db` argument to all command-line tools can be omitted and the `APD_DB_URI` environment variable
set instead.