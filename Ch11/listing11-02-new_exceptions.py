class APDSensorsError(Exception):
    """An exception base class for all exceptions raised by the
    sensor data collection system."""

class DataCollectionError(APDSensorsError, RuntimeError):
    """An error that represents the inability of a Sensor instance
    to retrieve a value"""

class IntermittentSensorFailureError(DataCollectionError):
    """A DataCollectionError that is expected to resolve itself
    in short order"""

class PersistentSensorFailureError(DataCollectionError):
    """A DataCollectionError that is unlikely to resolve itself
    if retried."""

