import logging

class AddSensorNameDefault(logging.Filter):
    def filter(self, record):
        if not hasattr(record, "sensorname"):
            record.sensorname = "none"
        return True

def set_logger_format(logger, format_str, filters=None):
    """Set up a new stderr handler for the given logger
    and configure the formatter with the provided string
    """
    logger.propagate = False
    formatter = logging.Formatter(format_str, None, "{")

    std_err_handler = logging.StreamHandler(None)
    std_err_handler.setFormatter(formatter)

    logger.handlers.clear()
    logger.addHandler(std_err_handler)
    if filters is not None:
        for filter in filters:
            std_err_handler.addFilter(filter)
    return logger 

