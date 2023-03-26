import logging

logger = logging.getLogger("DMSQG")
logger.setLevel(logging.DEBUG)

def configure_logger():
    logging.basicConfig(level=logging.DEBUG)