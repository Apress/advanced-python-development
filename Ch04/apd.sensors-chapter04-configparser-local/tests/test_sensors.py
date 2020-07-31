import os
from unittest import mock

from click.testing import CliRunner

import pytest

import apd.sensors.cli
import apd.sensors.sensors


class MockTestingSensor(apd.sensors.sensors.Sensor[int]):
    title = "Configured Number"

    def __init__(self, configured="0"):
        self.configured = configured

    def value(self) -> int:
        return int(self.configured)

    @classmethod
    def format(cls, value: int) -> str:
        return "{}".format(value)


def test_sensors():
    assert hasattr(apd.sensors.sensors, "PythonVersion")


@pytest.fixture
def default_config_path():
    return os.path.join(os.path.dirname(__file__), "default_test_config.cfg")


@pytest.mark.functional
def test_python_version_is_first_two_lines_of_cli_output(default_config_path):
    runner = CliRunner()
    result = runner.invoke(
        apd.sensors.cli.show_sensors, ["--config", default_config_path]
    )
    python_version = str(apd.sensors.sensors.PythonVersion())
    assert ["Python Version", python_version] == result.stdout.split("\n")[:2]


def test_parameter_for_sensor():
    with mock.patch("apd.sensors.cli.parse_config_file") as parse_config_file:
        parse_config_file.return_value = {
            "TestingSensor": {
                "plugin": "tests.test_sensors:MockTestingSensor",
                "configured": "42",
            }
        }
        sensors = apd.sensors.cli.get_sensors("")
        assert isinstance(sensors[0], MockTestingSensor)
        assert sensors[0].value() == 42


def test_spurious_parameters_raise_errors():
    with mock.patch("apd.sensors.cli.parse_config_file") as parse_config_file:
        parse_config_file.return_value = {
            "TestingSensor": {
                "plugin": "apd.sensors.sensors:PythonVersion",
                "magic": "42",
            }
        }
        with pytest.raises(RuntimeError, match="unexpected keyword argument magic"):
            apd.sensors.cli.get_sensors("")


def test_extract_plugins(default_config_path):
    parsed = apd.sensors.cli.parse_config_file(default_config_path)
    assert parsed == {
        "IPAddress": {"plugin": "apd.sensors.sensors:IPAddresses"},
        "PythonVersion": {"plugin": "apd.sensors.sensors:PythonVersion"},
    }


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
        with pytest.raises(RuntimeError, match="dotted.path.to.module:ClassName"):
            subject("apd.sensors.sensors.PythonVersion")

    def test_invalid_module(self, subject):
        with pytest.raises(RuntimeError, match="Could not import module"):
            subject("apd.nonsense.sensor:FakeSensor")

    def test_missing_sensor(self, subject):
        with pytest.raises(RuntimeError, match="Could not find attribute"):
            subject("apd.sensors.sensors:FakeSensor")

    def test_invalid_sensor(self, subject):
        with pytest.raises(RuntimeError, match="is not recognised as a Sensor"):
            subject("apd.sensors.sensors:Sensor")


@pytest.mark.functional
def test_develop_option_finds_sensor_by_path():
    runner = CliRunner()
    result = runner.invoke(
        apd.sensors.cli.show_sensors, ["--develop", "apd.sensors.sensors:PythonVersion"]
    )
    python_version = str(apd.sensors.sensors.PythonVersion())
    assert ["Python Version", python_version, "", ""] == result.stdout.split("\n")
