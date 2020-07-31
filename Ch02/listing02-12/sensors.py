#!/usr/bin/env python
# coding: utf-8
import math
import socket
import sys


import click
import psutil


class Sensor:
    def value(self):
        raise NotImplementedError

    @classmethod
    def format(cls, value):
        raise NotImplementedError

    def __str__(self):
        return self.format(self.value())


class PythonVersion(Sensor):
    title = "Python Version"

    def value(self):
        return sys.version_info

    @classmethod
    def format(cls, value):
        if value.micro == 0 and value.releaselevel == "alpha":
            return "{0.major}.{0.minor}.{0.micro}a{0.serial}".format(value)
        return "{0.major}.{0.minor}".format(value)


class IPAddresses(Sensor):
    title = "IP Addresses"
    FAMILIES = {"AF_INET": "IPv4", "AF_INET6": "IPv6"}

    def value(self):
        hostname = socket.gethostname()
        addresses = socket.getaddrinfo(hostname, None)

        address_info = []
        for address in addresses:
            family, ip = (address[0].name, address[4][0])
            if family not in self.FAMILIES:
                continue
            value = (family, ip)
            if value not in address_info:
                address_info.append(value)
        return address_info

    @classmethod
    def format(cls, value):
        return "\n".join(
            "{0} ({1})".format(address[1], cls.FAMILIES.get(address[0], "Unknown"))
            for address in value
        )


class CPULoad(Sensor):
    title = "CPU Usage"

    def value(self):
        return psutil.cpu_percent(interval=3) / 100.0

    @classmethod
    def format(cls, value):
        return "{:.1%}".format(value)


class RAMAvailable(Sensor):
    title = "RAM Available"
    UNITS = ("B", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB")
    UNIT_SIZE = 2 ** 10

    def value(self):
        return psutil.virtual_memory().available

    @classmethod
    def format(cls, value):
        magnitude = math.floor(math.log(value, cls.UNIT_SIZE))
        max_magnitude = len(cls.UNITS) - 1
        magnitude = min(magnitude, max_magnitude)
        scaled_value = value / (cls.UNIT_SIZE ** magnitude)
        return "{:.1f} {}".format(scaled_value, cls.UNITS[magnitude])


class ACStatus(Sensor):
    title = "AC Connected"

    def value(self):
        battery = psutil.sensors_battery()
        if battery is not None:
            return battery.power_plugged
        else:
            return None

    @classmethod
    def format(cls, value):
        if value is None:
            return "Unknown"
        elif value:
            return "Connected"
        else:
            return "Not connected"


class Temperature(Sensor):
    title = "Ambient Temperature"

    def value(self):
        try:
            # Connect to a DHT22 on pin 4
            from adafruit_dht import DHT22
            from board import D4
        except (ImportError, NotImplementedError):
            # No DHT library results in an ImportError.
            # Running on an unknown platform results in a
            # NotImplementedError when getting the pin
            return None
        try:
            return DHT22(D4).temperature
        except RuntimeError:
            return None

    @staticmethod
    def celsius_to_fahrenheit(value):
        return value * 9 / 5 + 32

    @classmethod
    def format(cls, value):
        if value is None:
            return "Unknown"
        else:
            return "{:.1f}C ({:.1f}F)".format(value, cls.celsius_to_fahrenheit(value))

    def __str__(self):
        return self.format(self.value())


class RelativeHumidity(Sensor):
    title = "Relative Humidity"

    def value(self):
        try:
            # Connect to a DHT22 on pin 4
            from adafruit_dht import DHT22
            from board import D4
        except (ImportError, NotImplementedError):
            # No DHT library results in an ImportError.
            # Running on an unknown platform results in a
            # NotImplementedError when getting the pin
            return None
        try:
            return DHT22(D4).humidity / 100
        except RuntimeError:
            return None

    @classmethod
    def format(cls, value):
        if value is None:
            return "Unknown"
        else:
            return "{:.1%}".format(value)


def get_sensors():
    return [
        PythonVersion(),
        IPAddresses(),
        CPULoad(),
        RAMAvailable(),
        ACStatus(),
        Temperature(),
        RelativeHumidity(),
    ]


@click.command(help="Displays the values of the sensors")
def show_sensors():
    sensors = get_sensors()
    for sensor in sensors:
        click.secho(sensor.title, bold=True)
        click.echo(str(sensor))
        click.echo("")


if __name__ == "__main__":
    show_sensors()
