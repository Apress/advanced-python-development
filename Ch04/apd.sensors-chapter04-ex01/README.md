# Advanced Python Development Sensors

This is the data collection package that forms part of the running example
for the book [Advanced Python Development](https://advancedpython.dev).

## Usage

This installs a console script called `sensors` that returns a report on
various aspects of the system. The available sensors are:

* Python version
* IP Addresses
* CPU Usage
* RAM Available
* Battery charging state
* Ambient Temperature
* Ambient Humidity

There are no command-line options, to view the report run `sensors` on the
command line.

## Caveats

The Ambient Temperature and Ambient Humidity sensors are only available on
RaspberryPi hosts and assume that a DHT22 sensor is connected to pin `D20`.

If there is an entry in `/etc/hosts` for the current machine's hostname that
value will be the only result from the IP Addresses sensor.

## Installation

Install with `pip3 install apd.sensors` under Python 3.7 or higher
