import pytest
from .temperature import celsius_to_fahrenheit


def test_celsius_to_fahrenheit():
    c = 21
    f = celsius_to_fahrenheit(c)
    assert f == 69.8

def test_celsius_to_fahrenheit_equivlance_point():
    c = -40
    f = celsius_to_fahrenheit(c)
    assert f == -40

def test_celsius_to_fahrenheit_float():
    c = 21.2
    f = celsius_to_fahrenheit(c)
    assert f == 70.16

def test_celsius_to_fahrenheit_string():
    c = "21"
    with pytest.raises(TypeError):
        f = celsius_to_fahrenheit(c)
