#!/usr/bin/env python
# coding: utf-8

import click
import psutil

import sys


def python_version():
    return sys.version_info


def cpu_load():
    return psutil.cpu_percent(interval=0.1) / 100.0


def ram_available():
    return psutil.virtual_memory().available


def ac_connected():
    return psutil.sensors_battery().power_plugged


@click.command(help="Displays the values of the sensors")
def show_sensors():
    click.secho("Python version: ", bold=True, nl=False)
    click.echo("{!r}".format(python_version()))
    click.secho("CPU Load: ", bold=True, nl=False)
    click.echo("{:.1%}".format(cpu_load()))
    click.secho("RAM Available: ", bold=True, nl=False)
    click.echo("{:d}".format(ram_available()))
    click.secho("AC Connected: ", bold=True, nl=False)
    click.echo("{!r}".format(ac_connected()))


if __name__ == '__main__':
    show_sensors()