from unittest import mock

import pytest

from apd.sensors.sensors import RAMAvailable


@pytest.fixture
def sensor():
    return RAMAvailable()


class TestRAMAvailableFormatter:
    @pytest.fixture
    def subject(self, sensor):
        return sensor.format

    def test_format_bytes(self, subject):
        assert subject(15) == "15.0 B"

    def test_format_kibibytes(self, subject):
        assert subject(15000) == "14.6 KiB"

    def test_format_mibibytes(self, subject):
        assert subject(15000000) == "14.3 MiB"

    def test_format_gibibytes(self, subject):
        assert subject(15000000000) == "14.0 GiB"


class TestRAMAvailableValue:
    @pytest.fixture
    def subject(self, sensor):
        return sensor.value

    @pytest.fixture
    def virtual_memory(self):
        with mock.patch("psutil.virtual_memory") as virtual_memory:
            virtual_memory.return_value.available = 1024
            yield virtual_memory

    def test_virtual_memory_called(self, subject, virtual_memory):
        assert subject() == 1024
        assert virtual_memory.call_count == 1

    def test_str_representation_is_formatted_value(self, sensor, virtual_memory):
        assert str(sensor) == "1.0 KiB"
