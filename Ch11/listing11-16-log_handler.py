import logging

class AddSensorNameDefault(logging.Filter):
    def filter(self, record):
        if not hasattr(record, "sensorname"):
            record.sensorname = "none"
        return True

class SensorNameStreamHandler(logging.StreamHandler):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.addFilter(AddSensorNameDefault())

