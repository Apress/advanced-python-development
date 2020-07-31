import os
import uuid
from unittest import mock

import flask
import pytest
from webtest import TestApp

from apd.sensors.sensors import PythonVersion
from apd.sensors.wsgi import set_up_config
from apd.sensors.wsgi import v10
from apd.sensors.wsgi import v20
from apd.sensors.wsgi import v21
from apd.sensors.wsgi import v30


@pytest.fixture(scope="session")
def api_key():
    return uuid.uuid4().hex


def test_api_key_is_required_config_option():
    app = mock.MagicMock()
    with pytest.raises(
        ValueError, match="Missing config variables: APD_SENSORS_API_KEY"
    ):
        set_up_config({"APD_SENSORS_DEPLOYMENT_ID": ""}, to_configure=app)


def test_os_environ_is_default_for_config_values(api_key):
    app = mock.MagicMock()
    os.environ["APD_SENSORS_API_KEY"] = api_key
    os.environ["APD_SENSORS_DEPLOYMENT_ID"] = "8f1b57faa04b430c81decbbeee9e300c"
    try:
        assert app.config.from_mapping.call_count == 0
        set_up_config(None, to_configure=app)
        assert app.config.from_mapping.call_count == 1
        for key, value in os.environ.items():
            # There may be keys in the config not from the environment
            assert app.config.from_mapping.call_args[0][0][key] == value
    finally:
        del os.environ["APD_SENSORS_API_KEY"]
        del os.environ["APD_SENSORS_DEPLOYMENT_ID"]


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
        set_up_config(
            {
                "APD_SENSORS_API_KEY": api_key,
                "APD_SENSORS_DEPLOYMENT_ID": "8f1b57faa04b430c81decbbeee9e300c",
            },
            to_configure=app,
        )
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

    @pytest.mark.functional
    def test_erroring_sensor_shows_None(self, api_server, api_key):
        from .test_utils import FailingSensor

        with mock.patch("apd.sensors.cli.get_sensors") as get_sensors:
            # Ensure failing sensor is first, to test that subsequent sensors
            # are still processed
            get_sensors.return_value = [FailingSensor(10), PythonVersion()]
            value = api_server.get("/sensors/", headers={"X-API-Key": api_key}).json
        assert value["Sensor which fails"] is None
        assert "Python Version" in value.keys()


class Testv20API(CommonTests):
    @pytest.fixture
    def subject(self, api_key):
        app = flask.Flask("testapp")
        app.register_blueprint(v20.version)
        set_up_config(
            {
                "APD_SENSORS_API_KEY": api_key,
                "APD_SENSORS_DEPLOYMENT_ID": "8f1b57faa04b430c81decbbeee9e300c",
            },
            to_configure=app,
        )
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

    @pytest.mark.functional
    def test_erroring_sensor_shows_None(self, api_server, api_key):
        from .test_utils import FailingSensor

        with mock.patch("apd.sensors.cli.get_sensors") as get_sensors:
            # Ensure failing sensor is first, to test that subsequent sensors
            # are still processed
            get_sensors.return_value = [FailingSensor(10), PythonVersion()]
            value = api_server.get("/sensors/", headers={"X-API-Key": api_key}).json
        sensors = value["sensors"]

        failing = [sensor for sensor in sensors if sensor["id"] == "FailingSensor"][0]
        python_version = [
            sensor for sensor in sensors if sensor["id"] == "PythonVersion"
        ][0]

        assert failing["title"] == "Sensor which fails"
        assert failing["value"] is None
        assert python_version["title"] == "Python Version"


class Testv21API(Testv20API):
    @pytest.fixture
    def subject(self, api_key):
        app = flask.Flask("testapp")
        app.register_blueprint(v21.version)
        set_up_config(
            {
                "APD_SENSORS_API_KEY": api_key,
                "APD_SENSORS_DEPLOYMENT_ID": "8f1b57faa04b430c81decbbeee9e300c",
            },
            to_configure=app,
        )
        return app

    @pytest.mark.functional
    def test_deployment_id(self, api_server, api_key):
        value = api_server.get("/deployment_id", headers={"X-API-Key": api_key}).json
        assert value == {"deployment_id": "8f1b57faa04b430c81decbbeee9e300c"}

    @pytest.mark.functional
    def test_erroring_sensor_shows_None(self, api_server, api_key):
        from .test_utils import FailingSensor

        with mock.patch("apd.sensors.cli.get_sensors") as get_sensors:
            # Ensure failing sensor is first, to test that subsequent sensors
            # are still processed
            get_sensors.return_value = [FailingSensor(10), PythonVersion()]
            value = api_server.get("/sensors/", headers={"X-API-Key": api_key}).json
        sensors = value["sensors"]

        failing = [sensor for sensor in sensors if sensor["id"] == "FailingSensor"][0]
        python_version = [
            sensor for sensor in sensors if sensor["id"] == "PythonVersion"
        ][0]

        assert failing["title"] == "Sensor which fails"
        assert failing["value"] is None
        assert python_version["title"] == "Python Version"


class Testv30API(CommonTests):
    @pytest.fixture
    def api_server(self, subject):
        return TestApp(subject)

    @pytest.fixture
    def subject(self, api_key):
        app = flask.Flask("testapp")
        app.register_blueprint(v30.version)
        set_up_config(
            {
                "APD_SENSORS_API_KEY": api_key,
                "APD_SENSORS_DEPLOYMENT_ID": "8f1b57faa04b430c81decbbeee9e300c",
                "APD_SENSORS_DB_URI": "sqlite://",
            },
            to_configure=app,
        )
        return app

    @pytest.fixture
    def db(self, subject):
        from flask_sqlalchemy import SQLAlchemy
        from apd.sensors.database import metadata

        db = SQLAlchemy(subject, metadata=metadata)
        db.create_all()
        return db

    @pytest.fixture
    def store_sensor_data(self):
        from apd.sensors.database import store_sensor_data

        return store_sensor_data

    @pytest.mark.functional
    def test_historical_with_no_data(self, api_key, api_server, db):
        value = api_server.get("/historical", headers={"X-API-Key": api_key}).json
        assert value == {"sensors": []}

    @pytest.mark.functional
    def test_historical_with_data(self, api_key, api_server, db, store_sensor_data):
        value = api_server.get("/historical", headers={"X-API-Key": api_key}).json
        store_sensor_data(PythonVersion, [3, 9, 0, "final", 1], db.session)
        assert value == {"sensors": []}

    @pytest.mark.functional
    def test_sensor_values_returned_as_json(self, api_server, api_key):
        value = api_server.get("/sensors/", headers={"X-API-Key": api_key}).json
        sensors = value["sensors"]

        python_version = [
            sensor for sensor in sensors if sensor["id"] == "PythonVersion"
        ][0]
        assert python_version["title"] == "Python Version"
        assert python_version["value"] == list(PythonVersion().value())

    @pytest.mark.functional
    def test_erroring_sensor_excluded_but_reported(self, api_server, api_key):
        from .test_utils import FailingSensor

        with mock.patch("apd.sensors.cli.get_sensors") as get_sensors:
            # Ensure failing sensor is first, to test that subsequent sensors
            # are still processed
            get_sensors.return_value = [FailingSensor(2), PythonVersion()]
            value = api_server.get("/sensors/", headers={"X-API-Key": api_key}).json
            second_attempt_value = api_server.get(
                "/sensors/", headers={"X-API-Key": api_key}
            ).json

        sensors = value["sensors"]
        failing = [sensor for sensor in sensors if sensor["id"] == "FailingSensor"]
        assert len(failing) == 0
        errors = value["errors"]
        failing = [sensor for sensor in errors if sensor["id"] == "FailingSensor"]
        assert len(failing) == 1

        python_version = [
            sensor for sensor in sensors if sensor["id"] == "PythonVersion"
        ]
        assert len(python_version) == 1

        sensors = second_attempt_value["sensors"]
        assert second_attempt_value["errors"] == []
        failing = [sensor for sensor in sensors if sensor["id"] == "FailingSensor"]
        assert len(failing) == 1
        python_version = [
            sensor for sensor in sensors if sensor["id"] == "PythonVersion"
        ]
        assert len(python_version) == 1
