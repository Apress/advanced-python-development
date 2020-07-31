from click.testing import CliRunner

import pytest
from unittest import mock

import apd.sensors.cli
import apd.sensors.sensors


def test_sensors():
    assert hasattr(apd.sensors.sensors, "PythonVersion")


@pytest.mark.functional
def test_first_sensor_is_first_two_lines_of_cli_output():
    runner = CliRunner()
    with mock.patch("apd.sensors.cli.get_sensors") as get_sensors:
        get_sensors.return_value = [apd.sensors.sensors.PythonVersion()]
        result = runner.invoke(apd.sensors.cli.show_sensors)
    python_version = str(apd.sensors.sensors.PythonVersion())
    assert ["Python Version", python_version] == result.stdout.split("\n")[:2]


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
