from __future__ import annotations

import contextlib
import functools
import importlib
import io
import logging
import math
import os
import typing as t

from pint import _DEFAULT_REGISTRY as ureg


# Set up mercator transform from https://wiki.openstreetmap.org/wiki/Mercator#Python
# Thanks to Paulo Silva and the OSM contributors
def merc_x(lon: float) -> float:
    r_major = 6378137.000
    return r_major * math.radians(lon)


def merc_y(lat: float) -> float:
    if lat > 89.5:
        lat = 89.5
    if lat < -89.5:
        lat = -89.5
    r_major = 6378137.000
    r_minor = 6356752.3142
    temp = r_minor / r_major
    eccent = math.sqrt(1 - temp ** 2)
    phi = math.radians(lat)
    sinphi = math.sin(phi)
    con = eccent * sinphi
    com = eccent / 2
    con = ((1.0 - con) / (1.0 + con)) ** com
    ts = math.tan((math.pi / 2 - phi) / 2) / con
    y = 0 - r_major * math.log(ts)
    return y


@functools.lru_cache
def convert_temperature(magnitude: float, origin_unit: str, target_unit: str) -> float:
    # if origin_unit == "degC" and target_unit == "degF":
    #    return (magnitude * 1.8) + 32
    temp = ureg.Quantity(magnitude, origin_unit)
    return temp.to(target_unit).magnitude


@contextlib.contextmanager
def jupyter_page_file() -> t.Iterator[io.StringIO]:
    from IPython.core import page

    output = io.StringIO()
    yield output
    output.seek(0)
    page.page(output.read())


@contextlib.contextmanager
def profile_with_yappi() -> t.Iterator[None]:
    import yappi

    yappi.clear_stats()
    yappi.start()
    try:
        yield None
    finally:
        yappi.stop()


@functools.lru_cache
def get_package_prefix(package: str) -> str:
    mod = importlib.import_module(package)
    prefix = mod.__file__
    if prefix.endswith("__init__.py"):
        prefix = os.path.dirname(prefix)
    return prefix


def yappi_package_matches(stat, packages: t.List[str]):
    """ This object can be passed to yappi's filter_callback to limit
    by Python package."""
    for package in packages:
        prefix = get_package_prefix(package)
        if stat.full_name.startswith(prefix):
            return True
    return False


class AddSensorNameDefault(logging.Filter):
    def filter(self, record):
        if not hasattr(record, "sensorname"):
            record.sensorname = "none"
        return True


class SensorNameStreamHandler(logging.StreamHandler):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.addFilter(AddSensorNameDefault())
