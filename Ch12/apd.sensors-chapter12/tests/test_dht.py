import pytest

from apd.sensors.sensors import Temperature, RelativeHumidity, ureg


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

    @staticmethod
    def to_degc(magnitude):
        return ureg.Quantity(magnitude, "degree_Celsius")

    def test_format_21c(self, subject):
        assert subject(self.to_degc(21.0)) == "21.0 °C (69.8 °F)"

    def test_format_negative(self, subject):
        assert subject(self.to_degc(-32.0)) == "-32.0 °C (-25.6 °F)"


class TestTemperatureSerializer:
    @pytest.fixture
    def serialize(self, temperature_sensor):
        return temperature_sensor.to_json_compatible

    @pytest.fixture
    def deserialize(self, temperature_sensor):
        return temperature_sensor.from_json_compatible

    @staticmethod
    def to_degc(magnitude):
        return ureg.Quantity(magnitude, "degree_Celsius")

    def test_serialize_21c(self, serialize):
        assert serialize(self.to_degc(21.0)) == {"magnitude": 21.0, "unit": "degree_Celsius"}

    def test_serialize_negative(self, serialize):
        assert serialize(self.to_degc(-32.3)) == {"magnitude": -32.3, "unit": "degree_Celsius"}

    def test_deserialize_21c(self, deserialize):
        assert deserialize({"magnitude": 21.0, "unit": "degree_Celsius"}) == self.to_degc(21.0)


class TestHumidityFormatter:
    @pytest.fixture
    def subject(self, humidity_sensor):
        return humidity_sensor.format

    def test_format_percentage(self, subject):
        assert subject(0.035) == "3.5%"
