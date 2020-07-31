from unittest import mock

import pytest

from sensors import CPULoad


@pytest.fixture
def sensor():
    return CPULoad()


class TestCPULoadFormatter:
    @pytest.fixture
    def subject(self, sensor):
        return sensor.format

    def test_format_simple_percentage(self, subject):
        assert subject(0.05) == "5.0%"

    def test_format_multiple_decimal_places(self, subject):
        assert subject(0.031415926) == "3.1%"

    def test_format_multiple_decimal_places_int(self, subject) -> None:
        assert subject(1) == "100.0%"


class TestCPULoadValue:
    @pytest.fixture
    def subject(self, sensor):
        return sensor.value

    @pytest.fixture
    def cpuload(self):
        with mock.patch("psutil.cpu_percent") as cpu_percent:
            cpu_percent.return_value = 50.1
            yield cpu_percent

    def test_cpu_percent_called_With_interval(self, subject, cpuload):
        assert subject() == 0.501
        assert cpuload.call_count == 1
        assert tuple(cpuload.call_args) == ((), {"interval": 3})

    def test_str_representation_is_formatted_value(self, sensor, cpuload):
        assert str(sensor) == "50.1%"
