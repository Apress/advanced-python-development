import logging

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

logger = set_logger_format(
    logging.getLogger(__name__),
    format_str="{asctime}: {levelname} - {message}",
)

