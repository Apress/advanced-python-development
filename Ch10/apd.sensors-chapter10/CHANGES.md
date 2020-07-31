## Changes

### 2.1.1 (2020-01-06)

* Cache DHT sensor connections (Matthew Wilkes)
* Force use of bitbang interface for DHT sensors, to improve reliability on Linux (Matthew Wilkes)

### 2.1.0 (2019-12-09)

* Add optional APD_SENSORS_DEPLOYMENT_ID parameter and v2.1 API which allows
  users to find a unique identifier for a webapp sensor deployment (Matthew Wilkes)

### 2.0.0 (2019-09-08)

* Add `to_json_compatible` and `from_json_compatible` methods to Sensor
  to facilitate better HTTP API (Matthew Wilkes)

* HTTP API is now versioned. The API from 1.3.0 is available at /v/1.0
  and an updated version is at /v/2.0 (Matthew Wilkes)

### 1.3.0 (2019-08-20)

* WSGI HTTP API support added (Matthew Wilkes)

### 1.2.0 (2019-08-05)

* Add external plugin support through `apd.sensors.sensors` entrypoint (Matthew Wilkes)

### 1.1.0 (2019-07-12)

* Add --develop argument (Matthew Wilkes)

### 1.0.1 (2019-06-20)

* Fix broken 1.0.0 release (Matthew Wilkes)

### 1.0.0 (2019-06-20)

* Added initial sensors (Matthew Wilkes)
