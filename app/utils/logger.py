import logging
import os

from pythonjsonlogger import jsonlogger

from app.utils.s3_log_handler import S3LogHandler  # New import


def get_logger(name=__name__):
    """
    Returns a logger configured with JSON formatting.
    This logger outputs to the console and uploads logs to S3 using S3LogHandler
    only if the environment is not a test environment.
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

        # Only add S3LogHandler if not in test mode
        if os.environ.get("DJANGO_ENV", "").lower() != "test":
            s3_key = "logs/app.log"  # Customize as needed
            s3_handler = S3LogHandler(s3_key=s3_key, capacity=20)
            s3_handler.setFormatter(formatter)
            logger.addHandler(s3_handler)

        logger.setLevel(logging.INFO)
    return logger
