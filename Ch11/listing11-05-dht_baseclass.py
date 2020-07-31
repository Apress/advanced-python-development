import os
import typing as t

from .exceptions import PersistentSensorFailureError


class DHTSensor:
    def __init__(self) -> None:
        self.board = os.environ.get("APD_SENSORS_TEMPERATURE_BOARD", "DHT22")
        self.pin = os.environ.get("APD_SENSORS_TEMPERATURE_PIN", "D20")

    @property
    def sensor(self) -> t.Any:
        try:
            import adafruit_dht
            import board
            sensor_type = getattr(adafruit_dht, self.board)
            pin = getattr(board, self.pin)
            return sensor_type(pin)
        except (ImportError, NotImplementedError, AttributeError) as err:
            # No DHT library results in an ImportError.
            # Running on an unknown platform results in a
            # NotImplementedError when getting the pin.
            # An unknown sensor type causes an AttributeError
            raise PersistentSensorFailureError("Unable to initialise sensor interface") from err

