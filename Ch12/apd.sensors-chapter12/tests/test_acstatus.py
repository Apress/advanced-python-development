from unittest import mock

import pytest

from apd.sensors.sensors import ACStatus
from apd.sensors.exceptions import (
    PersistentSensorFailureError,
    IntermittentSensorFailureError,
)


@pytest.fixture
def sensor():
    return ACStatus()


class TestACStatusFormatter:
    @pytest.fixture
    def subject(self, sensor):
        return sensor.format

    def test_format_True(self, subject):
        assert subject(True) == "Connected"

    def test_format_False(self, subject):
        assert subject(False) == "Not connected"


class TestACStatusValue:
    @pytest.fixture
    def subject(self, sensor):
        return sensor.value

    @pytest.fixture
    def sensors_battery(self):
        with mock.patch("psutil.sensors_battery") as sensors_battery:
            yield sensors_battery

    def test_sensors_battery_called(self, subject, sensors_battery):
        sensors_battery.return_value.power_plugged = True
        assert subject() is True
        assert sensors_battery.call_count == 1

    def test_sensor_but_battery_unknown(self, subject, sensors_battery):
        sensors_battery.return_value.power_plugged = None
        with pytest.raises(IntermittentSensorFailureError):
            subject()
        assert sensors_battery.call_count == 1

    def test_no_sensor(self, subject, sensors_battery):
        sensors_battery.return_value = None
        with pytest.raises(PersistentSensorFailureError):
            subject()

    def test_str_representation_is_formatted_value(self, sensor, sensors_battery):
        sensors_battery.return_value.power_plugged = True
        assert str(sensor) == "Connected"
        assert sensors_battery.call_count == 1
