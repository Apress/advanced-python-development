from collections import namedtuple

from sensors import PythonVersion

import pytest


class TestPythonVersionFormatter:

    @pytest.fixture
    def subject(self):
        return PythonVersion().format

    @pytest.fixture
    def version(self):
        return namedtuple("sys_versioninfo", ("major", "minor", "micro", "releaselevel", "serial"))

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
