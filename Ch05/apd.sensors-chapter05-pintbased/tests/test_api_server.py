import os
import uuid
from unittest import mock

import flask
import pytest
from webtest import TestApp

from apd.sensors.wsgi import set_up_config
from apd.sensors.sensors import PythonVersion
from apd.sensors.wsgi import v10
from apd.sensors.wsgi import v20


@pytest.fixture(scope="session")
def api_key():
    return uuid.uuid4().hex


def test_api_key_is_required_config_option():
    app = mock.MagicMock()
    with pytest.raises(
        ValueError, match="Missing config variables: APD_SENSORS_API_KEY"
    ):
        set_up_config({}, to_configure=app)


def test_os_environ_is_default_for_config_values(api_key):
    app = mock.MagicMock()
    os.environ["APD_SENSORS_API_KEY"] = api_key
    try:
        assert app.config.from_mapping.call_count == 0
        set_up_config(None, to_configure=app)
        assert app.config.from_mapping.call_count == 1
        assert app.config.from_mapping.call_args[0][0] == os.environ
    finally:
        del os.environ["APD_SENSORS_API_KEY"]


class CommonTests:
    @pytest.mark.functional
    def test_sensor_values_fails_on_missing_api_key(self, api_server):
        response = api_server.get("/sensors/", expect_errors=True)
        assert response.status_code == 403
        assert response.json["error"] == "Supply API key in X-API-Key header"

    @pytest.mark.functional
    def test_sensor_values_require_correct_api_key(self, api_server):
        response = api_server.get(
            "/sensors/", headers={"X-API-Key": "wrong_key"}, expect_errors=True
        )
        assert response.status_code == 403
        assert response.json["error"] == "Supply API key in X-API-Key header"


class Testv10API(CommonTests):
    @pytest.fixture
    def subject(self, api_key):
        app = flask.Flask("testapp")
        app.register_blueprint(v10.version)
        set_up_config({"APD_SENSORS_API_KEY": api_key}, to_configure=app)
        return app

    @pytest.fixture
    def api_server(self, subject):
        return TestApp(subject)

    @pytest.mark.functional
    def test_sensor_values_returned_as_json(self, api_server, api_key):
        value = api_server.get("/sensors/", headers={"X-API-Key": api_key}).json
        python_version = PythonVersion().value()

        sensor_names = value.keys()
        assert "Python Version" in sensor_names
        assert value["Python Version"] == list(python_version)

    @pytest.mark.functional
    def test_unserializable_sensor_is_omitted(self, api_server, api_key):
        value = api_server.get("/sensors/", headers={"X-API-Key": api_key}).json
        sensor_names = value.keys()
        assert "Temperature" not in sensor_names


class Testv20API(CommonTests):
    @pytest.fixture
    def subject(self, api_key):
        app = flask.Flask("testapp")
        app.register_blueprint(v20.version)
        set_up_config({"APD_SENSORS_API_KEY": api_key}, to_configure=app)
        return app

    @pytest.fixture
    def api_server(self, subject):
        return TestApp(subject)

    @pytest.mark.functional
    def test_sensor_values_returned_as_json(self, api_server, api_key):
        value = api_server.get("/sensors/", headers={"X-API-Key": api_key}).json
        sensors = value["sensors"]

        python_version = [
            sensor for sensor in sensors if sensor["id"] == "PythonVersion"
        ][0]
        assert python_version["title"] == "Python Version"
        assert python_version["value"] == list(PythonVersion().value())
