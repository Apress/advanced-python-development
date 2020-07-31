@click.command(help="Displays the values of the sensors")
@click.option(
    "--develop", required=False, metavar="path", help="Load a sensor by Python path"
)
@click.option("--verbose", is_flag=True, help="Show additional info")
@click.option("--save", is_flag=True, help="Store collected data to a database")
@click.option(
    "--db",
    metavar="<CONNECTION_STRING>",
    default="sqlite:///sensor_data.sqlite",
    help="The connection string to a database",
    envvar="APD_SENSORS_DB_URI",
)
def show_sensors(develop: str, verbose: bool, save: bool, db: str) -> None:
    sensors: t.Iterable[Sensor[t.Any]]
    if develop:
        try:
            sensors = [get_sensor_by_path(develop)]
        except UserFacingCLIError as error:
            if verbose:
                tb = traceback.format_exception(type(error), error, error.__traceback__)
                click.echo("".join(tb))
            click.secho(error.message, fg="red", bold=True)
            sys.exit(error.return_code)
    else:
        sensors = get_sensors()

    db_session = None
    if save:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        engine = create_engine(db)
        sm = sessionmaker(engine)
        db_session = sm()

    for sensor in sensors:
        click.secho(sensor.title, bold=True)
        try:
            value = sensor.value()
        except DataCollectionError as error:
            if verbose:
                tb = traceback.format_exception(type(error), error, error.__traceback__)
                click.echo("".join(tb))
                continue
            click.echo(error)
        else:
            click.echo(sensor.format(value))
            if save and db_session is not None:
                store_sensor_data(sensor, value, db_session)
                db_session.commit()

        click.echo("")
    sys.exit(ReturnCodes.OK)

