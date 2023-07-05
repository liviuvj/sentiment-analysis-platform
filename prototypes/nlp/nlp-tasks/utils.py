from sys import stdout
from datetime import datetime

import logging

def get_logger(
    name: str = None,
    format: str = "[%(name)s] [%(asctime)s] [%(levelname)s] [%(filename)s: %(funcName)s] %(message)s",
) -> logging.Logger:
    """
    Method for generating a logger instance and redirecting it to standard output.

    Args:
        name (str): Name of the logger.
        format (str, optional): String format of the logger.
            Defaults to `"[%(name)s] [%(asctime)s] [%(levelname)s] [%(filename)s: %(funcName)s] %(message)s"`.

    Returns:
        logging.Logger: Generated logger with the specified parameters.
    """

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logFormatter = logging.Formatter(format)
    consoleHandler = logging.StreamHandler(stdout)
    consoleHandler.setFormatter(logFormatter)
    logger.addHandler(consoleHandler)

    return logger

def convert_date(data: list[dict], field: str) -> dict:
    """
    Method for converting a datetime string to a datetime object.

    Args:
        data (list[dict]): Data to convert from `str` to `datetime`.
        field (str): The name of the field that contains the date.

    Yields:
        dict: Data with the field converted to datetime object.
    """

    for obj in data:

        # Convert field to daterime
        try:
            dt = datetime.strptime(obj[field], "%Y-%m-%dT%H:%M:%S.%fZ")
        except Exception as e:
            dt = datetime.strptime(obj[field], "%Y-%m-%d %H:%M:%S")
        obj[field] = dt

        yield obj
