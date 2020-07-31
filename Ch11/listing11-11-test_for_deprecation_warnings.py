def test_deprecation_warning_raised_by_config_with_no_getdata():
    with warnings.catch_warnings(record=True) as captured_warnings:
        warnings.simplefilter("always", DeprecationWarning)
        config = analysis.Config(
            sensor_name="Temperature",
            clean=analysis.clean_passthrough,
            title="Temperaure",
            ylabel="Deg C"
        )
        assert len(captured_warnings) == 1
        deprecation_warning = captured_warnings[0]
        assert deprecation_warning.filename == __file__
        assert deprecation_warning.category == DeprecationWarning
        assert str(deprecation_warning.message) == (
            "The sensor_name parameter is deprecated. Please pass "
            "get_data=get_one_sensor_by_deployment('Temperature') "
            "to ensure the same behaviour. The sensor_name= parameter "
            "will be removed in apd.aggregation 3.0."
        )

