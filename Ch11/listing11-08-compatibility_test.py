    @pytest.mark.functional
    def test_erroring_sensor_shows_None(self, api_server, api_key):
        from .test_utils import FailingSensor

        with mock.patch("apd.sensors.cli.get_sensors") as get_sensors:
            # Ensure the failing sensor is first, to test that subsequent sensors
            # are still processed
            get_sensors.return_value = [FailingSensor(10), PythonVersion()]
            value = api_server.get("/sensors/", headers={"X-API-Key": api_key}).json
        assert value['Sensor which fails'] == None
        assert "Python Version" in value.keys()

