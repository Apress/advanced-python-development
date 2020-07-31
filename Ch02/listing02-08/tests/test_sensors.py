import sys

from click.testing import CliRunner
import pytest

import sensors


def test_sensors():
    assert hasattr(sensors, 'PythonVersion')

@pytest.mark.functional
def test_python_version_is_first_two_lines_of_cli_output():
    runner = CliRunner()
    result = runner.invoke(sensors.show_sensors)
    python_version = str(sensors.PythonVersion())
    assert ["Python Version", python_version] == result.stdout.split("\n")[:2]