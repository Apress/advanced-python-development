import pytest

from apd.sensors.sensors import Temperature, RelativeHumidity


@pytest.fixture
def temperature_sensor():
    return Temperature()


@pytest.fixture
def humidity_sensor():
    return RelativeHumidity()


class TestTemperatureFormatter:
    @pytest.fixture
    def subject(self, temperature_sensor):
        return temperature_sensor.format

    def test_format_21c(self, subject):
        assert subject(21.0) == "21.0C (69.8F)"

    def test_format_negative(self, subject):
        assert subject(-32.0) == "-32.0C (-25.6F)"

    def test_format_unknown(self, subject):
        assert subject(None) == "Unknown"


class TestTemperatureConversion:
    @pytest.fixture
    def subject(self, temperature_sensor):
        return temperature_sensor.celsius_to_fahrenheit

    def test_celsius_to_fahrenheit(self, subject):
        c = 21
        f = subject(c)
        assert f == 69.8

    def test_celsius_to_fahrenheit_equivlance_point(self, subject):
        c = -40
        f = subject(c)
        assert f == -40

    def test_celsius_to_fahrenheit_float(self, subject):
        c = 21.2
        f = subject(c)
        assert f == 70.16

    def test_celsius_to_fahrenheit_string(self, subject):
        c = "21"
        with pytest.raises(TypeError):
            subject(c)


class TestHumidityFormatter:
    @pytest.fixture
    def subject(self, humidity_sensor):
        return humidity_sensor.format

    def test_format_percentage(self, subject):
        assert subject(0.035) == "3.5%"

    def test_format_unknown(self, subject):
        assert subject(None) == "Unknown"
