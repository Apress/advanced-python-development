import os
import subprocess
import typing as t

from apd.sensors.sensors import Sensor


class SolarCumulativeOutput(Sensor[t.Optional[float]]):
    title = "Solar panel cumulative output"

    def __init__(self, path=None, bt_addr=None):
        self.path = os.environ.get(
            "APD_SUNNYBOYSOLAR_PATH", "/home/pi/opensunny-master/opensunny"
        )
        self.bt_addr = os.environ.get("APD_SUNNYBOYSOLAR_BT_ADDRESS", None)

    def value(self) -> t.Optional[float]:
        if self.bt_addr is None:
            return None
        try:
            output: bytes = subprocess.check_output(
                [self.path, "-i", self.bt_addr], stderr=subprocess.STDOUT, timeout=15
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None

        lines = filter(None, output.split(b"\n"))
        found = {}
        for line in lines:
            start, value = line.rsplit(b"=", 1)
            start, key = start.rsplit(b" ", 1)
            found[key] = value

        try:
            yield_total = float(found[b"yield_total"][:-3].replace(b".", b""))
            power_dc_1 = int(found[b"power_dc_1"][:-1])
            power_dc_2 = int(found[b"power_dc_2"][:-1])
            if power_dc_1 > 1500 or power_dc_2 > 1500:
                return None
        except (ValueError, IndexError):
            return None
        return yield_total

    @classmethod
    def format(cls, value: t.Optional[float]) -> str:
        if value is None:
            return "Unknown"
        return "{} kW".format(value / 1000)
