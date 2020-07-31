from collections import namedtuple
from unittest import mock

import pytest

from sensors import PythonVersion


@pytest.fixture
def version():
    return namedtuple(
        "sys_versioninfo", ("major", "minor", "micro", "releaselevel", "serial")
    )


@pytest.fixture
def sensor():
    return PythonVersion()


class TestPythonVersionFormatter:
    @pytest.fixture
    def subject(self, sensor):
        return sensor.format

    def test_format_py38(self, subject, version):
        py38 = version(3, 8, 0, "final", 0)
        assert subject(py38) == "3.8"

    def test_format_large_version(self, subject, version):
        large = version(255, 128, 0, "final", 0)
        assert subject(large) == "255.128"

    def test_alpha_of_minor_is_marked(self, subject, version):
        py39 = version(3, 9, 0, "alpha", 1)
        assert subject(py39) == "3.9.0a1"

    def test_alpha_of_micro_is_unmarked(self, subject, version):
        py39 = version(3, 9, 1, "alpha", 1)
        assert subject(py39) == "3.9"


class TestPythonVersionValue:
    @pytest.fixture
    def subject(self, sensor):
        return sensor.value

    @pytest.fixture
    def python_version(self):
        import sys

        return sys.version_info

    def test_data_value_is_sys_versioninfo(self, python_version, subject):
        assert subject() == python_version


class TestPythonVersionSensor:
    def test_str_representation_is_formatted_value(self, sensor, version):
        with mock.patch("sys.version_info", new=version(3, 4, 1, "final", 1)):
            assert str(sensor) == "3.4"
