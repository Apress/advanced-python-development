import copy
import logging

class ExtraDefaultAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        extra = copy.copy(self.extra)
        extra.update(kwargs.pop("extra", {}))
        kwargs["extra"] = extra
        return msg, kwargs

def set_logger_format(logger, format_str):
    """Set up a new stderr handler for the given logger
    and configure the formatter with the provided string
    """
    logger.propagate = False
    formatter = logging.Formatter(format_str, None, "{")

    std_err_handler = logging.StreamHandler(None)
    std_err_handler.setFormatter(formatter)

    logger.handlers.clear()
    logger.addHandler(std_err_handler)
    return logger

