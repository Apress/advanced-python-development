import socket
from unittest import mock

import pytest

from sensors import IPAddresses


@pytest.fixture
def sensor():
    return IPAddresses()


class TestIPAddressFormatter:
    @pytest.fixture
    def subject(self, sensor):
        return sensor.format

    def test_format_single_ipv4(self, subject):
        ips = [("AF_INET", "192.0.2.1")]
        assert subject(ips) == "192.0.2.1 (IPv4)"

    def test_format_single_ipv6(self, subject):
        ips = [("AF_INET6", "2001:DB8::1")]
        assert subject(ips) == "2001:DB8::1 (IPv6)"

    def test_format_mixed_list(self, subject):
        ips = [("AF_INET", "192.0.2.1"), ("AF_INET6", "2001:DB8::1")]
        assert subject(ips) == "192.0.2.1 (IPv4)\n2001:DB8::1 (IPv6)"

    def test_unusual_protocols_are_marked_as_unknown(self, subject):
        ips = [("AF_IRDA", "ffff")]
        assert subject(ips) == "ffff (Unknown)"


class TestIPAddressesValue:
    @pytest.fixture
    def subject(self, sensor):
        return sensor.value

    @pytest.fixture
    def gethostname(self):
        with mock.patch("socket.gethostname") as gethostname:
            gethostname.return_value = "localhost"
            yield gethostname

    @pytest.fixture
    def getaddrinfo(self, gethostname):
        with mock.patch("socket.getaddrinfo") as getaddrinfo:
            yield getaddrinfo

    def test_getaddrinfo_used_for_value_collection(self, getaddrinfo, subject):
        getaddrinfo.return_value = [(socket.AF_INET, 0, 0, "", ("192.0.2.1", 0))]
        assert subject() == [("AF_INET", "192.0.2.1")]
        assert getaddrinfo.call_count == 1

    def test_str_representation_is_formatted_value(self, getaddrinfo, sensor):
        getaddrinfo.return_value = [(socket.AF_INET6, 0, 0, "", ("2001:DB8::1", 0))]
        assert str(sensor) == "2001:DB8::1 (IPv6)"
