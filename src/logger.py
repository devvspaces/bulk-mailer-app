import logging

from domain.settings import BASE_DIR

format = "%(asctime)s: %(message)s"

file_handler = logging.FileHandler(BASE_DIR / 'mailer.log')
stream_handler = logging.StreamHandler()

logging.basicConfig(
    format=format, level=logging.DEBUG,
    datefmt="%H:%M:%S", handlers=[file_handler, stream_handler])
