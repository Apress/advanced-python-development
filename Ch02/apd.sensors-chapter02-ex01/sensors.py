#!/usr/bin/env python
# coding: utf-8
import socket
import sys

import click
import psutil


def python_version():
    return sys.version_info


def ip_addresses():
    hostname = socket.gethostname()
    addresses = socket.getaddrinfo(socket.gethostname(), None)

    address_info = []
    for address in addresses:
        address_info.append((address[0].name, address[4][0]))
    return address_info


def cpu_load():
    return psutil.cpu_percent(interval=0.1) / 100.0


def ram_available():
    return psutil.virtual_memory().available


def ac_connected():
    return psutil.sensors_battery().power_plugged


def get_relative_humidity():
    try:
        from adafruit_dht import DHT11
        from board import D4
    except (ImportError, NotImplementedError):
        # No DHT library results in an ImportError.
        # Running on an unknown platform results in a NotImplementedError when getting the pin
        return None
    return DHT11(D4).humidity


@click.command()#help="Displays the values of the sensors")
def show_sensors():
    click.echo("Python version: {0.major}.{0.minor}".format(python_version()))
    for address in ip_addresses():
        click.echo("IP addresses: {0[1]} ({0[0]})".format(address))
    click.echo("CPU Load: {:.1%}".format(cpu_load()))
    click.echo("RAM Available: {:.0f} MiB".format(ram_available() / 1024**2))
    click.echo("AC Connected: {!r}".format(ac_connected()))
    click.echo("Humidity: {!r}".format(get_relative_humidity()))


if __name__ == '__main__':
    show_sensors()