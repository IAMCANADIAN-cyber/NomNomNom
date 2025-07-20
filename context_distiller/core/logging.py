import logging
import sys

def setup_logging(level=logging.INFO):
    """
    Sets up logging for the application.
    """
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
