import pytest
from webtest import TestApp

from apd.sensors.wsgi import sensor_values
from apd.sensors.sensors import PythonVersion


@pytest.fixture(scope="session")
def subject():
    return sensor_values


@pytest.fixture(scope="session")
def api_server(subject):
    return TestApp(subject)


@pytest.mark.functional
def test_sensor_values_returned_as_json(api_server):
    value = api_server.get("/sensors/").json
    python_version = PythonVersion().value()

    sensor_names = value.keys()
    assert "Python Version" in sensor_names
    assert value["Python Version"] == list(python_version)
