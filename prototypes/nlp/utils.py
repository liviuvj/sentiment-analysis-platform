from sys import stdout
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
