import logging

from pythonjsonlogger import jsonlogger


def get_logger(name=__name__):
    """
    Returns a logger configured with JSON formatting.
    This logger outputs to the console and can be extended
    to include additional handlers (like file handlers).
    """
    logger = logging.getLogger(name)
    if not logger.handlers:  # Prevent adding handlers multiple times
        # Console handler
        console_handler = logging.StreamHandler()
        formatter = jsonlogger.JsonFormatter(
            fmt="%(asctime)s %(name)s %(levelname)s %(message)s"
        )
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # Optionally, add more handlers here (for example, a file handler)
        # file_handler = logging.FileHandler('logs/combined.log')
        # file_handler.setFormatter(formatter)
        # logger.addHandler(file_handler)

        logger.setLevel(logging.INFO)
    return logger
