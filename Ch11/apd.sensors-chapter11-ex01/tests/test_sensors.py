import json
from unittest import mock

from click.testing import CliRunner

import pytest

import apd.sensors.cli
from apd.sensors.exceptions import UserFacingCLIError
import apd.sensors.sensors


def test_sensors():
    assert hasattr(apd.sensors.sensors, "PythonVersion")


class TestCLI:
    @pytest.mark.functional
    def test_first_sensor_is_first_two_lines_of_cli_output(self):
        runner = CliRunner()
        with mock.patch("apd.sensors.cli.get_sensors") as get_sensors:
            get_sensors.return_value = [apd.sensors.sensors.PythonVersion()]
            result = runner.invoke(apd.sensors.cli.show_sensors)
        python_version = str(apd.sensors.sensors.PythonVersion())
        assert ["Python Version", python_version] == result.stdout.split("\n")[:2]

    def test_failing_sensor_shows_error(self):
        from .test_utils import FailingSensor

        runner = CliRunner()
        with mock.patch("apd.sensors.cli.get_sensors") as get_sensors:
            get_sensors.return_value = [
                FailingSensor(10),
                apd.sensors.sensors.PythonVersion(),
            ]
            result = runner.invoke(apd.sensors.cli.show_sensors)
        assert ["Sensor which fails", "Failing 9 more times"] == result.stdout.split(
            "\n"
        )[:2]
        assert "Python Version" in result.stdout

    def test_mocked_failing_sensor_shows_error(self):
        from apd.sensors.base import Sensor
        from apd.sensors.exceptions import IntermittentSensorFailureError

        FailingSensor = mock.MagicMock(spec=Sensor)
        FailingSensor.title = "Sensor which fails"
        FailingSensor.name = "FailingSensor"
        FailingSensor.value.side_effect = (
            FailingSensor.__str__.side_effect
        ) = IntermittentSensorFailureError("Failing sensor")

        runner = CliRunner()
        with mock.patch("apd.sensors.cli.get_sensors") as get_sensors:
            get_sensors.return_value = [
                FailingSensor,
                apd.sensors.sensors.PythonVersion(),
            ]
            result = runner.invoke(apd.sensors.cli.show_sensors)
        assert ["Sensor which fails", "Failing sensor"] == result.stdout.split("\n")[:2]
        assert "Python Version" in result.stdout


class TestSensorFromPath:
    @pytest.fixture
    def subject(self):
        return apd.sensors.cli.get_sensor_by_path

    def test_get_sensor_by_path(self, subject):
        assert isinstance(
            subject("apd.sensors.sensors:PythonVersion"),
            apd.sensors.sensors.PythonVersion,
        )

    def test_invalid_format(self, subject):
        with pytest.raises(UserFacingCLIError, match="dotted.path.to.module:ClassName"):
            subject("apd.sensors.sensors.PythonVersion")

    def test_invalid_module(self, subject):
        with pytest.raises(UserFacingCLIError, match="Could not import module"):
            subject("apd.nonsense.sensor:FakeSensor")

    def test_missing_sensor(self, subject):
        with pytest.raises(UserFacingCLIError, match="Could not find attribute"):
            subject("apd.sensors.sensors:FakeSensor")

    def test_invalid_sensor(self, subject):
        with pytest.raises(UserFacingCLIError, match="is not recognised as a Sensor"):
            subject("apd.sensors.sensors:Sensor")


@pytest.mark.functional
def test_develop_option_finds_sensor_by_path():
    runner = CliRunner()
    result = runner.invoke(
        apd.sensors.cli.show_sensors, ["--develop", "apd.sensors.sensors:PythonVersion"]
    )
    python_version = str(apd.sensors.sensors.PythonVersion())
    assert ["Python Version", python_version, "", ""] == result.stdout.split("\n")


class TestDefaultSerializer:
    @pytest.fixture
    def python_version(self):
        return apd.sensors.sensors.PythonVersion()

    @pytest.fixture
    def serialize(self, python_version):
        return python_version.to_json_compatible

    @pytest.fixture
    def deserialize(self, python_version):
        return python_version.from_json_compatible

    def test_serialize_deserialize_is_symmetric(
        self, python_version, serialize, deserialize
    ):
        value = python_version.value()
        serialized = serialize(value)
        json_version = json.dumps(serialized)
        assert (
            json_version == f"[{value.major}, {value.minor}, {value.micro},"
            f' "{value.releaselevel}", {value.serial}]'
        )
        deserialized = deserialize(serialized)
        assert deserialized == value
