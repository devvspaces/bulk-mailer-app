import logging
import sys
from threading import Event, Thread
from domain.mail import send_email
from domain.settings import BASE_DIR
from domain.validators import validate_setting


def main():
    format = "%(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.DEBUG,
                        datefmt="%H:%M:%S")

    errors = validate_setting()
    if errors:
        for error in errors:
            print(error)
        sys.exit(1)

    event = Event()
    t = Thread(target=send_email, args=(event,), kwargs={
        'csv_file': BASE_DIR / 'test.csv',
        'subject': 'Hello {name}',
        'message': 'Hello {name}',
    })
    t.start()


if __name__ == "__main__":
    main()
