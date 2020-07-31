import os
import subprocess
import typing as t

from pint import _DEFAULT_REGISTRY as ureg

from apd.sensors.base import Sensor


class SolarCumulativeOutput(Sensor[t.Optional[t.Any]]):
    name = "SolarCumulativeOutput"
    title = "Solar panel cumulative output"

    def __init__(
        self, path: t.Optional[str] = None, bt_addr: t.Optional[str] = None
    ) -> None:
        self.path = os.environ.get(
            "APD_SUNNYBOYSOLAR_PATH", "/home/pi/opensunny-master/opensunny"
        )
        self.bt_addr = os.environ.get("APD_SUNNYBOYSOLAR_BT_ADDRESS", None)

    def value(self) -> t.Optional[t.Any]:
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
        except (ValueError, IndexError, KeyError):
            return None
        return ureg.Quantity(yield_total, "watt")

    @classmethod
    def format(cls, value: t.Optional[t.Any]) -> str:
        if value is None:
            return "Unknown"
        return "{:~P}".format(value.to(ureg.kilowatt))

    @classmethod
    def to_json_compatible(
        cls, value: t.Optional[t.Any]
    ) -> t.Optional[t.Dict[str, t.Union[str, float]]]:
        if value is not None:
            return {"magnitude": value.magnitude, "unit": str(value.units)}
        else:
            return None

    @classmethod
    def from_json_compatible(cls, json_version: t.Any) -> t.Optional[t.Any]:
        if json_version:
            return ureg.Quantity(json_version["magnitude"], ureg[json_version["unit"]])
        else:
            return None
