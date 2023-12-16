import logging

from domain.settings import BASE_DIR

format = "%(asctime)s: %(message)s"

LOG_PATH = BASE_DIR / 'mailer.log'
LOG_PATH.touch(exist_ok=True)
file_handler = logging.FileHandler(LOG_PATH)
stream_handler = logging.StreamHandler()

logging.basicConfig(
    format=format, level=logging.DEBUG,
    datefmt="%H:%M:%S", handlers=[file_handler, stream_handler])
