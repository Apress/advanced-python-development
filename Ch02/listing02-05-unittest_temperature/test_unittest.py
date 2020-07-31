import unittest
from temperature import celsius_to_fahrenheit


class TestTemperatureConversion(unittest.TestCase):

    def test_celsius_to_fahrenheit(self):
        self.assertEqual(celsius_to_fahrenheit(21), 69.8)

    def test_celsius_to_fahrenheit_equivlance_point(self):
        self.assertEqual(celsius_to_fahrenheit(-40), -40)

    def test_celsius_to_fahrenheit_float(self):
        self.assertEqual(celsius_to_fahrenheit(21.2), 70.16)

    def test_celsius_to_fahrenheit_string(self):
        with self.assertRaises(TypeError):
            f = celsius_to_fahrenheit("21")


if __name__ == '__main__':
    unittest.main()
